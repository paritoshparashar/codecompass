from ....application.classification_package.classification_strategy import (
    ClassificationStrategy,
)
from ....domain.issue import Issue, IssueType


# Assumes we have trained a BM25 regression model (Vocabulary and weights)
class BM25RegStrategy(ClassificationStrategy):
    def classify(self, issue: Issue) -> IssueType:
        # Implement the BM25 regression classification logic here
        # For now, we can just return a placeholder value
        '''
        1 - IssueText -> Tokenization (Chose a tokenization strategy words vs chars vs subwords)
        2 - Create Vectors(dim = len(vocabulary)) of Tokens using this strategy scores
        3 - 
        '''
        return IssueType.UNKNOWN