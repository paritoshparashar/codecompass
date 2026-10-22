# Represents the Localization block
from src.code_compass.domain.issue import Issue
from src.code_compass.domain.repository import Repository

# Return a list of localized documents based on the issue and repository
class Localization:
    def __init__(self, ranker: Ranker, issue: Issue, repository: Repository):
        self.ranker = ranker
        self.issue = issue
        self.repository = repository


   