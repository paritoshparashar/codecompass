"""Label raw issue records in JSONL with independent Gemini and Groq predictions."""

from __future__ import annotations

import json
import os
import random
import re
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LABELS = ("BUG", "FEATURE", "DOCUMENTATION", "PERFORMANCE", "TEST_GAP", "UNKNOWN")
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
LABELLED_ISSUES_FILE = Path(__file__).parent.parent / "data/labeled_issues.jsonl"
# if the labelled issues file does not exist or is empty, use the raw issues file as input else use the labelled issues file as input
RAW_ISSUES_FILE = Path(__file__).parent.parent / "data/raw_issues.jsonl"
if LABELLED_ISSUES_FILE.exists() and LABELLED_ISSUES_FILE.stat().st_size > 0:
    RAW_ISSUES_FILE = LABELLED_ISSUES_FILE
MAX_TEXT_CHARS = 8_000
CONFIDENCE_THRESHOLD = 0.75
MAX_RETRIES = 3
MAX_ISSUES = 400  # limit for testing; set to None for no limit
API_CALL_DELAY_SECONDS = 2
GEMINI = {
    "model": os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
    "api_key": os.getenv("GEMINI_API_KEY"),
}
GROQ = {
    "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
    "api_key": os.getenv("GROQ_API_KEY"),
}
GROQ2 = {
    "model": os.getenv("GROQ2_MODEL", DEFAULT_GROQ_MODEL),
    "api_key": os.getenv("GROQ_API_KEY"),
}


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    reason: str


class APIRequestError(RuntimeError):
    """Raised when an LLM request cannot be completed."""


def prompt_for(issue_text: str) -> str:
    return f"""Classify this software issue into exactly one label:
BUG, FEATURE, DOCUMENTATION, PERFORMANCE, TEST_GAP, or UNKNOWN.

Definitions:
- BUG: existing behavior is incorrect, crashes, or fails.
- FEATURE: requests new functionality or support.
- DOCUMENTATION: concerns documentation, examples, README, or incorrect instructions.
- PERFORMANCE: concerns speed, latency, memory, or resource usage.
- TEST_GAP: explicitly concerns missing or inadequate tests.
- UNKNOWN: ambiguous, insufficient, spam, a question, or equally plausible categories.

Return JSON only:
{{"label":"BUG","confidence":0.0,"reason":"one or two concise sentence"}}
Confidence must be a number from 0 to 1. Use only the issue text.

Issue:
{issue_text}"""


def request_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    max_retries: int,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(max_retries + 1):
        request = Request(
            url,
            data=body,
            headers={
                **headers,
                "Content-Type": "application/json",
                "User-Agent": "CodeCompass/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            if error.code != 429 or attempt == max_retries:
                raise APIRequestError(
                    f"HTTP {error.code}: {response_body[:500]}"
                ) from error
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
        except (URLError, TimeoutError) as error:
            if attempt == max_retries:
                raise APIRequestError(f"Network request failed: {error}") from error
            delay = 2**attempt
        time.sleep(delay * 10 + random.uniform(0, 0.5))
    raise APIRequestError("Request failed without a response.")


def parse_prediction(text: str) -> Prediction:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text.strip(), re.DOTALL)
    content = match.group(1) if match else text.strip()
    try:
        data = json.loads(content)
        label = str(data["label"]).upper().strip()
        confidence = float(data["confidence"])
        reason = str(data.get("reason", "")).strip()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise APIRequestError(f"Invalid model JSON: {content[:300]}") from error
    if label not in LABELS or not 0 <= confidence <= 1:
        raise APIRequestError(f"Invalid model prediction: {data}")
    return Prediction(label, confidence, reason)


# def gemini(text: str, api_key: str, model: str, max_retries: int) -> Prediction:
#     response = request_json(
#         f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
#         {},
#         {
#             "contents": [{"parts": [{"text": prompt_for(text)}]}],
#             "generationConfig": {"responseMimeType": "application/json"},
#         },
#         max_retries,
#     )
#     try:
#         content = response["candidates"][0]["content"]["parts"][0]["text"]
#     except (KeyError, IndexError, TypeError) as error:
#         raise APIRequestError("Gemini returned no text.") from error
#     return parse_prediction(content)


def groq(text: str, api_key: str, model: str, max_retries: int) -> Prediction:
    response = request_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}"},
        {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": prompt_for(text)},
            ],
        },
        max_retries,
    )
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise APIRequestError("Groq returned no text.") from error
    return parse_prediction(content)


def judge_with_groq(
    text: str,
    first: Prediction,
    second: Prediction,
    api_key: str,
    model: str,
    max_retries: int,
) -> Prediction:
    judge_prompt = f"""Choose the correct label for this issue:
BUG, FEATURE, DOCUMENTATION, PERFORMANCE, TEST_GAP, or UNKNOWN.
Use UNKNOWN if the evidence is insufficient. Return JSON only with label,
confidence, and one-sentence reason.

Issue:
{text}

Groq model 1 prediction:
{json.dumps(asdict(first))}

Groq model 2 prediction:
{json.dumps(asdict(second))}
"""
    response = request_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {api_key}"},
        {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": judge_prompt},
            ],
        },
        max_retries,
    )
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise APIRequestError("Groq judge returned no text.") from error
    return parse_prediction(content)


def read_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    """Rewrite the JSONL atomically so a stopped run keeps valid JSON."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()
            os.fsync(file.fileno())
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def process_row(
    row: dict[str, Any],
    groq_key: str,
) -> None:
    print(f"Waiting {API_CALL_DELAY_SECONDS} seconds before the next API call...")
    time.sleep(API_CALL_DELAY_SECONDS)
    text = str(row.get("text", ""))[:MAX_TEXT_CHARS]
    print(f"Calling Groq model 1: {GROQ['model']}")
    first = groq(text, groq_key, GROQ["model"], MAX_RETRIES)
    print(f"Groq model 1: {first.label} ({first.confidence:.4f})")
    print(f"Calling Groq model 2: {GROQ2['model']}")
    second = groq(text, groq_key, GROQ2["model"], MAX_RETRIES)
    print(f"Groq model 2: {second.label} ({second.confidence:.4f})")

    row.update(
        {
            "groq1_label": first.label,
            "groq1_label_confidence": f"{first.confidence:.4f}",
            "groq2_label": second.label,
            "groq2_label_confidence": f"{second.confidence:.4f}",
        }
    )
    if (
        first.label == second.label
        and first.confidence >= CONFIDENCE_THRESHOLD
        and second.confidence >= CONFIDENCE_THRESHOLD
    ):
        final = Prediction(
            first.label,
            min(first.confidence, second.confidence),
            f"Both Groq models agreed with high confidence. "
            f"Model 1: {first.reason} Model 2: {second.reason}",
        )
        source = "groq1+groq2"
    else:
        print(
            "Groq models disagreed or were below the confidence threshold; calling judge."
        )
        print(f"Waiting {API_CALL_DELAY_SECONDS} seconds before the next API call...")
        time.sleep(API_CALL_DELAY_SECONDS)
        final = judge_with_groq(
            text,
            first,
            second,
            groq_key,
            GROQ2["model"],
            MAX_RETRIES,
        )
        print(f"Judge: {final.label} ({final.confidence:.4f})")
        source = "groq_judge"

    row.update(
        {
            "my_label": final.label,
            "llm_confidence": f"{final.confidence:.4f}",
            "llm_reason": final.reason,
            "label_source": source,
            "needs_review": str(
                final.label == "UNKNOWN" or final.confidence < CONFIDENCE_THRESHOLD
            ).lower(),
            "label_status": "complete",
            "label_error": "",
        }
    )


def main() -> None:
    groq_key = GROQ["api_key"]
    if not groq_key:
        raise SystemExit("Set GROQ_API_KEY first.")
    records = read_records(RAW_ISSUES_FILE)
    if not records:
        raise SystemExit(f"No issue records found in {RAW_ISSUES_FILE}.")

    generated_fields = (
        "groq1_label",
        "groq1_label_confidence",
        "groq2_label",
        "groq2_label_confidence",
        "my_label",
        "llm_confidence",
        "llm_reason",
        "label_source",
        "needs_review",
        "label_status",
        "label_error",
    )
    for record in records:
        for field in generated_fields:
            record.setdefault(field, "")
    write_records(LABELLED_ISSUES_FILE, records)

    processed = 0
    i = 0
    for record in records:
        i += 1
        print(
            f"\nProcessing issue {i}: {record.get('repository')}#{record.get('issue_number')}"
        )
        if MAX_ISSUES is not None and processed >= MAX_ISSUES:
            print(f"Reached MAX_ISSUES limit of {MAX_ISSUES}. Stopping.")
            break
        if record.get("label_status") == "complete":
            print(
                f"Issue {record.get('repository')}#{record.get('issue_number')} already labeled:\nLabel: {record.get('my_label')}, Confidence: {record.get('llm_confidence')}, Source: {record.get('label_source')}"
            )
            continue
        try:
            process_row(record, groq_key)
        except APIRequestError as error:
            record.update(
                {
                    "label_status": "error",
                    "label_error": str(error),
                    "needs_review": "true",
                }
            )
            write_records(LABELLED_ISSUES_FILE, records)
            print(f"Error: {error}")
            print(
                f"Saved {LABELLED_ISSUES_FILE};\nProcessed {processed} issues in the current run\nTotal labeled issues: {i}"
            )
            return
        write_records(LABELLED_ISSUES_FILE, records)
        processed += 1
        print(
            f"Wrote labeled issue {record.get('repository')}#{record.get('issue_number')} to file\nLabel: {record.get('my_label')}, Confidence: {record.get('llm_confidence')}, Source: {record.get('label_source')}."
        )
    write_records(LABELLED_ISSUES_FILE, records)

    print(
        f"Saved {LABELLED_ISSUES_FILE};\nProcessed {processed} issues in the current run\nTotal labeled issues: {i}"
    )


if __name__ == "__main__":
    main()
