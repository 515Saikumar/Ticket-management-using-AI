"""
backend/main.py — FastAPI backend for AI-powered ticket triage

Flow:
  1. React frontend  →  POST /extract-ticket  {username, query}
  2. Groq API call   →  llama-3.3-70b-versatile  (direct HTTP, no SDK)
  3. Parse JSON      →  {username, category, priority, summary}
  4. Supabase insert →  tickets table (service-role key, server-side)
  5. Return result   →  frontend shows success card
"""

import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ── Groq config ───────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "groq/compound",
    "canopylabs/orpheus-v1-english"
]
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

# ── Supabase config ───────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # service role — safe server-side

VALID_CATEGORIES = {"Technical", "Academy", "HR", "General"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}

# ── Lazy Supabase client ──────────────────────────────────────────────
_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise HTTPException(status_code=500, detail="Supabase credentials missing in backend/.env")
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

# ── FastAPI app ───────────────────────────────────────────────────────
app = FastAPI(
    title="Ticket Triage API",
    description="Calls Groq API to classify helpdesk tickets, then stores them in Supabase.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# ── Request / Response schemas ────────────────────────────────────────
class TicketRequest(BaseModel):
    username: str
    query: str

class TicketResponse(BaseModel):
    username: str
    category: str
    priority: str
    summary: str

# ── LLM system prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpdesk ticket classifier for an organisation.

FIRST, decide if the query is valid and related to the organisation's internal helpdesk.
Internal topics include: work systems, software/hardware issues, login/account access,
Academy (LMS) portal, HR matters (leave, salary, onboarding), office policies, and similar workplace issues.

Respond ONLY with {"relevant": false} in ANY of these cases:
1. The query is COMPLETELY UNRELATED to the organisation (e.g., personal shopping, food delivery,
   social media, entertainment, personal banking, or any non-work topic).
2. The query is GIBBERISH, random characters, or has no meaningful content (e.g., 'asdfgh jkl', 'zzz', 'xyz abc').
3. The query is a SINGLE VAGUE WORD with no context (e.g., just 'help', 'error', 'issue', 'problem').

If the query IS a valid, work-related request (even with typos or short phrasing), extract:
- username: use the provided name, or "Anonymous" if not given
- category: exactly one of [Technical, Academy, HR, General]
  - Academy: course content, learning materials, certifications, training programmes. (CRITICAL: ANY technical issues or bugs specifically related to accessing the academy portal or courses MUST be classified as Academy, not Technical).
  - HR: leave, salary, payroll, employee welfare, job applications, onboarding. (Note: general office policies like dress code, WFH rules, and office timings belong in General).
  - Technical: software bugs, login errors, system/account access, dashboard issues. (UNLESS it relates to the Academy portal, which goes to Academy).
  - General: admin queries, feedback, office timings, work from home rules, dress code policy, or anything else.
- priority: exactly one of [Low, Medium, High, Critical]
  - Low: minor inconvenience, not time-sensitive
  - Medium: affects work but has a workaround
  - High: blocking work, needs prompt attention
  - Critical: complete work stoppage, severe or widespread impact
- summary: a clear, concise 1-2 sentence description of the issue

No markdown, no explanation. Valid JSON only.
Example (relevant): {"username":"Arjun","category":"Academy","priority":"High","summary":"User cannot access the academy portal."}
Example (irrelevant/gibberish/vague): {"relevant": false}"""


# ── Main endpoint ─────────────────────────────────────────────────────
@app.post("/extract-ticket", response_model=TicketResponse)
def extract_ticket(req: TicketRequest):
    """
    1. Call Groq API → extract ticket fields via LLM
    2. Validate and sanitise the fields
    3. Insert enriched ticket into Supabase
    4. Return extracted fields to the frontend
    """
    if not req.username.strip() or not req.query.strip():
        raise HTTPException(status_code=400, detail="Both 'username' and 'query' are required.")

    # ── Step 1: Call Groq API (direct HTTP) with fallbacks ────────────
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = None
    response = None

    for model in GROQ_FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Name: {req.username.strip()}\n\nIssue description:\n{req.query.strip()}",
                },
            ],
            "temperature": 0.1,
            "max_tokens": 300,
        }

        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                break  # Success, exit the loop!
            
            last_error = f"Model {model} failed with HTTP {response.status_code}: {response.text}"
            print(f"Fallback warning: {last_error}")
        except requests.exceptions.RequestException as e:
            last_error = f"Model {model} request failed: {e}"
            print(f"Fallback warning: {last_error}")
            response = None

    if response is None or response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"All models failed. Last error: {last_error}")

    # ── Step 2: Parse LLM response ────────────────────────────────────
    try:
        raw_content = response.json()["choices"][0]["message"]["content"]
        fields = json.loads(raw_content)
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"Unexpected Groq response structure: {e}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")

    # ── Step 2b: Relevance check ──────────────────────────────────────
    # If the LLM flagged the query as off-topic, reject it cleanly.
    # No Supabase insert is made for irrelevant queries.
    if fields.get("relevant") is False:
        raise HTTPException(
            status_code=422,
            detail="Please provide detailed information about your work-related problem. "
                   "We handle issues like system access, HR queries, Academy portal issues, "
                   "or technical errors. Vague or unrelated queries cannot be processed."
        )

    # ── Step 3: Validate + sanitise ───────────────────────────────────
    category = fields.get("category", "General")
    priority = fields.get("priority", "Medium")
    if category not in VALID_CATEGORIES:
        category = "General"
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    extracted = TicketResponse(
        username=fields.get("username") or req.username.strip() or "Anonymous",
        category=category,
        priority=priority,
        summary=fields.get("summary") or req.query.strip()[:250],
    )

    # ── Step 4: Insert into Supabase ──────────────────────────────────
    db = get_supabase()
    result = (
        db.table("tickets")
        .insert({
            "username":       extracted.username,
            "original_query": req.query.strip(),
            "category":       extracted.category,
            "priority":       extracted.priority,
            "summary":        extracted.summary,
            "status":         "Open",
        })
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=500, detail="Supabase insert returned no data.")

    return extracted


# ── Health check ──────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Verify the backend is running and check config."""
    return {
        "status": "ok",
        "groq_models": GROQ_FALLBACK_MODELS,
        "groq_url": GROQ_URL,
        "groq_key_set": bool(GROQ_API_KEY),
        "supabase_url": SUPABASE_URL[:40] + "..." if SUPABASE_URL else "NOT SET",
    }
