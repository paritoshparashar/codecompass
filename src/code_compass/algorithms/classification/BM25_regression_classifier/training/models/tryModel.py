from pathlib import Path

import joblib

MODEL_PATH = Path(__file__).parent / "github_issue_classifier_BM25LogRes.pkl"
# load the model from the pickle file

model = joblib.load(MODEL_PATH)
# Read the issue text from the issue file
issue_file = Path(__file__).parent / "issue.txt"
with open(issue_file, "r") as f:
    issue_text = f.read()

prediction = model.predict([issue_text])
print(prediction)
