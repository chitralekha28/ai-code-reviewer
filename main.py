from fastapi import FastAPI, Request, Response
import json

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Code Reviewer Server is running!"}

@app.post("/webhook")
async def github_webhook(request: Request):
    # GitHub sends data as JSON in the body of a POST request
    payload = await request.json()
    
    # For now, let's just look at what action happened in the Pull Request
    action = payload.get("action")
    print(f"➔ Received webhook! Action: {action}")
    
    # We only care when a PR is opened, synchronized (new code pushed), or reopened
    if action in ["opened", "synchronize", "reopened"]:
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")
        print(f"🔥 Processing Pull Request #{pr_number} on repo: {repo_name}")
        
        # This is where our AI logic will go in the next steps!
        
    return Response(status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)