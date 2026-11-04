import os
import requests

token = os.getenv("GITHUB_TOKEN")

if not token:
    print("Token not found!")
    exit()

response = requests.get(
    "https://api.github.com/rate_limit",
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    },
)

print("Status:", response.status_code)
print(response.json()["rate"])