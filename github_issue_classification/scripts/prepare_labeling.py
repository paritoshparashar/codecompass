import json
from pathlib import Path

import pandas as pd

# Define the path to the input file relative to the current script
INPUT_FILE = Path(__file__).parent.parent / "data/labeled_issues.jsonl"
OUTPUT_FILE = INPUT_FILE.parent / "labeled_issues.csv"


def main():

    records: list[dict] = []

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            issue = json.loads(line)
            records.append(
                {
                    "repository": issue.get("repository"),
                    "issue_number": issue.get("issue_number"),
                    "groq1_label": issue.get("groq1_label"),
                    "groq1_label_confidence": issue.get("groq1_label_confidence"),
                    "groq2_label": issue.get("groq2_label"),
                    "groq2_label_confidence": issue.get("groq2_label_confidence"),
                    "my_label": issue.get("my_label"),
                    "llm_confidence": issue.get("llm_confidence"),
                    "llm_reason": issue.get("llm_reason"),
                    "label_source": issue.get("label_source"),
                    "needs_review": issue.get("needs_review"),
                    "label_status": issue.get("label_status"),
                    "label_error": issue.get("label_error"),
                    "text": issue.get("text"),
                }
            )

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["text"])
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("Total issues:", len(df))
    print("File:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
