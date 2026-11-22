import json,re
from urllib.parse import urlparse
T=json.load(open('data/raw/claim-tags-klaviyo.json'))
raw=json.load(open('data/raw/chatgpt-klaviyo.json'))
R="Klaviyo"; G="GetResponse"; N="None"
SHOP="https://apps.shopify.com/getresponse-official"; PRICE="https://www.getresponse.com/pricing"
CL={'A':"Klaviyo integrates more deeply with Shopify",'B':"GetResponse is cheaper",'C':"Klaviyo segments better and predicts (CLV, churn)",
'D':"Klaviyo has better revenue reporting",'E':"Klaviyo's e-commerce flows go deeper",'F':"GetResponse does more beyond email",
'G':"Klaviyo has stronger SMS",'H':"GetResponse locks abandoned cart behind higher plans",'I':"GetResponse is easier to set up"}
live=lambda k: T['claude_on'][k]+T['chatgpt_on'][k]+T['gemini'][k]+T['google'][k]
train=lambda k: T['claude_off'][k]+T['chatgpt_off'][k]
rt=lambda k: T['claude_on'][k]+T['chatgpt_on'][k]+T['google'][k]

def cg(mode):
    rows=[]
    for r in sorted([x for x in raw['runs'] if x['search']==mode],key=lambda x:x['n']):
        p=re.search(r'PICK:\s*(.+)',r['text']); q=re.search(r'REASON:\s*(.+)',r['text'])
        doms=sorted({urlparse(s['url'] if isinstance(s,dict) else s).netloc.replace('www.','') for s in r.get('sources',[])})
        doms=[d for d in doms if 'cloudfront' not in d and 'ctfassets' not in d]
        rows.append([p.group(1).strip(), q.group(1).strip().rstrip('.'), ', '.join(doms) if mode=='on' else 'Search off'])
    return rows
def simple(picks,reasons={},src=lambda i:''):
    return [[picks.get(i,R),reasons.get(i,''),src(i)] for i in range(1,11)]
gem_src={1,2,4,5,6,7,8}
org1={1,2,3,7,10}
answers={
 'claude_off':{'note':"Clean Claude helper, web search off (training data only). Picks and claim tags were logged; per-answer reasons weren't. The helper once mentioned GetResponse as a client, so slight context bleed is possible.",
   'rows':simple({8:N},{},lambda i:'Search off')},
 'claude_on':{'note':"Same Claude helper with web search on. Picks and claim tags logged; per-answer reasons and sources weren't.",
   'rows':simple({5:N,8:N},{})},
 'chatgpt_off':{'note':"OpenAI API (gpt-5.2), web search off, run from GitHub Actions. Reasons are ChatGPT's own one-line summary.",'rows':cg('off')},
 'chatgpt_on':{'note':"gpt-5.2 with web search forced on. It cited getresponse.com in 9 of 10 answers and still picked Klaviyo in 9.",'rows':cg('on')},
 'gemini':{'note':"Gemini web app, logged out, US VPN. Gemini decides when to search: sources showed on 7 of 10. Picks logged; reasons only where noted.",
   'rows':simple({5:G,8:N},{5:"Answered yes: cheaper",8:"GetResponse not mentioned"},lambda i:'Shown' if i in gem_src else 'None shown')},
 'google':{'note':"Google US (gl=us, hl=en, pws=0), logged out, VPN. Pick = the AI Overview's pick; None = no pick or a split answer. Sources column shows where getresponse.com's own comparison page ranks.",
   'rows':simple({1:N,2:N,4:N,5:G,8:N,9:N,10:N},{5:"Answered yes: cheaper",8:"GetResponse not in the AI Overview"},
     lambda i:'getresponse.com ranks #1 organic' if i in org1 else '')},
}
def nopick_check():
    for k,v in answers.items(): print(k,[r[0] for r in v['rows']].count(R),[r[0] for r in v['rows']].count(G))
nopick_check()
cons=sorted('ABCDEFGHI',key=lambda k:-live(k))
d={
"rival":R,"sample":False,"collected":"22 Nov 2026","market":"US (VPN), logged out",
"headline":{"lead":"AI picks Klaviyo in 47 of 60 answers. Its revenue-reporting and automation reasons are out of date. Address these first on the comparison page.",
 "points":[
  {"text":"Klaviyo is picked in 47 of 60 answers. GetResponse wins 3, all on price or all-in-one value.","chips":["6 runs × 10 prompts","US, logged out"]},
  {"text":"“Klaviyo has better revenue reporting” comes from training data: 18 of 20 search-off answers say it, 13 of 30 live ones. GetResponse now reports revenue per message and per workflow.","chips":["Outdated","Revenue attribution"],"youChip":0},
  {"text":"Price is the main reason AI ever picks GetResponse, but it only holds at bigger lists. At 1k contacts the plan with abandoned cart costs $59 against Klaviyo's $30.","chips":["30 of 40 live answers","Partly holds"]},
  {"text":"GetResponse's own comparison page ranks #1 on Google for 5 of 10 prompts. AI Overviews still pick it once and leave it out of “Klaviyo alternatives”.","chips":["Google US","Organic vs AI Overview"]}]},
"priority":[
 {"feature":"E-commerce automation flows","need":5,"ai":f"Klaviyo deeper ({live('E')}/40)","verdict":"partly","reason":"Top store need and a widely repeated weakness. Browse abandonment and price drop campaigns are new (Apr 2026) and answers miss them. Back-in-stock is still missing, so say so."},
 {"feature":"Revenue attribution","need":4,"ai":f"Klaviyo better ({live('D')}/40)","verdict":"outdated","reason":"The clearest training-data gap: 90% of search-off answers make the claim, 43% of live ones. GetResponse now reports revenue per message and workflow (Marketer and up). Easy win."},
 {"feature":"Price by list size","need":5,"ai":f"GetResponse cheaper ({live('B')}/40)","verdict":"partly","reason":"The main reason AI picks GetResponse at all. True at 10k contacts, not at 1k on the plan stores need. Show a list-size table so the claim survives a check."},
 {"feature":"Shopify integration","need":5,"ai":f"Klaviyo deeper ({live('A')}/40)","verdict":"holds","reason":"High need, and it holds: the Shopify app has 1 review rated 1.0. Cover it honestly. This is a product fix more than a page fix."},
 {"feature":"Abandoned cart by plan","need":4,"ai":f"Locked to higher plans ({live('H')}/40)","verdict":"holds","reason":"Live search adds this objection: 4 of 20 search-off answers raise it, 10 of 30 live ones. Starter has no abandoned cart. Name the plan that does, up front."},
 {"feature":"Segmentation and predictions","need":4,"ai":f"Klaviyo stronger ({live('C')}/40)","verdict":"holds","reason":"Repeated almost everywhere and true: AI recommendations are Enterprise only; no predictive CLV or churn found. Don't contest it. Narrow it."},
 {"feature":"SMS","need":3,"ai":f"Klaviyo stronger ({live('G')}/40)","verdict":"holds","reason":"SMS is Enterprise only (MAX). Live answers raise it less than training data does (33% vs 75%), so one honest line is enough."},
 {"feature":"Ease of setup","need":3,"ai":f"GetResponse easier ({live('I')}/40)","verdict":"unclear","reason":"Few answers make it and no primary source settles it. Don't lead with it."},
 {"feature":"Beyond email (webinars, courses, sites)","need":2,"ai":f"GetResponse does more ({live('F')}/40)","verdict":"holds","reason":"Already credited and true (Creator plan). Low store need, so it goes last."}],
"scoreboard":[
 {"engine":"Claude","mode":"search off","gr":0,"rival":9,"none":1,"split":False,"note":"No pick on “Klaviyo alternatives”"},
 {"engine":"Claude","mode":"search on","gr":0,"rival":8,"none":2,"split":False,"note":"No pick on price (Q5) or alternatives (Q8)"},
 {"engine":"ChatGPT","mode":"search off · gpt-5.2","gr":0,"rival":10,"none":0,"split":False,"note":"Klaviyo in every answer"},
 {"engine":"ChatGPT","mode":"search on · gpt-5.2","gr":1,"rival":9,"none":0,"split":False,"note":"GetResponse once: all-in-one value (Q8)"},
 {"engine":"Gemini","mode":"web app · searches when it decides","gr":1,"rival":8,"none":1,"split":False,"note":"GetResponse on price (Q5); left out of alternatives (Q8)"},
 {"engine":"Google","mode":"AI Overview","gr":1,"rival":3,"none":6,"split":True,"note":"6 of 10 AI Overviews don't pick"}],
"strengths":{"gr":[{"label":"Beyond email (webinars, courses, sites)","n":live('F')},{"label":"Price","n":live('B')},{"label":"Ease of setup","n":live('I')}],
 "rival":[{"label":"Segmentation and predictions","n":live('C')},{"label":"E-commerce flows","n":live('E')},{"label":"Revenue reporting","n":live('D')},{"label":"Shopify integration","n":live('A')},{"label":"SMS","n":live('G')}]},
"engines":[["claude","Claude"],["chatgpt","ChatGPT"],["gemini","Gemini"],["google","Google"]],
"consensus":[{"claim":CL[k],"counts":{"claude":T['claude_on'][k],"chatgpt":T['chatgpt_on'][k],"gemini":T['gemini'][k],"google":T['google'][k]}} for k in cons],
"prompts":["Which is better for an online store, GetResponse or Klaviyo?","Which is better for an online store, Klaviyo or GetResponse?","GetResponse vs Klaviyo for Shopify","Best email marketing for a small ecommerce store: GetResponse or Klaviyo?","Is GetResponse cheaper than Klaviyo?","GetResponse vs Klaviyo for abandoned cart emails","GetResponse vs Klaviyo automation","Klaviyo alternatives for ecommerce","GetResponse vs Klaviyo pros and cons","Should I switch from Klaviyo to GetResponse?"],
"tabs":[["claude_off","Claude · off"],["claude_on","Claude · on"],["chatgpt_off","ChatGPT · off"],["chatgpt_on","ChatGPT · on"],["gemini","Gemini"],["google","Google"]],
"answers":answers,
"retest":[
 {"claim":CL['D'],"k":"D","check":"Revenue per message and per workflow, on Marketer and up (updated 15 Apr 2026).","url":"https://www.getresponse.com/blog/email-revenue-attribution","verdict":"outdated"},
 {"claim":CL['E'],"k":"E","check":"Abandoned cart, browse abandonment (“products your shoppers considered”) and price drop campaigns exist (Apr 2026). No back-in-stock found.","url":"https://www.getresponse.com/blog/price-drop-email","verdict":"partly"},
 {"claim":CL['B'],"k":"B","check":"Marketer, the first plan with abandoned cart: $59/mo at 1k vs Klaviyo $30. At 10k: €99 vs Klaviyo $150. Klaviyo prices are from third-party sources.","url":PRICE,"verdict":"partly"},
 {"claim":CL['A'],"k":"A","check":"GetResponse's Shopify app: 1 review, rated 1.0.","url":SHOP,"verdict":"holds"},
 {"claim":CL['H'],"k":"H","check":"Starter has no abandoned cart; it starts at Marketer.","url":PRICE,"verdict":"holds"},
 {"claim":CL['C'],"k":"C","check":"AI recommendations are Enterprise only. No predictive CLV or churn found.","url":PRICE,"verdict":"holds"},
 {"claim":CL['G'],"k":"G","check":"SMS only in GetResponse MAX (Enterprise, from $1,099/mo per the Shopify listing).","url":SHOP,"verdict":"holds"},
 {"claim":CL['F'],"k":"F","check":"Creator plan includes webinars, courses and a website builder.","url":PRICE,"verdict":"holds"},
 {"claim":CL['I'],"k":"I","check":"No primary source settles it.","url":"","verdict":"unclear"}],
"gapNote":"Live search barely moves the pick: Klaviyo 19 of 20 with search off, 17 of 20 with it on (Claude and ChatGPT). ChatGPT cited getresponse.com in 9 of 10 live answers and still credited Klaviyo with better revenue attribution. The page needs plain, dated statements on revenue attribution and the new flows, so live engines have something to quote.",
"how":["10 fixed prompts, the same for every engine, asked from the US (VPN), logged out. Prompts 1 and 2 swap the name order; every engine answered the same both ways.",
 "Claude: a clean helper, search off then on. ChatGPT: OpenAI API (gpt-5.2), search off then forced on.",
 "Gemini: web app. It decides when to search, so it counts as live only. Google: the AI Overview, plus where getresponse.com ranks.",
 "Training data = Claude + ChatGPT with search off (20 answers). Live = Claude + ChatGPT with search on, plus Google (30). Gemini is left out of this table.",
 "Claims are tagged per answer. ChatGPT tags are keyword matches, so allow ±1–2 per claim.",
 "Primary sources = GetResponse's pricing page, blog, help docs and Shopify listing. Klaviyo prices come from third-party sources.",
 "Not covered yet: logged-in runs, non-US results, Perplexity and Copilot."]}
for x in d['retest']:
    k=x.pop('k'); x.update(train=train(k),trainOf=20,live=rt(k),liveOf=30)
json.dump(d,open('docs/data/klaviyo.json','w'),ensure_ascii=False,indent=1)
print('ok')
