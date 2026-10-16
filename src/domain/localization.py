# Represents the Localization block
from domain.issue import Issue
from domain.repository import Repository

# Return a list of localized documents based on the issue and repository
class Localization:
    def __init__(self, ranker: Ranker, issue: Issue, repository: Repository):
        self.ranker = ranker
        self.issue = issue
        self.repository = repository


   