"""Run the 10 prompts on Claude (Anthropic API), web search off and on.

Needs ANTHROPIC_API_KEY (GitHub secret). Optional ANTHROPIC_MODEL (GitHub variable).
Writes data/raw/claude-<rival>.json with each answer's text, pick, reason and cited URLs.
"""
import os
from common import http, first_available, run_all

KEY = os.environ["ANTHROPIC_API_KEY"]
H = {"x-api-key": KEY, "anthropic-version": "2023-06-01"}
PREFERRED = ["claude-sonnet-5-5", "claude-opus-5-5", "claude-sonnet-4-5", "claude-sonnet-4-0"]


def call(prompt, search):
    body = {"model": MODEL, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}
    if search:
        body["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5,
                          "user_location": {"type": "approximate", "country": "US"}}]
        body["tool_choice"] = {"type": "any"}
    try:
        data = http("https://api.anthropic.com/v1/messages", body, H)
    except RuntimeError as e:
        if search and "tool_choice" in str(e):  # forcing a server tool not allowed: let Claude decide
            body.pop("tool_choice"); data = http("https://api.anthropic.com/v1/messages", body, H)
        else:
            raise
    text, sources, searched = "", [], False
    for b in data.get("content", []):
        if b.get("type") == "text":
            text += b.get("text", "")
            for c in b.get("citations") or []:
                if c.get("url"):
                    sources.append(c["url"])
        elif b.get("type") == "server_tool_use":
            searched = True
    return {"text": text.strip(), "searched": searched, "sources": sorted(set(sources))}


if __name__ == "__main__":
    ids = {m["id"] for m in http("https://api.anthropic.com/v1/models?limit=100", None, H).get("data", [])}
    MODEL = first_available(ids, PREFERRED, "ANTHROPIC_MODEL")
    print("model:", MODEL, flush=True)
    run_all("Claude (Anthropic API)", MODEL, call)
