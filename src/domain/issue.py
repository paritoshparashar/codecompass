# Class for the issue being processed

class Issue:
    def __init__(self, issue_id: int, title: str, description: str):
        self.issue_id = issue_id
        self.title = title
        self.description = description
        self.label = None  # Label can be set later

    def __repr__(self):
        return f"Issue(issue_id={self.issue_id}, title={self.title})"