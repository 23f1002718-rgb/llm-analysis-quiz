import os
import re
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Secret key for validation
SECRET = os.environ.get("QUIZ_SECRET", "ratisecret123")

app = FastAPI()

class QuizPayload(BaseModel):
    email: str
    secret: str
    url: str

def render_js_page(url):
    """
    Render JavaScript using Jina AI's r.jina.ai text engine.
    Correct syntax: https://r.jina.ai/https://website.com
    """
    render_url = f"https://r.jina.ai/{url}"
    print("Fetching rendered page from:", render_url)

    response = requests.get(render_url, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Render failed: {response.status_code}")

    return response.text

def get_submit_url(text):
    urls = re.findall(r"https?://[^\s\"'>]+", text)
    for u in urls:
        if "submit" in u.lower():
            return u
    return urls[0] if urls else None

def simple_solver(text):
    nums = re.findall(r"-?\d+", text)
    nums = [int(n) for n in nums]

    # If numbers were found → return the sum
    if nums:
        return sum(nums)

    # If no numbers → return a default answer (DEMO requires ANY answer)
    return "demo-answer"

@app.post("/")
async def solve(payload: QuizPayload):
    # 1. Check secret
    if payload.secret != SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # 2. Render page
    html = render_js_page(payload.url)

    # 3. Find submit URL
    submit_url = get_submit_url(html)
    if not submit_url:
        raise HTTPException(status_code=400, detail="No submit URL found")

    # 4. Solve question (simple sum of numbers)
    answer = simple_solver(html)
    print("Answer computed:", answer)


    # 5. Send answer back
    result = requests.post(submit_url, json={
        "email": payload.email,
        "secret": payload.secret,
        "url": payload.url,
        "answer": answer
    })

    try:
        return result.json()
    except:
        return {"status": result.status_code, "text": result.text}
