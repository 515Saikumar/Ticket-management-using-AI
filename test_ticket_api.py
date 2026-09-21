"""
test_ticket_api.py
20 test cases for the Ticket Triage API relevance check + classification.
Run with: python test_ticket_api.py
Requires the FastAPI backend to be running on http://localhost:8000
"""

import requests
import json

API_URL = "http://localhost:8000/extract-ticket"

# ─────────────────────────────────────────────────────────────────────────────
# Test definitions
# Each entry: (test_id, description, username, query, expected_outcome)
# expected_outcome: "PASS" = should create ticket, "BLOCK" = should be rejected (422)
# ─────────────────────────────────────────────────────────────────────────────
TEST_CASES = [
    # ── RELEVANT (should PASS and create ticket) ──────────────────────────────
    (1,  "Login issue",
     "Arjun",   "I cannot login to my work account, it keeps showing an error page.", "PASS"),
    (2,  "Academy portal blank screen",
     "Vishali",  "The Academy portal shows a blank white screen after I log in. I cannot access any courses.", "PASS"),
    (3,  "Salary not credited",
     "Geetha",   "My salary for this month has not been credited to my bank account yet.", "PASS"),
    (4,  "Leave application",
     "Srinivas",  "I want to apply for 3 days of casual leave next week. How do I do it?", "PASS"),
    (5,  "VPN not connecting",
     "Saikumar",  "My VPN is not connecting when I work from home. I am unable to access internal systems.", "PASS"),
    (6,  "Dashboard not loading",
     "Govind",   "The admin dashboard is completely stuck and not loading any ticket data.", "PASS"),
    (7,  "Office laptop issue",
     "Arjun",   "My office laptop is running extremely slow and crashes every hour.", "PASS"),
    (8,  "Onboarding docs missing",
     "Priya",   "I just joined the company and I have not received my onboarding documents or system credentials.", "PASS"),
    (9,  "Academy certification error",
     "Rahul",   "I completed the Python certification course on the LMS but the certificate was not generated.", "PASS"),
    (10, "Email access blocked",
     "Deepa",   "I am unable to access my company email. It says my account is disabled.", "PASS"),

    # ── IRRELEVANT (should BLOCK with 422) ────────────────────────────────────
    (11, "Amazon order complaint",
     "Test",    "My Amazon order has not been delivered yet and the refund was rejected.", "BLOCK"),
    (12, "Food delivery",
     "Test",    "My Swiggy order is 2 hours late and the food is cold. I want a refund.", "BLOCK"),
    (13, "Netflix not working",
     "Test",    "Netflix is not playing videos on my personal TV. It keeps buffering.", "BLOCK"),
    (14, "Personal banking",
     "Test",    "My Paytm wallet is not allowing me to add money and my bank transfer failed.", "BLOCK"),
    (15, "Cricket score query",
     "Test",    "Who won yesterday's IPL cricket match? What is the current score?", "BLOCK"),
    (16, "Social media help",
     "Test",    "My Instagram account has been hacked and I cannot log into it anymore.", "BLOCK"),
    (17, "Flipkart shopping",
     "Test",    "I bought a phone on Flipkart and the seller sent me a fake product. Need help.", "BLOCK"),
    (18, "Food recipe",
     "Test",    "Can you give me a good recipe for making biryani at home?", "BLOCK"),
    (19, "Personal travel",
     "Test",    "I want to book flight tickets to Goa for a vacation next month. Any suggestions?", "BLOCK"),
    (20, "Movie recommendation",
     "Test",    "Can you recommend some good Hollywood movies to watch this weekend?", "BLOCK"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
PASS_COLOR  = "\033[92m"  # green
FAIL_COLOR  = "\033[91m"  # red
WARN_COLOR  = "\033[93m"  # yellow
RESET       = "\033[0m"
BOLD        = "\033[1m"

def run_tests():
    passed = 0
    failed = 0
    results = []

    print(f"\n{BOLD}{'='*65}")
    print("  TICKET TRIAGE API — 20 TEST CASES")
    print(f"{'='*65}{RESET}\n")

    for (tid, desc, username, query, expected) in TEST_CASES:
        try:
            resp = requests.post(
                API_URL,
                json={"username": username, "query": query},
                timeout=30
            )
            status_code = resp.status_code

            if expected == "PASS":
                outcome = "✅ PASS" if status_code == 200 else f"❌ FAIL (got {status_code})"
                ok = status_code == 200
            else:  # BLOCK
                outcome = "✅ PASS" if status_code == 422 else f"❌ FAIL (got {status_code}, expected 422)"
                ok = status_code == 422

            color = PASS_COLOR if ok else FAIL_COLOR
            label = "RELEVANT" if expected == "PASS" else "IRRELEVANT"

            print(f"{color}[{tid:02d}] {outcome}{RESET}  [{label:10s}]  {desc}")
            if not ok:
                try:
                    detail = resp.json().get("detail", resp.text[:120])
                except Exception:
                    detail = resp.text[:120]
                print(f"       {WARN_COLOR}↳ Response: {detail}{RESET}")

            if ok:
                passed += 1
            else:
                failed += 1
            results.append((tid, desc, expected, status_code, ok))

        except requests.exceptions.ConnectionError:
            print(f"{FAIL_COLOR}[{tid:02d}] ❌ CONNECTION ERROR{RESET}  Backend not running on port 8000!")
            failed += 1
            results.append((tid, desc, expected, "ERR", False))
            break
        except Exception as e:
            print(f"{FAIL_COLOR}[{tid:02d}] ❌ EXCEPTION: {e}{RESET}")
            failed += 1
            results.append((tid, desc, expected, "ERR", False))

    # ── Summary ───────────────────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{BOLD}{'─'*65}")
    print(f"  RESULTS: {passed}/{total} passed")
    print(f"{'─'*65}{RESET}")

    if failed == 0:
        print(f"{PASS_COLOR}{BOLD}  🎉 All tests passed! The relevance check is working correctly.{RESET}\n")
    else:
        print(f"{FAIL_COLOR}{BOLD}  ⚠️  {failed} test(s) failed. Review the output above.{RESET}\n")

if __name__ == "__main__":
    run_tests()
