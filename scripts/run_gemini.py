"""Run the 10 prompts on Gemini (Gemini API), Google Search grounding off and on.

Needs GEMINI_API_KEY (GitHub secret). Optional GEMINI_MODEL (GitHub variable).
Writes data/raw/gemini-<rival>.json. Note: the API is not the Gemini app; it is used
because search can be switched off and on, which the app does not allow.
"""
import os
from common import http, first_available, run_all

KEY = os.environ["GEMINI_API_KEY"]
BASE = "https://generativelanguage.googleapis.com/v1beta"
H = {"x-goog-api-key": KEY}
PREFERRED = ["gemini-3-pro-preview", "gemini-3-pro", "gemini-2.5-pro", "gemini-2.5-flash"]


def call(prompt, search):
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if search:
        body["tools"] = [{"google_search": {}}]
    data = http(f"{BASE}/models/{MODEL}:generateContent", body, H)
    cand = (data.get("candidates") or [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    gm = cand.get("groundingMetadata") or {}
    # Grounding URIs are Google redirect links; the title holds the source domain.
    sources = sorted({(c.get("web") or {}).get("title", "") for c in gm.get("groundingChunks", [])} - {""})
    return {"text": text.strip(), "searched": bool(gm.get("webSearchQueries")), "sources": sources,
            "queries": gm.get("webSearchQueries", [])}


if __name__ == "__main__":
    ids = {m["name"].split("/")[-1] for m in http(f"{BASE}/models?pageSize=200", None, H).get("models", [])}
    MODEL = first_available(ids, PREFERRED, "GEMINI_MODEL")
    print("model:", MODEL, flush=True)
    run_all("Gemini (Gemini API)", MODEL, call)
