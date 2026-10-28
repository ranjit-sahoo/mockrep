"""Builds app/static/practice-pack.json: the Practice Sessions content (role -> questions with model answers).

Sources (all original or the owner's own content):
- app/bank.py (role questions with a how-to-answer hint) and app/basic_in_data.py (the owner's interview Q&A)
- scripts/answers/a*.txt  model answers for the professional-role questions (numbered in bank order)
- scripts/answers/b1.txt  sample answers for basic-level questions that only had guidance
- scripts/answers/general.txt  answers for the seven common questions
Run: python scripts/build_practice_pack.py   (tests fail if the committed pack is stale)
"""
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app import bank  # noqa: E402

OUT = os.path.join(ROOT, "app", "static", "practice-pack.json")
AD = os.path.join(ROOT, "scripts", "answers")

GROUPS = [
    ("it", "IT and Tech", "Software, data, cloud and testing jobs"),
    ("biz", "Business, Finance and Management", "Analyst, sales, HR, accounts, banking, project roles"),
    ("svc", "Hotel, Airline, BPO and Office", "Hotel, cabin crew, airport, call centre, data entry"),
]
ROLE_META = {
    "QA Automation Engineer": ("it", "Testing, Selenium, Playwright, API tests", "qa tester testing selenium playwright automation sdet quality"),
    "Java Developer": ("it", "Core Java, Spring Boot, microservices", "java spring boot backend developer"),
    "Python Developer": ("it", "Python, FastAPI, Django, scripting", "python django fastapi flask backend developer"),
    "Business Analyst": ("biz", "Requirements, user stories, stakeholders", "ba business analyst requirements product analyst"),
    "Data Analyst": ("it", "SQL, Excel, Power BI, dashboards", "data analyst sql excel power bi tableau analytics mis"),
    "DevOps Engineer": ("it", "CI/CD, Docker, Kubernetes, Terraform", "devops docker kubernetes terraform sre ci cd"),
    "Frontend Developer": ("it", "JavaScript, React, CSS, performance", "frontend front end react javascript web developer ui"),
    "Project Manager": ("biz", "Planning, risk, agile, stakeholders", "project manager pm program manager delivery"),
    "Data Engineer": ("it", "Pipelines, Spark, warehouses, quality", "data engineer etl spark pipeline warehouse big data"),
    ".NET Developer": ("it", "C#, ASP.NET, Entity Framework", "dotnet net c# asp.net developer"),
    "Full Stack Developer": ("it", "Front end, back end, APIs, databases", "full stack fullstack mern web developer"),
    "Salesforce Developer": ("it", "Apex, LWC, Flow, integrations", "salesforce sfdc apex lwc admin developer crm"),
    "ServiceNow Developer": ("it", "ITSM, Flow Designer, ACLs, integrations", "servicenow snow itsm developer"),
    "AWS Cloud Engineer": ("it", "AWS, IAM, VPC, high availability", "aws cloud engineer amazon web services architect"),
    "Cybersecurity Analyst": ("it", "SOC, SIEM, incident response", "cyber security cybersecurity soc analyst infosec"),
    "Scrum Master": ("biz", "Scrum, agile coaching, retrospectives", "scrum master agile coach"),
    "Network Engineer": ("it", "Routing, switching, firewalls, VPN", "network engineer ccna routing switching networking"),
    "Machine Learning Engineer": ("it", "Models in production, MLOps, LLMs", "machine learning ml engineer mlops ai llm"),
    "Data Scientist": ("it", "Statistics, modelling, A/B tests", "data science data scientist statistics ml analytics"),
    "SAP Consultant": ("biz", "SAP modules, S/4HANA, implementation", "sap consultant fico mm sd abap hana"),
    "Sales / Business Development Executive": ("biz", "Selling, objections, targets", "sales business development bde executive marketing telecaller"),
    "Digital Marketing Executive": ("biz", "SEO, ads, social media, analytics", "digital marketing seo sem social media executive"),
    "HR Executive": ("biz", "Recruitment, payroll basics, employee relations", "hr human resources recruiter hr executive talent"),
    "PHP Developer": ("it", "PHP, Laravel, MySQL, security", "php laravel mysql wordpress developer"),
    "Android Developer": ("it", "Kotlin, MVVM, Room, Play Store", "android kotlin app developer mobile"),
    "UI/UX Designer": ("biz", "Design process, research, Figma", "ui ux designer figma product designer graphic"),
    "Banking Operations": ("biz", "KYC, accounts, payments, loans", "bank banking operations clerk po kyc loan"),
    "Accountant (Tally)": ("biz", "Tally, GST, TDS, reconciliation", "accountant accounts tally gst tds finance bookkeeping"),
    "BPO / Call Centre": ("svc", "Voice and non-voice, customer care", "bpo call centre call center customer support customer care telecaller voice process"),
    "Cabin Crew / Air Hostess": ("svc", "Safety, service, grooming, scenarios", "cabin crew air hostess flight attendant airline steward"),
    "Hotel & Hospitality": ("svc", "Front desk, housekeeping, F&B, guest service", "hotel hospitality receptionist front desk front office housekeeping waiter restaurant f&b guest relations concierge"),
    "Airport Ground Staff": ("svc", "Check-in, boarding, baggage, passengers", "airport ground staff check in boarding baggage airline counter"),
    "Data Entry / Back Office": ("svc", "Typing, accuracy, Excel, back office", "data entry back office typing operator mis executive"),
}


TEXT_FIXES = {"What is your long-term": "What is your long-term goal?"}  # truncated in the owner's source set


def _read_numbered(pattern):
    d = {}
    for f in sorted(glob.glob(os.path.join(AD, pattern))):
        for line in open(f, encoding="utf-8"):
            if line.strip():
                n, t = line.split("|", 1)
                assert int(n) not in d, f"duplicate answer number {n}"
                d[int(n)] = t.strip()
    return d


def _qid(text):
    return "q" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def _split_hint(hint):
    """Basic-level hints look like: 'Sample answer: X Tip: Y Hindi: Z' or 'Guidance Hindi: Z'."""
    hi = ""
    if " Hindi: " in hint:
        hint, hi = hint.split(" Hindi: ", 1)
    elif hint.startswith("Hindi: "):
        hint, hi = "", hint[7:]
    tip = ""
    if " Tip: " in hint:
        hint, tip = hint.split(" Tip: ", 1)
    sample = ""
    if hint.startswith("Sample answer: "):
        sample, hint = hint[len("Sample answer: "):], ""
    return sample.strip(), (tip or hint).strip(), hi.strip()


def build():
    prof = _read_numbered("a*.txt")
    basic = _read_numbered("b*.txt")
    general = {}
    for line in open(os.path.join(AD, "general.txt"), encoding="utf-8"):
        if line.strip():
            q, a = line.split("|", 1)
            general[q.strip()] = a.strip()
    gen_q = {g[2] for g in bank.GENERAL}
    assert set(general) == gen_q, "general answers must cover bank.GENERAL exactly"
    names = bank.roles()
    qs, roles, seen_p, seen_b = {}, [], {}, {}
    pn = bn = 0
    for name in names:
        group, blurb, keys = ROLE_META[name]
        ids = []
        is_basic = group == "svc"
        for q in bank.curated(name)["questions"]:
            text, hint = q["question"], q["hint"]
            text = TEXT_FIXES.get(text, text)
            if text in gen_q:
                a, look, hi = general[text], hint, ""
                if hint.startswith("Sample answer") or "Hindi:" in hint:
                    s, t, hi = _split_hint(hint)
                    if s:
                        a, look = s, t
                    else:
                        look = t or hint
            elif is_basic:
                s, t, hi = _split_hint(hint)
                if s:
                    a, look = s, t
                else:
                    if text not in seen_b:
                        bn += 1
                        seen_b[text] = basic[bn]
                    a, look = seen_b[text], t
            else:
                if text not in seen_p:
                    pn += 1
                    seen_p[text] = prof[pn]
                a, look, hi = seen_p[text], hint, ""
            rec = {"q": text, "t": q["type"], "l": q["level"], "a": a}
            if look:
                rec["w"] = look
            if hi:
                rec["h"] = hi
            qid = _qid(text + "|" + a)
            if qid in qs:
                # same question can carry a richer own-role answer; keep the first, they match by design
                pass
            else:
                qs[qid] = rec
            ids.append(qid)
        roles.append({"id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"), "name": name, "group": group,
                      "blurb": blurb, "keys": keys, "qs": ids})
    assert pn == len(prof), f"unused professional answers: {pn} used of {len(prof)}"
    assert bn == len(basic), f"unused basic answers: {bn} used of {len(basic)}"
    return {"version": 1, "groups": [{"id": i, "name": n, "blurb": b} for i, n, b in GROUPS], "roles": roles, "qs": qs}


def main():
    pack = build()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    print("roles", len(pack["roles"]), "unique questions", len(pack["qs"]), "bytes", os.path.getsize(OUT))


if __name__ == "__main__":
    main()
