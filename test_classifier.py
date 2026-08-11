from codecompass.classifier import IssueClassifier
import os

api_key = os.environ.get("GROQ_API_KEY")
print(f"Using API key: {api_key[:10]}...")  # Print first 10 chars to verify

classifier = IssueClassifier(api_key=api_key)
issues = [
    "OAuth login fails with timeout error",
    "Add support for OAuth 2.0 PKCE flow",
    "README doesn't explain how to configure timeouts",
    "API endpoint takes 10 seconds to respond",
]

for issue in issues:
    print(f"Issue: {issue[:50]}... -> Category: {classifier.classify(issue)}")