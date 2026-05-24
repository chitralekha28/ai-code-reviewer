import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration - Replace with your exact PR details
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Make sure your .env has this variable!
REPO_OWNER = "chitralekha28"
REPO_NAME = "ai-code-reviewer"
PR_NUMBER = 2  # The Pull Request number showing on your GitHub screen

def post_live_comment():
    print("🤖 Agent initiating direct code review pass...")
    
    # Target URL for creating a review comment on a PR
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{PR_NUMBER}/reviews"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Mocking the precise payload your Groq engine generates
    payload = {
        "commit_id": "b45736c2ef6dfb77be368a5c37ca5e5077bd6be6", # Look at your PR's latest commit ID on GitHub and paste it here
        "event": "COMMENT",
        "comments": [
            {
                "path": "bad_code.py",
                "position": 5,
                "body": "🚨 **GroqReviewer AI Security Audit:**\nCritical Security Risk: Hardcoded AWS Secret Key detected. Move this configuration value to an isolated environment variable file (`.env`) immediately."
            },
            {
                "path": "bad_code.py",
                "position": 12,
                "body": "⚠️ **GroqReviewer AI Performance Audit:**\nInefficient nested loop detected ($O(N^2)$ complexity). Consider using a hash map or single-pass linear scan to check for duplicate IDs."
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201 or response.status_code == 200:
        print("🎉 Success! Inline comments successfully transmitted to GitHub PR.")
    else:
        print(f"❌ Failed with status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    post_live_comment()
