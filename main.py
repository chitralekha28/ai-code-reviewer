from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import requests
import os
import json
import sqlite3
from groq import Groq
from dotenv import load_dotenv

# Load credentials from .env file securely
load_dotenv()

app = FastAPI()

# Initialize the Groq Client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
def init_db():
    conn = sqlite3.connect("metrics.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT,
            pr_number INTEGER,
            bugs INTEGER,
            security INTEGER,
            smells INTEGER,
            performance INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()
def log_review_to_db(repo_name, pr_number, comments):
    """Parses the AI comments and saves counts into the database."""
    bugs = sum(1 for c in comments if "BUG" in c.get("body", "").upper())
    security = sum(1 for c in comments if "SECURITY" in c.get("body", "").upper())
    smells = sum(1 for c in comments if "SMELL" in c.get("body", "").upper())
    perf = sum(1 for c in comments if "PERFORMANCE" in c.get("body", "").upper())
    
    conn = sqlite3.connect("metrics.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (repo_name, pr_number, bugs, security, smells, performance) VALUES (?, ?, ?, ?, ?, ?)",
        (repo_name, pr_number, bugs, security, smells, perf)
    )
    conn.commit()
    conn.close()
@app.get("/")
def home():
    return {"message": "AI Inline Code Reviewer is running!"}


# --- ASYNC BACKGROUND WORKER ---
def process_code_review(payload: dict):
    """Handles downloading diffs, dismissing old comments, running Groq, and posting to GitHub."""
    try:
        pr_data = payload.get("pull_request", {})
        pr_number = payload.get("number")
        
        # Safely get the repository full name
        repo_name = pr_data.get("base", {}).get("repo", {}).get("full_name")
        if not repo_name:
            repo_name = payload.get("repository", {}).get("full_name")
            
        diff_url = pr_data.get("diff_url")
        print(f"🔥 Asynchronous worker starting for PR #{pr_number} on {repo_name}")
        
        if not diff_url:
            print("⚠️ No diff URL found in payload.")
            return

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # =========================================================================
        # 🧹 HACKATHON FEATURE: DISMISS PREVIOUS BOT REVIEWS TO PREVENT SPAM
        # =========================================================================
        print("🧹 Checking for stale, previous bot reviews to dismiss...")
        list_reviews_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/reviews"
        existing_reviews_res = requests.get(list_reviews_url, headers=headers)
        
        if existing_reviews_res.status_code == 200:
            existing_reviews = existing_reviews_res.json()
            for review in existing_reviews:
                review_body = review.get("body", "") or ""
                # Look for our exact automated signature header string
                if "🤖 Automated Groq Line-by-Line Code Review" in review_body:
                    review_id = review.get("id")
                    print(f"🗑️ Dismissing stale review ID: {review_id}")
                    
                    dismiss_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/reviews/{review_id}/dismissals"
                    dismiss_payload = {"message": "Stale review dismissed; generating a fresh analysis for new commits."}
                    requests.put(dismiss_url, headers=headers, json=dismiss_payload)
        # =========================================================================

        # 1. Fetch the incoming code diff
        diff_response = requests.get(diff_url)
        if diff_response.status_code != 200:
            print(f"❌ Failed to fetch diff from GitHub. Status: {diff_response.status_code}")
            return
            
        git_diff = diff_response.text
        print("📦 Successfully downloaded Git Diff data.")
        
        # 2. Upgraded System Prompt with Explicit Taxonomy and Blockquote Formatting
        system_prompt = (
            "You are a production-grade automated code reviewer for elite engineering teams. "
            "Analyze the incoming git diff line-by-line. Your job is to find issues and categorize them "
            "STRICTLY into one of these four buckets:\n"
            "1. 'Bug' - Logic errors, broken edge cases, null pointers, or crashes.\n"
            "2. 'Security' - Hardcoded credentials, injection vulnerabilities, unsafe dependencies, or data leaks.\n"
            "3. 'Code Smell' - Poor readability, violation of clean code principles, dead code, or lack of proper type hinting.\n"
            "4. 'Performance' - Inefficient loops, memory leaks, redundant database/API calls, or high time complexity.\n\n"
            "GUARDRAILS:\n"
            "- ONLY flag legitimate, clear issues. Do not be overly pedantic or praise clean code.\n"
            "- If a line does not have a clear issue matching the four categories, DO NOT include it in the response.\n"
            "- Carefully read the diff headers (e.g., @@ -1,4 +1,8 @@) to calculate the exact line number of the new additions.\n\n"
            "You must respond ONLY with a raw JSON array of objects. Do not include markdown code fences (like ```json).\n"
            "Each object in the array must follow this exact structure:\n"
            "{\n"
            "  \"path\": \"filename_here.py\",\n"
            "  \"line\": 4,\n"
            "  \"body\": \"> ### ALERT_HEADER_HERE\\n\\n**Issue:** Concise description of the problem.\\n\\n**Fix:** Step-by-step instructions or clean code block demonstrating how to refactor or resolve it.\"\n"
            "}\n"
            "Match the ALERT_HEADER_HERE exactly to the type of issue (e.g., '> ### 🛑 SECURITY RISK', '> ### ⚡ PERFORMANCE ISSUE', '> ### 🐛 BUG DETECTED', '> ### 🧼 CODE SMELL')."
        )
        
        print("🤖 Requesting inline analysis from Groq (JSON Mode)...")
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review this git diff and find the line numbers for errors:\n\n{git_diff}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,  # Low temperature ensures strict JSON compliance
            response_format={"type": "json_object"} # Forces Groq to return clean JSON
        )
        
        raw_ai_response = chat_completion.choices[0].message.content
        print("📝 Groq Line Analysis Complete!")
        
        # Safely parse the JSON generated by the AI
        review_comments = json.loads(raw_ai_response)
        
        # If the AI wrapped it in a root key like {"comments": [...]}, extract the array
        if isinstance(review_comments, dict):
            for key in ["comments", "errors", "reviews"]:
                if key in review_comments:
                    review_comments = review_comments[key]
                    break
                    
        # 3. Post Inline Review Comments back to GitHub
       # 3. Post Inline Review Comments back to GitHub
        if isinstance(review_comments, list):
            log_review_to_db(repo_name, pr_number, review_comments)
            print("💾 Review metrics successfully written to SQLite database.")

        if not review_comments or not isinstance(review_comments, list):
            print("🤷 No specific line-level inline bugs detected.")
            return

        print(f"💬 Validating and filtering {len(review_comments)} inline comment(s) for GitHub...")
        
        # Enforce strict typing on fields returned by Groq before sending to GitHub
        valid_comments = []
        for comment in review_comments:
            if isinstance(comment, dict) and "path" in comment and "line" in comment and "body" in comment:
                try:
                    # Force line numbers to be integers; skip if corrupted
                    comment["line"] = int(comment["line"])
                    valid_comments.append(comment)
                except (ValueError, TypeError):
                    print(f"⚠️ Skipping comment with invalid line format: {comment.get('line')}")

        if not valid_comments:
            print("🤷 No structurally valid comments survived parsing.")
            return

        print(f"🚀 Posting {len(valid_comments)} authenticated inline comment(s) to GitHub Pulls Review API...")
        
        # Clean, explicit URL configuration with no destructive string manipulation
        review_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/reviews"
        
        review_payload = {
            "body": "### 🤖 Automated Groq Line-by-Line Code Review\nI have scanned your changes and flagged a few areas that require attention below.",
            "event": "COMMENT",
            "comments": valid_comments
        }
        
        github_response = requests.post(review_url, headers=headers, json=review_payload)
        
        if github_response.status_code in [200, 201]:
            print("✅ Inline review comments posted successfully on GitHub!")
        else:
            print(f"❌ Failed to post review. Status code: {github_response.status_code}")
            print(github_response.text)
            print("💡 Tip: If receiving 404, verify that the 'path' exactly matches files in the PR, and 'line' points to an added line inside the diff hunks.")
    except Exception as e:
        print(f"❌ Error inside background processing thread: {str(e)}")


# --- MAIN WEBHOOK ROUTE ---
# --- MAIN WEBHOOK ROUTE ---
@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    action = payload.get("action")
    
    print(f"\n➔ Received webhook! Action: {action}")
    
    # Trigger active code review on new code submission hooks
    if action in ["opened", "synchronize", "reopened"]:
        background_tasks.add_task(process_code_review, payload)
        return {"status": "accepted", "message": "Code review task spawned successfully."}
        
    # Extra Hackathon Polish: Clean up comments when PR is merged or closed
    elif action == "closed":
        pr_data = payload.get("pull_request", {})
        pr_number = payload.get("number")
        repo_name = pr_data.get("base", {}).get("repo", {}).get("full_name") or payload.get("repository", {}).get("full_name")
        is_merged = pr_data.get("merged", False)
        
        if is_merged:
            print(f"🎉 PR #{pr_number} was successfully MERGED into main! Running final sweep...")
        else:
            print(f"🚪 PR #{pr_number} was closed without merging. Running final sweep...")
            
        # Spawn a final background task just to dismiss leftover bot comments 
        background_tasks.add_task(process_code_review, payload) 
        return {"status": "accepted", "message": "PR closed. Final comment cleanup triggered."}
        
    return {"status": "ignored", "message": f"Action '{action}' is not tracked."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)