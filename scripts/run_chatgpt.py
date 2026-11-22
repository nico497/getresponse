"""Run the 10 prompts on ChatGPT (OpenAI API), web search off and on.

Needs OPENAI_API_KEY (GitHub secret). Optional OPENAI_MODEL (GitHub variable).
Writes data/raw/chatgpt-<rival>.json.
"""
import os
from common import http, first_available, run_all

H = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
PREFERRED = ["gpt-5.2", "gpt-5.1", "gpt-5", "gpt-4.1", "gpt-4o"]


def call(prompt, search):
    body = {"model": MODEL, "input": prompt}
    if search:
        body["tools"] = [{"type": "web_search"}]
        body["tool_choice"] = "required"
    data = http("https://api.openai.com/v1/responses", body, H)
    text, sources = "", []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")
                    sources += [a["url"] for a in c.get("annotations") or [] if a.get("type") == "url_citation" and a.get("url")]
    searched = any(i.get("type") == "web_search_call" for i in data.get("output", []))
    return {"text": text.strip(), "searched": searched, "sources": sorted(set(sources))}


if __name__ == "__main__":
    ids = {m["id"] for m in http("https://api.openai.com/v1/models", None, H).get("data", [])}
    MODEL = first_available(ids, PREFERRED, "OPENAI_MODEL")
    print("model:", MODEL, flush=True)
    run_all("ChatGPT (OpenAI API)", MODEL, call)
