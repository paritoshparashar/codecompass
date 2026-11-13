from pathlib import Path

import joblib
import pandas as pd

from ....application.classification_package.classification_strategy import (
    ClassificationStrategy,
)
from ....domain.issue import Issue, IssueType


# Assumes we have trained a BM25 regression model (Vocabulary and weights)
class BM25RegStrategy(ClassificationStrategy):
    def __init__(self, model_path: Path | None = None):
        # Load the trained model
        if model_path is None:
            model_path = (
                Path(__file__).parent
                / "training"
                / "models"
                / "github_issue_classifier_BM25LogRes.pkl"
            )
        model = joblib.load(model_path)
        self.model = model

    def classify(self, issue: Issue) -> IssueType:
        # Implement the BM25 regression classification logic here
        # For now, we can just return a placeholder value
        """
        1 - IssueText -> Tokenization (Chose a tokenization strategy words vs chars vs subwords)
        2 - Create Vectors(dim = len(vocabulary)) of Tokens using this strategy scores
        3 -
        """
        issueText = issue.description + issue.title
        issueToClassify = pd.DataFrame({"text": [issueText]})
        prediction = self.model.predict(issueToClassify["text"])
        predictedLabel: IssueType = self.getIssueType(prediction)
        print (f"Predicted Label: {predictedLabel.name}")
        return predictedLabel

    def getIssueType(self, prediction) -> IssueType:
        label = IssueType.UNKNOWN
        match prediction[0]:
            case "BUG":
                label = IssueType.BUG
            case "FEATURE":
                label = IssueType.FEATURE
            case "DOCUMENTATION":
                label = IssueType.DOCUMENTATION
            case "PERFORMANCE":
                label = IssueType.PERFORMANCE
            case "TEST_GAP":
                label = IssueType.TEST_GAP
        return label
