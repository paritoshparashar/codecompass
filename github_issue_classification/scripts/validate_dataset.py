import json
from collections import Counter
from pathlib import Path

import pandas as pd

INPUT_FILE = Path(__file__).parent.parent / "data/labeled_issues.csv"
OUTPUT_FILE = INPUT_FILE.parent / "validated_labeled_issues.jsonl"
ALLOWED_LABELS = {
    "BUG",
    "FEATURE",
    "PERFORMANCE",
    "DOCUMENTATION",
    "TEST_GAP",
    "UNKNOWN",
}

TARGET_PER_CATEGORY = 120


def main():
    df = pd.read_csv(INPUT_FILE).fillna("")
    errors = []

    missing = df["my_label"].str.strip() == ""

    if missing.any():
        errors.append(f"{missing.sum()} records have missing labels.")

    # Check for invalid labels
    invalid_labels = set(df["my_label"]) - ALLOWED_LABELS
    if invalid_labels:
        errors.append(f"Invalid labels found: {invalid_labels}")
        print(f"Invalid labels found: {invalid_labels}")

    valid_df = df[df["my_label"].isin(ALLOWED_LABELS)].copy()

    counts = Counter(valid_df["my_label"])

    print("\nDATASET VALIDATION")
    print("------------------")

    print("Total labeled examples:", len(valid_df))

    for label in sorted(ALLOWED_LABELS):
        count = counts[label]
        status = "OK" if count >= TARGET_PER_CATEGORY else "LOW"

        print(f"{label}: {count} [{status}]")

    # Report errors and warnings
    if errors:
        print("\nWarnings:")
        for error in errors:
            print("-", error)

    # Export only text and label
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        for _, row in valid_df.iterrows():
            record = {
                "label": row["my_label"],
                "text": row["text"],
            }
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("\nExport completed!")
    print("Saved to:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
