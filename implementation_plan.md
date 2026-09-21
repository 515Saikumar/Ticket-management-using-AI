# Hybrid ML + LLM Integration Guide

You asked for a step-by-step breakdown of how to integrate a traditional ML model with the Groq LLM. This hybrid approach uses the ML model to quickly predict the `category` and `priority`, and then passes those predictions to the LLM to generate the `summary`.

Since you requested no code changes be made directly, this document serves as your complete "copy-paste" guide to modifying `backend/main.py` when you are ready.

---

## Step 1: Install ML Dependencies
You will need to install the tools used for traditional Machine Learning. Update your `requirements.txt` to include:
```text
scikit-learn
joblib
```
*(Run `pip install -r requirements.txt` after adding these).*

---

## Step 2: Load the ML Models in FastAPI
At the top of your `backend/main.py`, you need to import `joblib` and load the `.pkl` files (which you exported from your ML training dataset) into memory. Loading them at startup ensures they don't slow down every request.

```python
import joblib

# Add this near your other globals like `_supabase`
_vectorizer = None
_category_model = None
_priority_model = None

# We use the FastAPI lifespan event to load models when the server starts
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _vectorizer, _category_model, _priority_model
    try:
        # Replace these paths with the actual paths to your trained models
        _vectorizer = joblib.load("models/vectorizer.pkl")
        _category_model = joblib.load("models/category_model.pkl")
        _priority_model = joblib.load("models/priority_model.pkl")
        print("ML Models loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load ML models: {e}")
    yield

# Update your FastAPI app initialization to use the lifespan
app = FastAPI(
    title="Ticket Triage API",
    description="Hybrid ML + LLM backend.",
    version="1.0.0",
    lifespan=lifespan
)
```

---

## Step 3: Update the LLM Prompt
Currently, your `SYSTEM_PROMPT` asks the LLM to extract everything. We need to change the prompt so it knows that the `category` and `priority` have *already* been decided by the ML model, and it only needs to generate the summary.

Update your `SYSTEM_PROMPT` in `main.py`:
```python
SYSTEM_PROMPT = """You are a helpdesk assistant. 
You will be given a user's query, as well as a Category and Priority that were assigned by our Machine Learning system.

Your job is to:
1. Accept the provided Category and Priority as-is.
2. Generate a clear, concise 1-2 sentence `summary` of the issue.

Respond ONLY with valid JSON in this exact format:
{"summary": "the 1-2 sentence summary"}

No markdown, no explanation.
"""
```

---

## Step 4: Update the `/extract-ticket` logic
This is the core logic where we combine ML and LLMs. Replace the inside of your `extract_ticket` function with this pipeline:

```python
@app.post("/extract-ticket", response_model=TicketResponse)
def extract_ticket(req: TicketRequest):
    if not req.username.strip() or not req.query.strip():
        raise HTTPException(status_code=400, detail="Both 'username' and 'query' are required.")

    # ─────────────────────────────────────────────────────────────────
    # Phase 1: Machine Learning Prediction
    # ─────────────────────────────────────────────────────────────────
    if _vectorizer and _category_model and _priority_model:
        # Convert text to features
        features = _vectorizer.transform([req.query])
        
        # Predict using your models
        ml_category = _category_model.predict(features)[0]
        ml_priority = _priority_model.predict(features)[0]
    else:
        # Fallback if models failed to load
        ml_category = "General"
        ml_priority = "Medium"

    # ─────────────────────────────────────────────────────────────────
    # Phase 2: LLM Summary Generation
    # ─────────────────────────────────────────────────────────────────
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # Pass the ML predictions TO the LLM in the user prompt
    user_content = f"Name: {req.username}\nCategory: {ml_category}\nPriority: {ml_priority}\n\nIssue:\n{req.query}"

    last_error = None
    response = None

    for model in GROQ_FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "max_tokens": 150, # Reduced tokens since we only need a summary
        }

        try:
            response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                break
            last_error = f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)
            response = None

    if response is None or response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"LLM failed: {last_error}")

    # ─────────────────────────────────────────────────────────────────
    # Phase 3: Combine ML + LLM data
    # ─────────────────────────────────────────────────────────────────
    try:
        raw_content = response.json()["choices"][0]["message"]["content"]
        llm_fields = json.loads(raw_content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM JSON Error: {e}")

    extracted = TicketResponse(
        username=req.username.strip() or "Anonymous",
        category=ml_category, # From ML
        priority=ml_priority, # From ML
        summary=llm_fields.get("summary", req.query[:250]) # From LLM
    )

    # ─────────────────────────────────────────────────────────────────
    # Phase 4: Insert to Supabase (Unchanged)
    # ─────────────────────────────────────────────────────────────────
    db = get_supabase()
    db.table("tickets").insert({
        "username": extracted.username,
        "original_query": req.query.strip(),
        "category": extracted.category,
        "priority": extracted.priority,
        "summary": extracted.summary,
        "status": "Open",
    }).execute()

    return extracted
```

### Why this approach works:
1. **Accuracy**: You use your custom trained ML model exactly for what it's good at (predicting your specific categories/priorities from your dataset).
2. **Readability**: You still utilize the LLM's excellent NLP abilities to write a clean, human-readable summary, but you save tokens (making it faster/cheaper) because the LLM no longer has to "think" about classification.
