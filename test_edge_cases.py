"""
test_edge_cases.py
Edge case tests - vague, short, misspelled, and ambiguous queries.
Run with: python test_edge_cases.py
"""

import requests

API_URL = "http://localhost:8000/extract-ticket"

PASS_COLOR = "\033[92m"
FAIL_COLOR = "\033[91m"
WARN_COLOR = "\033[93m"
RESET      = "\033[0m"
BOLD       = "\033[1m"

EDGE_CASES = [
    # (id, description, username, query, expected)

    # ── The user's exact query (vague + typo) ───────────────────────────────
    (1,  'User query: "im facing login issue for this protol"',
     "Arjun",  "im facing login issue for this protol",    "PASS"),

    # ── Very short / one-word ────────────────────────────────────────────────
    (2,  "Single word: 'help'  → too vague",
     "Test",   "help",                                     "BLOCK"),  # < 4 words, blocked on frontend

    (3,  "Single word: 'error'  → too vague",
     "Test",   "error",                                    "BLOCK"),  # < 4 words, blocked on frontend

    # ── Typo-heavy but work-related ──────────────────────────────────────────
    (4,  "Misspelled: 'I cant acess my acount'",
     "Ravi",   "I cant acess my acount on the compny sistem",  "PASS"),

    (5,  "Misspelled: 'acedemy potal is not opning'",
     "Priya",  "acedemy potal is not opning aftr login",   "PASS"),

    # ── Ambiguous — could be work or personal ───────────────────────────────
    (6,  "Ambiguous: 'my account is not working'",
     "Test",   "my account is not working",                "PASS"),

    (7,  "Ambiguous: 'payment failed'  (personal context)",
     "Test",   "payment failed for my online purchase",    "BLOCK"),

    # ── Mixed: off-topic keyword but work context ────────────────────────────
    (8,  "Mixed: Amazon laptop ordered by company",
     "Test",   "The laptop my company ordered from Amazon arrived but it is not connecting to our office network",  "PASS"),

    # ── Purely irrelevant but politely phrased ───────────────────────────────
    (9,  "Polite irrelevant: 'please help me with my Netflix'",
     "Test",   "Could you please help me with my Netflix subscription? It is not working.",   "BLOCK"),

    # ── Gibberish ────────────────────────────────────────────────────────────
    (10, "Gibberish: 'asdfgh jklqwerty'  → LLM blocks",
     "Test",   "asdfgh jklqwerty zxcvbnm",               "BLOCK"),
]

def run():
    passed = 0
    failed = 0

    print(f"\n{BOLD}{'='*68}")
    print("  EDGE CASE TESTS")
    print(f"{'='*68}{RESET}\n")

    for (tid, desc, username, query, expected) in EDGE_CASES:
        try:
            resp = requests.post(API_URL, json={"username": username, "query": query}, timeout=30)
            code = resp.status_code

            if expected == "PASS":
                ok = code == 200
                label = "RELEVANT"
                result = "✅ PASS" if ok else f"❌ FAIL (got HTTP {code}, expected 200)"
            else:
                ok = code == 422
                label = "IRRELEVANT"
                result = "✅ PASS" if ok else f"❌ FAIL (got HTTP {code}, expected 422)"

            color = PASS_COLOR if ok else FAIL_COLOR
            print(f"{color}[{tid:02d}] {result}{RESET}")
            print(f"     [{label:10s}] {desc}")
            print(f"     Query: \"{query}\"")

            if not ok:
                try:
                    detail = resp.json()
                    print(f"     {WARN_COLOR}Response: {detail}{RESET}")
                except Exception:
                    print(f"     {WARN_COLOR}Response: {resp.text[:150]}{RESET}")
            elif code == 200:
                try:
                    data = resp.json()
                    print(f"     {WARN_COLOR}→ Category: {data.get('category')} | Priority: {data.get('priority')}{RESET}")
                except Exception:
                    pass
            print()

            passed += ok
            failed += (not ok)

        except requests.exceptions.ConnectionError:
            print(f"{FAIL_COLOR}[{tid:02d}] ❌ CONNECTION ERROR — Backend not running on port 8000!{RESET}\n")
            break
        except Exception as e:
            print(f"{FAIL_COLOR}[{tid:02d}] ❌ EXCEPTION: {e}{RESET}\n")
            failed += 1

    total = passed + failed
    print(f"{BOLD}{'─'*68}")
    print(f"  RESULTS: {passed}/{total} passed")
    print(f"{'─'*68}{RESET}")
    if failed == 0:
        print(f"{PASS_COLOR}{BOLD}  🎉 All edge cases passed!{RESET}\n")
    else:
        print(f"{FAIL_COLOR}{BOLD}  ⚠️  {failed} edge case(s) failed.{RESET}\n")

if __name__ == "__main__":
    run()
