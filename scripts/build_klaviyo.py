"""Build docs/data/klaviyo.json from data/raw/* (answers + claim tags) and the primary-source checks below.

Engines: Claude and ChatGPT via API (search off/on), Google AI Overview (browser), Gemini (earlier app run
until the API run is billed). Editorial text (priority reasons, headline) is written here and uses the counts.
"""
import json, re, os
from urllib.parse import urlparse
R = "Klaviyo"; G = "GetResponse"; N = "None"
raw = lambda e: json.load(open(f"data/raw/{e}-klaviyo.json")) if os.path.exists(f"data/raw/{e}-klaviyo.json") else None
T = json.load(open("data/raw/claim-tags-klaviyo.json"))
gem_api = raw("gemini")

def cnt(key, L):
    if key == "gemini": key = "gemini_on"
    return sum(L in s for s in T.get(key, {}).values())
LIVE4 = ["claude_on", "chatgpt_on", "gemini_on", "google_on"]
train = lambda L: cnt("claude_off", L) + cnt("chatgpt_off", L) + cnt("gemini_off", L)
live30 = lambda L: live40(L)
live40 = lambda L: sum(cnt(k, L) for k in LIVE4)

def rows(e, mode):
    d = raw(e); out = []
    for r in sorted([x for x in d["runs"] if x["search"] == mode], key=lambda x: x["n"]):
        p = re.search(r"PICK:\s*\**\s*([A-Za-z]+)", r["text"]); q = re.search(r"REASON:\s*\**\s*([^\n]+)", r["text"])
        pick = p.group(1) if p else N
        if e == "google": src = "Organic top 3: " + r.get("organic_top3", "")
        elif mode == "off": src = "Search off"
        elif e == "gemini":
            src = ", ".join(r["sources"]) or "Didn't search"
        else:
            doms = sorted({urlparse(u).netloc.replace("www.", "") for u in r["sources"]} - {""})
            doms = [x for x in doms if "cloudfront" not in x and "ctfassets" not in x]
            src = ", ".join(doms) or "None cited"
        out.append([pick, q.group(1).strip().rstrip(".") if q else "", src])
    return out

def tally(rs): return {k: sum(r[0] == k for r in rs) for k in (G, R, N)}

ans = {"claude_off": rows("claude", "off"), "claude_on": rows("claude", "on"),
       "chatgpt_off": rows("chatgpt", "off"), "chatgpt_on": rows("chatgpt", "on"), "google": rows("google", "on")}
ans["gemini_off"] = rows("gemini", "off"); ans["gemini_on"] = rows("gemini", "on")
_unused = [[N if i == 8 else G if i == 5 else R,
    {5: "Answered yes: cheaper", 8: "GetResponse not mentioned"}.get(i, ""), "Shown" if i in {1, 2, 4, 5, 6, 7, 8} else "None shown"] for i in range(1, 11)]
P = {k: tally(v) for k, v in ans.items()}
allp = {k: sum(P[e][k] for e in P) for k in (G, R, N)}; TOTAL = sum(allp.values())
cite_gr = lambda e: sum(any("getresponse.com" in u for u in r["sources"]) for r in raw(e)["runs"] if r["search"] == "on")
attr = lambda e, m: sum(bool(re.search("attribut", r[1], re.I)) for r in rows(e, m))
cl_model = raw("claude")["model"]; gm_model = raw("gemini")["model"]; gm_searched = sum(r["searched"] for r in raw("gemini")["runs"] if r["search"] == "on"); cg_model = raw("chatgpt")["model"]

CL = {"A": "Klaviyo integrates more deeply with Shopify", "B": "GetResponse is cheaper", "C": "Klaviyo segments better and predicts (CLV, churn)",
      "D": "Klaviyo has better revenue reporting", "E": "Klaviyo's e-commerce flows go deeper", "F": "GetResponse does more beyond email",
      "G": "Klaviyo has stronger SMS", "H": "GetResponse locks abandoned cart behind higher plans", "I": "GetResponse is easier to set up"}
SHOP = "https://apps.shopify.com/getresponse-official"; PRICE = "https://www.getresponse.com/pricing"
pct = lambda a, b: round(a / b * 100)

d = {
"rival": R, "sample": False, "collected": "22 Nov 2026", "market": "US (VPN), logged out",
"headline": {"lead": f"AI picks Klaviyo in {allp[R]} of {TOTAL} answers. Its main live reason, revenue attribution, is out of date. Address it first on the comparison page.",
 "points": [
  {"text": f"Klaviyo is picked in {allp[R]} of {TOTAL} answers. GetResponse wins {allp[G]}, all on price or all-in-one value.", "chips": ["7 runs × 10 prompts", "US, logged out"]},
  {"text": f"Live search doesn't correct the revenue-reporting claim: {pct(train('D'),30)}% of search-off answers make it, {pct(live30('D'),40)}% of live ones. GetResponse now reports revenue per message and per workflow.", "chips": ["Outdated", "Revenue attribution"], "youChip": 0},
  {"text": "Price is the main reason AI ever picks GetResponse, but it only holds at bigger lists. At 1k contacts the plan with abandoned cart costs $59 against Klaviyo's $30.", "chips": [f"{live40('B')} of 40 live answers", "Partly holds"]}]},
"priority": [
 {"feature": "Revenue attribution", "need": 4, "ai": f"Klaviyo better ({live40('D')}/40)", "verdict": "outdated",
  "reason": f"Outdated, and search doesn't fix it: {pct(train('D'),30)}% of search-off and {pct(live30('D'),40)}% of live answers make the claim, and Claude gives it as its stated reason in {attr('claude','on')} of 10 live answers. GetResponse reports revenue per message and workflow (Marketer and up). It's the clearest fix we can prove."},
 {"feature": "E-commerce automation flows", "need": 5, "ai": f"Klaviyo deeper ({live40('E')}/40)", "verdict": "partly",
  "reason": "Top store need and repeated almost everywhere. Browse abandonment and price drop campaigns are new (Apr 2026) and answers miss them. Back-in-stock is still missing, so say so."},
 {"feature": "Price by list size", "need": 5, "ai": f"GetResponse cheaper ({live40('B')}/40)", "verdict": "partly",
  "reason": "The main reason AI picks GetResponse at all. True at 10k contacts, not at 1k on the plan stores need. Show a list-size table by plan so the claim survives a check."},
 {"feature": "Shopify integration", "need": 5, "ai": f"Klaviyo deeper ({live40('A')}/40)", "verdict": "holds",
  "reason": "High need, and it holds: the Shopify app has 1 review rated 1.0. Cover it honestly. This is a product fix more than a page fix."},
 {"feature": "Abandoned cart by plan", "need": 4, "ai": f"Locked to higher plans ({live40('H')}/40)", "verdict": "holds",
  "reason": f"Live search adds this objection: {train('H')} of 30 search-off answers raise it, {live30('H')} of 40 live ones. Starter has no abandoned cart. Name the plan that does, up front."},
 {"feature": "Segmentation and predictions", "need": 4, "ai": f"Klaviyo stronger ({live40('C')}/40)", "verdict": "holds",
  "reason": "Repeated almost everywhere and true: AI recommendations are Enterprise only; no predictive CLV or churn found. Don't contest it. Narrow it."},
 {"feature": "Ease of setup", "need": 3, "ai": f"GetResponse easier ({live40('I')}/40)", "verdict": "unclear",
  "reason": "Google's AI Overviews credit it more than the chatbots do. No primary source settles it. Don't lead with it."},
 {"feature": "SMS", "need": 3, "ai": f"Klaviyo stronger ({live40('G')}/40)", "verdict": "holds",
  "reason": "SMS is Enterprise only (MAX), but few answers raise it. One honest line is enough."},
 {"feature": "Beyond email (webinars, courses, sites)", "need": 2, "ai": f"GetResponse does more ({live40('F')}/40)", "verdict": "holds",
  "reason": "Already credited and true (Creator plan). Low store need, so it goes last."}],
"scoreboard": [
 {"engine": "Claude", "mode": f"search off · {cl_model}", "gr": P["claude_off"][G], "rival": P["claude_off"][R], "none": P["claude_off"][N], "split": False, "note": "Klaviyo in every answer"},
 {"engine": "Claude", "mode": f"search on · {cl_model}", "gr": P["claude_on"][G], "rival": P["claude_on"][R], "none": P["claude_on"][N], "split": False, "note": "Q8 suggests Omnisend, not GetResponse"},
 {"engine": "ChatGPT", "mode": f"search off · {cg_model}", "gr": P["chatgpt_off"][G], "rival": P["chatgpt_off"][R], "none": P["chatgpt_off"][N], "split": False, "note": "Klaviyo in every answer"},
 {"engine": "ChatGPT", "mode": f"search on · {cg_model}", "gr": P["chatgpt_on"][G], "rival": P["chatgpt_on"][R], "none": P["chatgpt_on"][N], "split": False, "note": "GetResponse once: all-in-one value (Q8)"},
 {"engine": "Gemini", "mode": f"search off · {gm_model}", "gr": P["gemini_off"][G], "rival": P["gemini_off"][R], "none": P["gemini_off"][N], "split": False, "note": "Klaviyo in every answer"},
 {"engine": "Gemini", "mode": f"search on · {gm_model}", "gr": P["gemini_on"][G], "rival": P["gemini_on"][R], "none": P["gemini_on"][N], "split": False, "note": f"Klaviyo in every answer; searched {gm_searched} of 10"},
 {"engine": "Google", "mode": "AI Overview", "gr": P["google"][G], "rival": P["google"][R], "none": P["google"][N], "split": False, "note": f"{P['google'][N]} of 10 don't pick; GetResponse missing from alternatives"}],
"strengths": {"gr": [{"label": "Beyond email (webinars, courses, sites)", "n": live40("F")}, {"label": "Price", "n": live40("B")}, {"label": "Ease of setup", "n": live40("I")}],
 "rival": sorted([{"label": "Segmentation and predictions", "n": live40("C")}, {"label": "E-commerce flows", "n": live40("E")}, {"label": "Shopify integration", "n": live40("A")},
                  {"label": "Revenue reporting", "n": live40("D")}, {"label": "SMS", "n": live40("G")}], key=lambda x: -x["n"])},
"engines": [["claude", "Claude"], ["chatgpt", "ChatGPT"], ["gemini", "Gemini"], ["google", "Google"]],
"consensus": [{"claim": CL[L], "counts": {"claude": cnt("claude_on", L), "chatgpt": cnt("chatgpt_on", L), "gemini": cnt("gemini_on", L), "google": cnt("google_on", L)}}
              for L in sorted("ABCDEFGHI", key=lambda L: -live40(L))],
"prompts": [r["prompt"] for r in raw("claude")["runs"] if r["search"] == "off"],
"tabs": [["claude_off", "Claude · off"], ["claude_on", "Claude · on"], ["chatgpt_off", "ChatGPT · off"], ["chatgpt_on", "ChatGPT · on"], ["gemini_off", "Gemini · off"], ["gemini_on", "Gemini · on"], ["google", "Google"]],
"answers": {
 "claude_off": {"note": f"Anthropic API ({cl_model}), web search off. No system prompt, no account context. Reasons are Claude's own one-line summary.", "rows": ans["claude_off"]},
 "claude_on": {"note": f"Same model with web search on (US). It cited getresponse.com in {cite_gr('claude')} of 10 answers.", "rows": ans["claude_on"]},
 "chatgpt_off": {"note": f"OpenAI API ({cg_model}), web search off.", "rows": ans["chatgpt_off"]},
 "chatgpt_on": {"note": f"Web search forced on. It cited getresponse.com in {cite_gr('chatgpt')} of 10 answers and still picked Klaviyo in {P['chatgpt_on'][R]}.", "rows": ans["chatgpt_on"]},
 "gemini_off": {"note": f"Gemini API ({gm_model}), no search tool.", "rows": ans["gemini_off"]},
 "gemini_on": {"note": f"Google Search grounding on, plus one line asking it to check Google first (the API can't force a search). It searched on {gm_searched} of 10 and cited getresponse.com in {sum(any('getresponse' in u for u in r['sources']) for r in raw('gemini')['runs'] if r['search'] == 'on')}.", "rows": ans["gemini_on"]},
 "google": {"note": "Google US (gl=us, hl=en, pws=0), logged out, VPN. Pick judged by Launch Space: a named winner for the store case counts; split by store stage, pros/cons only or 'depends' = None.", "rows": ans["google"]}},
"retest": [
 dict(claim=CL["D"], L="D", check="Revenue per message and per workflow, on Marketer and up (updated 15 Apr 2026).", url="https://www.getresponse.com/blog/email-revenue-attribution", verdict="outdated"),
 dict(claim=CL["E"], L="E", check="Abandoned cart, browse abandonment (“products your shoppers considered”) and price drop campaigns exist (Apr 2026). No back-in-stock found.", url="https://www.getresponse.com/blog/price-drop-email", verdict="partly"),
 dict(claim=CL["B"], L="B", check="Marketer, the first plan with abandoned cart: $59/mo at 1k vs Klaviyo $30. At 10k: €99 vs Klaviyo $150. Klaviyo prices are from third-party sources.", url=PRICE, verdict="partly"),
 dict(claim=CL["H"], L="H", check="Starter has no abandoned cart; it starts at Marketer.", url=PRICE, verdict="holds"),
 dict(claim=CL["A"], L="A", check="GetResponse's Shopify app: 1 review, rated 1.0.", url=SHOP, verdict="holds"),
 dict(claim=CL["C"], L="C", check="AI recommendations are Enterprise only. No predictive CLV or churn found.", url=PRICE, verdict="holds"),
 dict(claim=CL["G"], L="G", check="SMS only in GetResponse MAX (Enterprise, from $1,099/mo per the Shopify listing).", url=SHOP, verdict="holds"),
 dict(claim=CL["F"], L="F", check="Creator plan includes webinars, courses and a website builder.", url=PRICE, verdict="holds"),
 dict(claim=CL["I"], L="I", check="No primary source settles it.", url="", verdict="unclear")],
"gapNote": (f"Live search barely changes what AI says: the claims AI makes are about as common with search on as off. Claude with search on cited getresponse.com in {cite_gr('claude')} of 10 answers, Gemini in {sum(any('getresponse' in u for u in r['sources']) for r in raw('gemini')['runs'] if r['search'] == 'on')}. "
            f"ChatGPT cited it in {cite_gr('chatgpt')} of 10 and still credited Klaviyo with better attribution. Google quotes GetResponse's own comparison page for price "
            "($15/mo, $65 at 10k), which looks like Starter pricing, the plan without abandoned cart. Check that page's figures, and state revenue attribution and the new flows in plain, dated lines so live engines have something to quote."),
"how": ["10 fixed prompts, the same for every engine, asked as US, logged out. Prompts 1 and 2 swap the name order.",
        f"Claude: Anthropic API ({cl_model}), search off then on. ChatGPT: OpenAI API ({cg_model}), search off then forced on. No account context or memory.",
        f"Gemini: API ({gm_model}), no search then Google Search grounding; it chose to search on {gm_searched} of 10. Google: the AI Overview in a logged-out browser on a US VPN, plus the top 3 organic results.",
        "Training data = Claude, ChatGPT and Gemini with search off (30 answers). Live = the same three with search on, plus Google (40).",
        "Claims are tagged by one Claude classifier across all 70 answers.",
        "Primary sources = GetResponse's pricing page, blog, help docs and Shopify listing. Klaviyo prices come from third-party sources.",
        "Not covered yet: logged-in runs, non-US results, Perplexity and Copilot."]}
for x in d["retest"]:
    L = x.pop("L"); x.update(train=train(L), trainOf=30, live=live30(L), liveOf=40)
json.dump(d, open("docs/data/klaviyo.json", "w"), ensure_ascii=False, indent=1)
print("picks", allp, {k: v for k, v in P.items()})
