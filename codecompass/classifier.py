import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class IssueClassifier:
    """
    Classifies GitHub issues into categories to route them 
    to specialized analysis strategies.
    """

    CATEGORIES = ["bug", "feature", "documentation", "performance", "testing", "other"]

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq API initialized for issue classification.")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}. Falling back to keyword classification.")
        else:
            logger.warning("No GROQ_API_KEY found. Using keyword-based classification.")

    def classify(self, issue_text: str) -> str:
        """
        Classifies the issue text into one of the predefined categories.
        Uses LLM if available, falls back to keyword matching.
        """
        if self.client:
            return self._classify_with_llm(issue_text)
        return self._classify_with_keywords(issue_text)

    def _classify_with_llm(self, issue_text: str) -> str:
        prompt = (
            "You are a GitHub issue classifier. Classify the issue into exactly one category.\n\n"
            "CATEGORIES AND DEFINITIONS:\n"
            "- bug: Something that SHOULD work is broken, crashing, or producing wrong results.\n"
            "- feature: Requesting NEW functionality that does not exist yet. Often phrased as 'add support for', 'allow', 'enable', or 'why not support X'.\n"
            "- documentation: Issues about README, docs, tutorials, examples, or explanations.\n"
            "- performance: Issues about speed, latency, memory usage, timeouts, or optimization.\n"
            "- testing: Issues about test coverage, unit tests, mocks, or test infrastructure.\n"
            "- other: Anything that doesn't fit the above categories.\n\n"
            "IMPORTANT DISTINCTIONS:\n"
            "- 'Cannot do X' where X was NEVER supported = feature (not bug)\n"
            "- 'Cannot do X' where X USED TO WORK or SHOULD WORK = bug\n"
            "- 'Add support for X' = feature\n"
            "- 'Why not allow X' = feature\n\n"
            "EXAMPLES:\n"
            "Issue: 'OAuth login crashes with timeout error' -> bug\n"
            "Issue: 'Cannot create defaultdict field with dict value type. Why not add support?' -> feature\n"
            "Issue: 'README missing installation instructions' -> documentation\n"
            "Issue: 'API takes 10 seconds, need optimization' -> performance\n"
            "Issue: 'No test coverage for auth module' -> testing\n\n"
            f"Issue to classify:\n\"{issue_text[:2000]}\"\n\n"
            "Respond with ONLY the category name. No explanation."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10
            )
            result = response.choices[0].message.content.strip().lower()
            
            if result in self.CATEGORIES:
                return result
            return "other"
        except Exception as e:
            logger.warning(f"Groq API failed: {e}. Falling back to keywords.")
            return self._classify_with_keywords(issue_text)

    def _classify_with_keywords(self, issue_text: str) -> str:
        text = issue_text.lower()
        
        bug_keywords = ["bug", "error", "crash", "fail", "broken", "fix", "exception", 
                        "traceback", "doesn't work", "not working", "regression", 
                        "used to work", "stopped working"]
        feature_keywords = ["feature", "add", "support", "implement", "new", "enhancement", 
                            "request", "allow", "enable", "why not", "would be nice", 
                            "please add", "can we have", "missing support", "impossible to create"]
        doc_keywords = ["documentation", "docs", "readme", "tutorial", "guide", "example", 
                        "explain", "how to", "clarify"]
        perf_keywords = ["slow", "performance", "latency", "timeout", "optimize", 
                        "bottleneck", "seconds", "respond", "memory", "cpu", "speed"]
        test_keywords = ["test", "coverage", "unit test", "mock", "assert", "pytest", "test case"]
        
        scores = {
            "bug": sum(1 for k in bug_keywords if k in text),
            "feature": sum(1 for k in feature_keywords if k in text),
            "documentation": sum(1 for k in doc_keywords if k in text),
            "performance": sum(1 for k in perf_keywords if k in text),
            "testing": sum(1 for k in test_keywords if k in text),
        }
        
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "other"
        return best