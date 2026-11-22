"""Run the 10 head-to-head prompts on ChatGPT (OpenAI API), web search off and on.

Writes data/raw/chatgpt-<rival>.json. Needs the OPENAI_API_KEY environment variable
(a GitHub Actions secret). Model can be changed with the OPENAI_MODEL variable.
"""
import json, os, sys, time, datetime, urllib.request, urllib.error

RIVAL = os.environ.get("RIVAL", "Klaviyo")
KEY = os.environ["OPENAI_API_KEY"]
PREFERRED = ["gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o"]


def pick_model():
    """Use OPENAI_MODEL if set, else the newest preferred model this key can use."""
    if os.environ.get("OPENAI_MODEL"):
        return os.environ["OPENAI_MODEL"]
    req = urllib.request.Request("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        ids = {m["id"] for m in json.load(r).get("data", [])}
    for m in PREFERRED:
        if m in ids:
            return m
    raise SystemExit("None of the preferred models are available: " + ", ".join(PREFERRED))


MODEL = None

PROMPTS = [
    f"Which is better for an online store, GetResponse or {RIVAL}?",
    f"Which is better for an online store, {RIVAL} or GetResponse?",
    f"GetResponse vs {RIVAL} for Shopify",
    f"Best email marketing for a small ecommerce store: GetResponse or {RIVAL}?",
    f"Is GetResponse cheaper than {RIVAL}?",
    f"GetResponse vs {RIVAL} for abandoned cart emails",
    f"GetResponse vs {RIVAL} automation",
    f"{RIVAL} alternatives for ecommerce",
    f"GetResponse vs {RIVAL} pros and cons",
    f"Should I switch from {RIVAL} to GetResponse?",
]
SUFFIX = ("\n\nAnswer the way you normally would for a user. After your answer, on its own line write "
          f"PICK: GetResponse | {RIVAL} | None (which you'd recommend for an online store), then "
          "REASON: the main reason in under 12 words.")


def call(prompt, search):
    body = {"model": MODEL, "input": prompt + SUFFIX}
    if search:
        body["tools"] = [{"type": "web_search"}]
        body["tool_choice"] = "required"
    req = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(10 * (attempt + 1)); continue
            raise SystemExit(f"OpenAI error {e.code}: {msg}")
    text, sources = "", []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")
                    for a in c.get("annotations", []) or []:
                        if a.get("type") == "url_citation" and a.get("url"):
                            sources.append(a["url"])
    searched = any(i.get("type") == "web_search_call" for i in data.get("output", []))
    return {"text": text.strip(), "searched": searched, "sources": sorted(set(sources))}


def main():
    global MODEL
    MODEL = pick_model()
    print("model:", MODEL, flush=True)
    out = {"engine": "ChatGPT (OpenAI API)", "model": MODEL, "rival": RIVAL,
           "collected": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "runs": []}
    for mode in ("off", "on"):
        for i, p in enumerate(PROMPTS, 1):
            r = call(p, mode == "on")
            r.update({"n": i, "prompt": p, "search": mode})
            out["runs"].append(r)
            print(f"search {mode} · prompt {i}: {len(r['text'])} chars, searched={r['searched']}", flush=True)
    path = f"data/raw/chatgpt-{RIVAL.lower()}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
