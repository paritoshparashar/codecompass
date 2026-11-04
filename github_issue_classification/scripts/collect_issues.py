import json
import os
import time
from pathlib import Path

import requests

REPOSITORIES: list[tuple[str, str]] = [
    ("encode", "httpx"),
    ("fastapi", "fastapi"),
    ("pallets", "flask"),
    ("psf", "requests"),
    ("scikit-learn", "scikit-learn")
]

MAX_PER_REPOSITORY = 150

OUTPUT_FILE = Path(__file__).parent.parent / "data/raw_issues.jsonl"

BASE_URL = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10"
}
token = os.getenv("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"Bearer {token}"

def collect_repository (owner, repo):
    print (f"Collecting issues for {owner}/{repo}...")
    collected_issues = []
    page = 1

    while len(collected_issues) < MAX_PER_REPOSITORY:
        url = f"{BASE_URL}/repos/{owner}/{repo}/issues"
        params = {
            "state": "closed",
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
            "page": page
        }
        response = requests.get(
            url, headers=HEADERS, params=params, timeout=30
        )
        response.raise_for_status()
        issues = response.json()
        if not issues:
            break
        for issue in issues:
            if "pull_request" in issue:
                continue
            title = (issue.get("title") or "").strip()
            body = (issue.get("body") or "").strip()
            if not title or len(title) < 5:
                continue
            if not body or len(body) < 20:
                continue

            # to store the issue data in a structured format, we can create a dictionary
            record = {
                "text": f"{title}\n\n{body}",
                "title": title,
                "body": body,
                "url": issue.get("html_url"),
                "repository": f"{owner}/{repo}",
                "issue_number": issue.get("number"),
                "github_labels": [label.get("name") for label in issue.get("labels", [])],
            }

            collected_issues.append(record)
            if len(collected_issues) >= MAX_PER_REPOSITORY:
                break
        print(f"Collected {len(collected_issues)} issues so far for {owner}/{repo}...")
        page += 1
        time.sleep(2)  # To avoid hitting the rate limit

    return collected_issues

def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_collected_issues = []
    for owner, repo in REPOSITORIES:
        try:    
            issues = collect_repository(owner, repo)
            all_collected_issues.extend(issues)
        except requests.exceptions.RequestException as e:
            print(f"Error collecting issues for {owner}/{repo}: {e}")
            continue

    # check if the output file does not exist or is empty, if so, create it
    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0:
        with open(OUTPUT_FILE, "w") as f:
            f.write("")  # Create an empty file
    # Write the collected issues to a JSONL file
    with open(OUTPUT_FILE, "w") as f:
        for issue in all_collected_issues:
            f.writelines(json.dumps(issue, ensure_ascii=False) + "\n")

    print(f"Collection Complete. Total issues collected: {len(all_collected_issues)}")
    print(f"Issues saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()