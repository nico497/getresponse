"""Shared prompts, HTTP helper and output writer for the engine runners."""
import json, os, time, datetime, urllib.request, urllib.error

RIVAL = os.environ.get("RIVAL", "Klaviyo")

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


def http(url, body=None, headers=None, timeout=240):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:600]
            if e.code in (429, 500, 502, 503, 529) and attempt < 3:
                time.sleep(15 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")


def first_available(ids, preferred, env_name):
    if os.environ.get(env_name):
        return os.environ[env_name]
    for m in preferred:
        if m in ids:
            return m
    raise SystemExit(f"Set {env_name}: none of {preferred} are available. Available: {sorted(ids)[:30]}")


def run_all(engine, model, call, modes=("off", "on")):
    out = {"engine": engine, "model": model, "rival": RIVAL,
           "collected": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "runs": []}
    for mode in modes:
        for i, p in enumerate(PROMPTS, 1):
            r = call(p + SUFFIX, mode == "on")
            r.update({"n": i, "prompt": p, "search": mode})
            out["runs"].append(r)
            print(f"{engine} · search {mode} · prompt {i}: {len(r['text'])} chars, searched={r['searched']}, sources={len(r['sources'])}", flush=True)
    key = engine.split()[0].lower()
    path = f"data/raw/{key}-{RIVAL.lower()}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w"), indent=1)
    print("wrote", path)
