"""Tag every saved answer with the claims it makes, using one Claude classifier for all engines.

Replaces the keyword matching used for the first ChatGPT run, so counts are consistent
across engines. Needs ANTHROPIC_API_KEY. Reads data/raw/<engine>-<rival>.json and writes
data/raw/claim-tags-<rival>.json as {"<engine>_<mode>": {"1": "ABD", ...}}.
"""
import glob, json, os, re
from common import http, RIVAL

H = {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}
MODEL = os.environ.get("ANTHROPIC_TAG_MODEL") or os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-5-5"
R = RIVAL
CLAIMS = {
    "A": f"{R} integrates more deeply with Shopify than GetResponse",
    "B": f"GetResponse is cheaper than {R}",
    "C": f"{R} has better segmentation or predictive analytics (CLV, churn, AI predictions)",
    "D": f"{R} has better revenue reporting or attribution",
    "E": f"{R}'s e-commerce automation flows are deeper or more advanced",
    "F": "GetResponse does more beyond email (webinars, courses, landing pages, website builder)",
    "G": f"{R} has stronger SMS",
    "H": "GetResponse puts abandoned cart or e-commerce automation on higher-priced plans",
    "I": "GetResponse is easier to set up or use",
}
GUIDE = ("You label answers about two email marketing tools. A claim counts only if the answer states or clearly "
         "implies it. Ignore the final PICK/REASON lines. Reply with JSON only: {\"claims\": [letters]}.\n\nClaims:\n"
         + "\n".join(f"{k}: {v}" for k, v in CLAIMS.items()))


def tag(text):
    body = {"model": MODEL, "max_tokens": 100, "system": GUIDE,
            "messages": [{"role": "user", "content": text[:20000]}]}
    out = "".join(b.get("text", "") for b in http("https://api.anthropic.com/v1/messages", body, H)["content"])
    m = re.search(r"\{.*\}", out, re.S)
    letters = json.loads(m.group(0))["claims"] if m else []
    return "".join(sorted({l for l in letters if l in CLAIMS}))


def main():
    path = f"data/raw/claim-tags-{R.lower()}.json"
    tags = json.load(open(path)) if os.path.exists(path) else {}
    tags["_claims"] = CLAIMS
    tags["_method"] = f"Claude classifier ({MODEL})"
    for f in sorted(glob.glob(f"data/raw/*-{R.lower()}.json")):
        if "claim-tags" in f:
            continue
        raw = json.load(open(f)); eng = os.path.basename(f).split("-")[0]
        for m in ("off", "on"):
            tags[f"{eng}_{m}"] = {}  # re-tag from scratch
        for r in raw["runs"]:
            key = f"{eng}_{r['search']}"
            tags.setdefault(key, {})[str(r["n"])] = tag(r["text"])
        print(eng, {k: v for k, v in tags.items() if k.startswith(eng)}, flush=True)
    json.dump(tags, open(path, "w"), indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
