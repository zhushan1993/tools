#!/usr/bin/env python3
"""Test correct API format: handle inside result.handle"""
import requests, json, re, os, time

BASE = "http://10.212.129.61:8889"
USER = os.environ.get("HUE_USER", "zhus")
PASS = os.environ.get("HUE_PASSWORD", "SHANzhu5433510")

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})

# Login
r = s.get(f"{BASE}/hue/accounts/login/")
csrf = re.search(r"""name=["']csrfmiddlewaretoken["']\s+value=["']([^"']+)["']""", r.text).group(1)
r2 = s.post(f"{BASE}/hue/accounts/login/", data={
    "csrfmiddlewaretoken": csrf, "username": USER, "password": PASS, "server": "hue",
}, headers={"Referer": f"{BASE}/hue/accounts/login/"})
assert "login" not in r2.url.lower(), "Login failed"
print("Login OK")
csrf_token = s.cookies.get("csrftoken", "")
h = {"X-CSRFToken": csrf_token}

statement = "SELECT 1 as test"

# EXECUTE - using the format that works
nb_exec = {"type": "query-impala", "name": "test", "snippets": [{"id": "1", "type": "impala",
    "statement_raw": statement, "statement": statement}],
    "isSaved": False, "sessions": [], "skipHistorify": True}
sn_exec = {"id": "1", "type": "impala", "statement_raw": statement, "statement": statement,
           "result": {}, "properties": {}}

r = s.post(f"{BASE}/notebook/api/execute/", data={
    "csrfmiddlewaretoken": csrf_token,
    "notebook": json.dumps(nb_exec),
    "snippet": json.dumps(sn_exec),
}, headers=h)
j = r.json()
handle = j.get("handle", {})
clean_handle = {k: v.strip() if isinstance(v, str) else v for k, v in handle.items()}
print(f"Execute OK, guid={clean_handle['guid'][:20]}...")
time.sleep(2)

# Now use adaptExecutableToNotebook format for status/fetch
snippet_a = {
    "type": "impala",
    "result": {"handle": clean_handle},  # handle inside result!
    "status": "running",
    "id": "1",
    "statement_raw": statement,
    "statement": statement,
    "variables": [],
    "properties": {"settings": []},
}

notebook_s = {
    "type": "impala",  # just "impala", not "query-impala"
    "snippets": [snippet_a],
    "id": None,
    "name": "",
    "isSaved": False,
    "sessions": [],
}

print("\n=== check_status ===")
for label, cs_data in [
    ("adaptExecutable format", {"notebook": json.dumps(notebook_s), "snippet": json.dumps(snippet_a)}),
    ("notebook only", {"notebook": json.dumps(notebook_s)}),
]:
    r = s.post(f"{BASE}/notebook/api/check_status", data={
        "csrfmiddlewaretoken": csrf_token,
        **cs_data
    }, headers=h)
    try:
        j = r.json()
        print(f"  {label}: {json.dumps(j, indent=2)[:500]}")
    except:
        print(f"  {label}: parse error: {r.text[:200]}")

print("\n=== fetch_result_data ===")
frd_data = {
    "csrfmiddlewaretoken": csrf_token,
    "notebook": json.dumps(notebook_s),
    "snippet": json.dumps(snippet_a),
    "rows": "100",
    "startOver": "false",
}
r = s.post(f"{BASE}/notebook/api/fetch_result_data", data=frd_data, headers=h)
try:
    j = r.json()
    print(f"  Result: {json.dumps(j, indent=2)[:500]}")
except:
    # Response might be text (not JSON) that needs JSON.bigdataParse
    print(f"  Raw (first 500): {r.text[:500]}")

# Also try with dataType:text treatment (fetch_result_data might return text)
print("\n=== fetch_result_data (text response) ===")
r = s.post(f"{BASE}/notebook/api/fetch_result_data", data=frd_data, headers={
    **h, "Accept": "text/plain, */*"
})
print(f"  Status: {r.status_code}, Content-Type: {r.headers.get('Content-Type', 'N/A')}")
if r.status_code == 200:
    # Try to find JSON in the response
    text = r.text.strip()
    print(f"  Raw first 500: {text[:500]}")
    if text.startswith('{') or text.startswith('['):
        try:
            j = json.loads(text)
            print(f"  Parsed: {json.dumps(j, indent=2)[:500]}")
        except:
            pass
    else:
        # Might be bigdata format
        print(f"  Not JSON start, trying to find JSON...")
        # Sometimes Django wraps with HTML
        if '<' not in text[:10]:
            try:
                j = json.loads(text)
                print(f"  Parsed: {json.dumps(j, indent=2)[:500]}")
            except:
                pass

print("\nDone")
