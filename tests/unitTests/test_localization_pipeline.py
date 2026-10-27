__all__ = [
    "TestTokenizer",
    "TestBM25Scorer",
    "TestBM25LocalizationStrategy",
    "TestLocalizationService",
    "TestPipelineLocalizationEndToEnd",
]

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_compass.algorithms.localization.BM25.bm25_localization_strategy import (
    BM25LocalizationStrategy,
)
from code_compass.algorithms.localization.BM25.bm25_scorer import BM25Scorer
from code_compass.application.initialization_package.repostiory_initialization_service import (
    RepositoryInitializationService,
)
from code_compass.application.localization_package.localization_config import (
    LocalizationLevel,
)
from code_compass.application.localization_package.localization_service import (
    LocalizationService,
)
from code_compass.application.localization_package.tokenizer import Tokenizer
from code_compass.domain.candidate_package.candidate_interface import Candidate
from code_compass.domain.candidate_package.file_candidate import FileCandidate
from code_compass.domain.candidate_package.function_candidate import FunctionCandidate
from code_compass.domain.issue import Issue
from code_compass.domain.repository_package.document import Document
from code_compass.domain.repository_package.repository import Repository
from code_compass.domain.token_package.token import Token
from code_compass.pipeline.io_module import (
    InitializeRepositoryRequest,
    IssueLocalizationRequest,
    ResponseStatus,
)
from code_compass.pipeline.orchestrator import CodeCompassPipeline


class TestTokenizer(unittest.TestCase):
    """Unit tests for code-aware tokenization."""

    def setUp(self):
        self.tokenizer = Tokenizer()

    def test_snake_case_tokenization(self):
        tokens = self.tokenizer.tokenize("calculate_export_total")
        normalized = [t.normalized for t in tokens]
        self.assertIn("calculate", normalized)
        self.assertIn("export", normalized)
        self.assertIn("total", normalized)
        self.assertIn("calculate_export_total", normalized)

    def test_camel_case_tokenization(self):
        tokens = self.tokenizer.tokenize("getUserAccount")
        normalized = [t.normalized for t in tokens]
        self.assertIn("get", normalized)
        self.assertIn("user", normalized)
        self.assertIn("account", normalized)
        self.assertIn("getuseraccount", normalized)

    def test_preserves_token_frequency(self):
        # Frequency must be preserved (not set-deduplicated) for BM25 TF calculation
        tokens = self.tokenizer.tokenize("error error error warning")
        normalized = [t.normalized for t in tokens]
        self.assertEqual(normalized.count("error"), 3)
        self.assertEqual(normalized.count("warning"), 1)

    def test_strips_syntax_punctuation(self):
        code = "def process(item: str) -> None:\n    return item.strip()"
        tokens = self.tokenizer.tokenize(code)
        normalized = [t.normalized for t in tokens]
        # Punctuation/syntax characters must not stick to tokens
        self.assertIn("process", normalized)
        self.assertIn("item", normalized)
        self.assertIn("strip", normalized)
        for token in tokens:
            self.assertNotIn("(", token.text)
            self.assertNotIn(")", token.text)
            self.assertNotIn(":", token.text)


class TestBM25Scorer(unittest.TestCase):
    """Unit tests for Robertson-Spärck Jones Okapi BM25 scoring."""

    def setUp(self):
        self.scorer = BM25Scorer(k1=1.5, b=0.75)
        self.tokenizer = Tokenizer()

    def _make_candidate(self, cid: int, text: str) -> Candidate:
        tokens = self.tokenizer.tokenize(text)
        return FileCandidate(candidate_id=cid, filePath=Path(f"/f{cid}.py"), tokens=tokens)

    def _make_issue(self, text: str) -> Issue:
        issue = Issue(issue_id=1, description=text)
        issue.set_tokens(self.tokenizer.tokenize(text))
        return issue

    def test_empty_candidates_returns_empty(self):
        issue = self._make_issue("export bug")
        scores = self.scorer.score([], issue)
        self.assertEqual(scores, [])

    def test_no_matching_tokens_scores_zero(self):
        doc1 = self._make_candidate(1, "def user_authentication(): pass")
        issue = self._make_issue("export report payment")
        scores = self.scorer.score([doc1], issue)
        self.assertEqual(scores, [0.0])

    def test_relevant_document_scores_higher(self):
        doc_relevant = self._make_candidate(1, "def export_batch(): export_data()")
        doc_irrelevant = self._make_candidate(2, "def login(): authenticate()")

        issue = self._make_issue("export batch failure")
        scores = self.scorer.score([doc_relevant, doc_irrelevant], issue)

        self.assertGreater(scores[0], scores[1])
        self.assertGreater(scores[0], 0.0)
        self.assertEqual(scores[1], 0.0)

    def test_case_insensitive_matching(self):
        # Query has uppercase, document has lowercase
        doc = self._make_candidate(1, "def parse_receipt(): pass")
        issue = self._make_issue("Receipt Parser")
        scores = self.scorer.score([doc], issue)
        self.assertGreater(scores[0], 0.0)

    def test_term_frequency_saturation(self):
        # Repeated terms increase score, but with saturation
        doc_single = self._make_candidate(1, "error")
        doc_multiple = self._make_candidate(2, "error error error error")
        issue = self._make_issue("error")

        scores = self.scorer.score([doc_single, doc_multiple], issue)
        self.assertGreater(scores[1], scores[0])


class TestBM25LocalizationStrategy(unittest.TestCase):
    """Unit tests for BM25 ranking strategy."""

    def setUp(self):
        self.strategy = BM25LocalizationStrategy(BM25Scorer())
        self.tokenizer = Tokenizer()

    def _make_candidate(self, cid: int, text: str) -> Candidate:
        tokens = self.tokenizer.tokenize(text)
        return FileCandidate(candidate_id=cid, filePath=Path(f"/f{cid}.py"), tokens=tokens)

    def test_ranking_and_metadata_assignment(self):
        c1 = self._make_candidate(1, "export export export")
        c2 = self._make_candidate(2, "export")
        c3 = self._make_candidate(3, "completely unrelated")

        issue = Issue(issue_id=1, description="export")
        issue.set_tokens(self.tokenizer.tokenize("export"))

        ranked = self.strategy.localize([c1, c2, c3], issue, top_k=3)

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0].candidate_id, 1)
        self.assertEqual(ranked[0].rank, 1)
        self.assertGreater(ranked[0].score, ranked[1].score)
        self.assertEqual(ranked[1].rank, 2)
        self.assertEqual(ranked[2].rank, 3)

    def test_top_k_limits_results(self):
        c1 = self._make_candidate(1, "export")
        c2 = self._make_candidate(2, "export")
        c3 = self._make_candidate(3, "export")

        issue = Issue(issue_id=1, description="export")
        issue.set_tokens(self.tokenizer.tokenize("export"))

        ranked = self.strategy.localize([c1, c2, c3], issue, top_k=2)
        self.assertEqual(len(ranked), 2)

    def test_top_k_zero_or_negative(self):
        c = self._make_candidate(1, "export")
        issue = Issue(issue_id=1, description="export")
        issue.set_tokens(self.tokenizer.tokenize("export"))

        self.assertEqual(self.strategy.localize([c], issue, top_k=0), [])
        with self.assertRaises(ValueError):
            self.strategy.localize([c], issue, top_k=-1)


class TestLocalizationService(unittest.TestCase):
    """Unit tests for candidate generation and service orchestration."""

    def test_file_level_localization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            p1 = Path(tmp_dir) / "export_service.py"
            p1.write_text("def run_export(): pass", encoding="utf-8")
            p2 = Path(tmp_dir) / "auth_service.py"
            p2.write_text("def authenticate(): pass", encoding="utf-8")

            repo = Repository(id=1, name="test_repo", url="http://test", path=Path(tmp_dir))
            repo.add_document(Document(doc_id=10, name="export_service.py", path=p1, repository_id=1))
            repo.add_document(Document(doc_id=20, name="auth_service.py", path=p2, repository_id=1))

            strategy = BM25LocalizationStrategy(BM25Scorer())
            service = LocalizationService(strategy=strategy, loc_level=LocalizationLevel.FILE, top_k=2)

            issue = Issue(issue_id=1, description="export service error")
            candidates = service.localize_issue(issue, repo)

            self.assertEqual(len(candidates), 2)
            self.assertIsInstance(candidates[0], FileCandidate)
            self.assertEqual(candidates[0].filePath.name, "export_service.py")
            self.assertEqual(candidates[0].rank, 1)

    def test_function_level_candidate_extraction(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "billing.py"
            file_path.write_text(
                "def generate_invoice():\n    return 42\n\ndef process_refund():\n    return 0\n",
                encoding="utf-8",
            )

            repo = Repository(id=1, name="test_repo", url="http://test", path=Path(tmp_dir))
            repo.add_document(Document(doc_id=1, name="billing.py", path=file_path, repository_id=1))

            strategy = BM25LocalizationStrategy(BM25Scorer())
            service = LocalizationService(strategy=strategy, loc_level=LocalizationLevel.FUNCTION, top_k=5)

            issue = Issue(issue_id=1, description="generate invoice calculation")
            candidates = service.localize_issue(issue, repo)

            self.assertEqual(len(candidates), 2)
            self.assertIsInstance(candidates[0], FunctionCandidate)
            self.assertEqual(candidates[0].function_name, "generate_invoice")
            self.assertEqual(candidates[0].start_line, 1)
            self.assertEqual(candidates[0].end_line, 2)
            self.assertEqual(candidates[0].rank, 1)

    def test_handles_syntax_error_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_file = Path(tmp_dir) / "corrupt.py"
            bad_file.write_text("def broken_syntax(:\n", encoding="utf-8")

            repo = Repository(id=1, name="test_repo", url="http://test", path=Path(tmp_dir))
            repo.add_document(Document(doc_id=1, name="corrupt.py", path=bad_file, repository_id=1))

            strategy = BM25LocalizationStrategy(BM25Scorer())
            service = LocalizationService(strategy=strategy, loc_level=LocalizationLevel.FUNCTION, top_k=5)

            issue = Issue(issue_id=1, description="broken syntax")
            # Should not crash on invalid Python syntax
            candidates = service.localize_issue(issue, repo)
            self.assertEqual(len(candidates), 0)


class TestPipelineLocalizationEndToEnd(unittest.TestCase):
    """End-to-end integration tests using CodeCompassPipeline."""

    @patch.object(RepositoryInitializationService, "_clone_repository")
    def test_pipeline_localizes_issue_successfully(self, mock_clone):
        def fake_clone(git_url, branch, destination):
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "billing.py").write_text(
                "def generate_invoice():\n    return 100\n", encoding="utf-8"
            )
            (destination / "auth.py").write_text(
                "def login():\n    return True\n", encoding="utf-8"
            )
            return True

        mock_clone.side_effect = fake_clone

        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = CodeCompassPipeline()
            # Point initialization root to isolated temporary directory
            pipeline.initialization_service = RepositoryInitializationService(Path(tmp_dir))

            # Step 1: Initialize Repository
            init_req = InitializeRepositoryRequest(git_url="https://github.com/org/payments", branch="main")
            init_resp = pipeline.create_and_initialize_repository(init_req)

            self.assertEqual(init_resp.status, ResponseStatus.SUCCESS)
            self.assertIsNotNone(init_resp.repository_id)

            # Step 2: Localize Issue
            loc_req = IssueLocalizationRequest(
                repository_id=int(init_resp.repository_id),
                issue="error in generate invoice",
            )
            loc_resp = pipeline.localize_issue(loc_req)

            self.assertEqual(loc_resp.status, ResponseStatus.SUCCESS)
            self.assertIsNotNone(loc_resp.localized_candidates)
            self.assertGreater(len(loc_resp.localized_candidates), 0)

            # Top candidate should be the generate_invoice function
            top_candidate = loc_resp.localized_candidates[0]
            self.assertEqual(top_candidate.rank, 1)
            self.assertEqual(top_candidate.function_name, "generate_invoice")


if __name__ == "__main__":
    unittest.main()

