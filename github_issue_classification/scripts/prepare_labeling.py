import json
from pathlib import Path

import pandas as pd

# Define the path to the input file relative to the current script
INPUT_FILE = Path(__file__).parent.parent / "data/raw_issues.jsonl"
OUTPUT_FILE = INPUT_FILE.parent / "labeling.csv"


def main():

    records: list[dict] = []

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            issue = json.loads(line)

            records.append(
                {
                    "repository": issue["repository"],
                    "issue_number": issue["issue_number"],
                    "my_label": "",  # Placeholder for the label to be filled in later
                    "github_labels": ", ".join(issue.get("github_labels", [])),
                    "url": issue["url"],
                    "text": issue["text"],
                }
            )

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["text"])
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print("Total issues:", len(df))
    print("File:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
