from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from code_compass.algorithms.classification.BM25_regression_classifier.training.bm25_vectorizer import (
    BM25Vectorizer,
)

INPUT_FILE = (
    Path(__file__).parent.parent.parent.parent.parent.parent.parent
    / "github_issue_classification/data/validated_labeled_issues.jsonl"
)
# read the jsonl file into a pandas dataframe
df = pd.read_json(INPUT_FILE, lines=True)

# get the text and label columns
X = df["text"]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ==================================
# CREATE CLASSIFICATION PIPELINE
# ==================================

model = Pipeline([
    (
        "bm25",
        BM25Vectorizer(
            k1=1.5,
            b=0.75,
            max_features=10000,
            min_df=2
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42
        )
    )
])


# ==================================
# 4. TRAIN MODEL
# ==================================

model.fit(X_train, y_train)


# ==================================
# 5. EVALUATE MODEL
# ==================================

predictions = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, predictions))

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# ==================================
# 6. SAVE TRAINED MODEL
# ==================================

# Create directory if it doesn't exist
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "github_issue_classifier_BM25LogRes.pkl"
joblib.dump(
    model,
    MODEL_FILE
)

print("Model successfully saved!")