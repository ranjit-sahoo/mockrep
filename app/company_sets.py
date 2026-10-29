"""Curated company-wise interview question sets (instant, no AI call).

These are commonly reported interview THEMES for each company, written by
MockRep. They are not leaked or confidential questions. Keys match the
canonical names in companies.py so a profile lookup can attach the set.
"""

_NOTE = "Commonly reported themes for {name} interviews, written by MockRep. Not leaked questions."

# (type, level, question, one-line hint)
_SETS: dict[str, list[tuple[str, str, str, str]]] = {
    "TCS": [
        ("behavioral", "easy", "Tell me about yourself and why you want to join TCS.", "60-90 seconds: education, key skills, one project, and a genuine reason tied to TCS's scale and learning."),
        ("technical", "easy", "Explain OOPS concepts (encapsulation, inheritance, polymorphism, abstraction) with a small example each.", "Define each in one line, then a tiny code or real-life example."),
        ("technical", "medium", "Write or explain a program to reverse a string or check a palindrome.", "Talk through your approach before coding; mention edge cases like empty string."),
        ("technical", "medium", "What is the difference between an array and a linked list? When would you use each?", "Memory layout, access time, insert/delete cost - then one use case each."),
        ("scenario", "medium", "Your project deadline moved up by a week. What do you do?", "Re-prioritize scope, inform the lead early, propose what can ship - no silent slipping."),
        ("behavioral", "medium", "Are you comfortable with relocation or night shifts?", "Answer honestly; if yes, say so clearly. If conditional, state your condition politely."),
        ("behavioral", "medium", "Tell me about a time you learned a new technology quickly for a project.", "STAR: what you learned, how (docs, small prototype), and the result."),
    ],
    "Infosys": [
        ("behavioral", "easy", "Introduce yourself and tell us why Infosys.", "Keep it structured: background, strengths, one achievement, why their training and projects appeal to you."),
        ("technical", "easy", "What is the difference between a compiler and an interpreter?", "One line each, plus one language example for each."),
        ("technical", "medium", "Explain pseudo-code logic: how would you find the second largest number in an array?", "Infosys loves pseudo-code rounds. Narrate the loop clearly; handle duplicates."),
        ("technical", "medium", "What are joins in SQL? Explain inner vs left join with an example.", "Small two-table example, say what rows survive in each."),
        ("scenario", "medium", "A teammate's code breaks your module right before a demo. What do you do?", "Stay factual: reproduce, isolate, pair-fix or roll back, then prevent with tests."),
        ("behavioral", "medium", "Tell me about your final year project and your exact contribution.", "Be specific about YOUR part, the tech stack, and one problem you solved."),
        ("behavioral", "medium", "Describe a situation where you disagreed with a teammate.", "Show listening, data-backed discussion, and a professional outcome."),
    ],
    "Wipro": [
        ("behavioral", "easy", "Tell me about yourself and your family background.", "Brief and professional - then steer to your skills and goals."),
        ("technical", "easy", "What is the difference between C and Java (or any two languages you know)?", "Pick 3 clear contrasts: memory management, platform, paradigm."),
        ("technical", "medium", "Explain normalization in databases with an example.", "1NF-3NF in plain words with a small table example."),
        ("technical", "medium", "Write a program to find duplicates in an array or count vowels in a string.", "Explain the approach first; mention time complexity in one line."),
        ("scenario", "medium", "You are given a task with unclear requirements. What do you do?", "Ask clarifying questions, write down assumptions, confirm before building."),
        ("behavioral", "medium", "Tell me about a time you handled multiple tasks at once.", "Show prioritization method and that nothing dropped."),
        ("behavioral", "medium", "Where do you see yourself in three years?", "Growth within the company: deeper skills, more ownership - realistic, not title-chasing."),
    ],
    "HCLTech": [
        ("behavioral", "easy", "Walk me through your resume.", "Chronological, 90 seconds, pause for them to pick what to dig into."),
        ("technical", "easy", "What are the features of the language you are most comfortable with?", "Pick one language, 4-5 features with one-line examples."),
        ("technical", "medium", "Explain the difference between process and thread.", "Memory, overhead, communication - one real example of each."),
        ("technical", "medium", "How do you reverse a linked list or find its middle element?", "Two-pointer or iterative approach; draw it in words before code."),
        ("scenario", "medium", "Production is down and you cannot find the cause. Walk me through your next hour.", "Stabilize first (rollback/restart), then logs, isolate, escalate with facts."),
        ("behavioral", "medium", "Tell me about a time you got critical feedback. What did you change?", "Name the feedback honestly and the concrete change you made."),
        ("behavioral", "medium", "How do you keep your technical skills up to date?", "Name real sources and one thing you learned recently."),
    ],
    "Tech Mahindra": [
        ("behavioral", "easy", "Tell me something that is not on your resume.", "One genuine interest or achievement that shows character, keep it short."),
        ("technical", "easy", "What is cloud computing? Name the service models.", "IaaS/PaaS/SaaS with one example each."),
        ("technical", "medium", "Explain REST APIs. What are GET, POST, PUT, DELETE for?", "One line per verb plus idempotency in one line."),
        ("technical", "medium", "What is the difference between TCP and UDP?", "Reliability vs speed, one use case each."),
        ("scenario", "medium", "A client asks for a change that will break an existing feature. How do you respond?", "Explain impact with facts, offer options, let the client decide - stay helpful."),
        ("behavioral", "medium", "Describe a time you worked under a tight deadline.", "STAR with what you cut, what you protected, and the outcome."),
        ("behavioral", "medium", "Why should we hire you over other freshers?", "Two concrete strengths with evidence, plus eagerness to learn - no arrogance."),
    ],
    "Cognizant (India)": [
        ("behavioral", "easy", "Tell me about yourself and your strengths.", "Two strengths, each backed by a one-line example."),
        ("technical", "easy", "What is the difference between == and equals() in Java (or similar in your language)?", "Reference vs value comparison with a tiny example."),
        ("technical", "medium", "Explain exception handling. When would you create a custom exception?", "try/catch/finally in one line each; custom exception for domain errors."),
        ("technical", "medium", "Write a query to find the second highest salary from an Employee table.", "Classic GenC question - LIMIT/OFFSET or subquery; explain it aloud."),
        ("scenario", "medium", "You finish your work early regularly. What do you do with the time?", "Help teammates, learn, improve tests/docs - show initiative without judging others."),
        ("behavioral", "medium", "Tell me about a conflict in a team project and how you resolved it.", "Focus on the resolution steps, not the blame."),
        ("behavioral", "medium", "Are you open to working in a different technology than you trained in?", "Yes-with-reason: fundamentals transfer; give one example of switching."),
    ],
    "Cognizant (US)": [
        ("behavioral", "easy", "Tell me about yourself and your most recent project.", "Result-first: what it does, your role, one measurable outcome."),
        ("technical", "medium", "Explain the difference between an abstract class and an interface.", "One line each plus when you would pick which."),
        ("technical", "medium", "How would you design a simple rate limiter or URL shortener?", "Clarify scale, sketch components, explain one trade-off."),
        ("technical", "medium", "SQL: find customers with no orders.", "LEFT JOIN ... IS NULL or NOT EXISTS; say why."),
        ("scenario", "medium", "A production bug appears only for one client. How do you investigate?", "Reproduce with their config/data, add logging, compare environments, fix and add a regression test."),
        ("behavioral", "medium", "Tell me about a time you had to learn something outside your comfort zone.", "STAR: what, how you ramped, and how fast you contributed."),
        ("behavioral", "medium", "How do you handle working with a distributed team across time zones?", "Async-first communication, overlap hours, clear handoffs."),
    ],
    "Capgemini": [
        ("behavioral", "easy", "Introduce yourself in one minute.", "Practice a tight 60-second version: who, skills, project, goal."),
        ("technical", "easy", "What is the difference between a list, tuple, and dictionary (Python) or similar collections?", "Mutability and use case for each."),
        ("technical", "medium", "Explain the software development life cycle and where testing fits.", "Phases in order; testing is continuous, not a single phase."),
        ("technical", "medium", "Write a program to swap two numbers or find factorial.", "Explain the logic first; mention iterative vs recursive briefly."),
        ("scenario", "medium", "You realize you misunderstood a requirement after finishing the work. What now?", "Own it early, quantify rework, confirm correct requirement, prevent with written confirmation next time."),
        ("behavioral", "medium", "Tell me about a time you helped a struggling teammate.", "Show patience and a concrete outcome; no superiority."),
        ("behavioral", "medium", "What do you know about Capgemini?", "One or two real facts (services, clients, values) - do not recite the website."),
    ],
    "Accenture": [
        ("behavioral", "easy", "Tell me about yourself and why Accenture.", "Tie your answer to their variety of clients and learning; be specific."),
        ("technical", "easy", "What is the difference between overloading and overriding?", "Compile-time vs runtime, one small example each."),
        ("technical", "medium", "Explain what happens when you type a URL in a browser.", "DNS, TCP/TLS, HTTP request, server, rendering - 4-5 steps."),
        ("technical", "medium", "What are indexes in a database and when do they hurt?", "Faster reads, slower writes; use on filtered/joined columns."),
        ("scenario", "medium", "Your client keeps changing requirements every few days. How do you handle it?", "Welcome change but make impact visible: estimates, change log, prioritized backlog."),
        ("behavioral", "medium", "Tell me about a time you explained a technical concept to a non-technical person.", "Show analogy use and checking for understanding."),
        ("behavioral", "medium", "Describe your most challenging project.", "What made it hard, your specific actions, the measurable result."),
    ],
    "Deloitte": [
        ("behavioral", "easy", "Tell me about yourself and why consulting.", "Show client mindset: solving problems for people, not just coding."),
        ("technical", "medium", "Explain a project end to end: problem, options, choice, result.", "Consultants probe decision-making, not just tech. Show trade-off thinking."),
        ("technical", "medium", "How would you explain a database to a client with no technical background?", "One clean analogy, zero jargon, check understanding."),
        ("scenario", "medium", "Case: a retail client's online sales dropped 20%. How would you structure your analysis?", "Framework aloud: internal vs external, funnel stages, data you would request."),
        ("scenario", "hard", "You discover your team's deliverable has a significant error the night before client presentation.", "Assess impact, inform lead immediately, fix or clearly caveat, propose follow-up plan."),
        ("behavioral", "medium", "Tell me about a time you led without formal authority.", "Influence through clarity and credibility, not title."),
        ("behavioral", "medium", "Describe a time you received vague direction from a senior person.", "How you scoped it: questions, assumptions written down, early checkpoint."),
    ],
    "IBM": [
        ("behavioral", "easy", "Tell me about yourself and your interest in IBM.", "Mention one real IBM area (cloud, AI/watsonx, consulting) and why it fits you."),
        ("technical", "easy", "What is the difference between SQL and NoSQL databases?", "Structure, scaling, one use case each."),
        ("technical", "medium", "Explain multithreading and one problem it can cause.", "Race condition or deadlock in plain words, plus one prevention."),
        ("technical", "medium", "Write SQL to count employees per department, sorted high to low.", "GROUP BY + ORDER BY; say each clause aloud as you write."),
        ("scenario", "medium", "You inherit code with no documentation. How do you become productive?", "Read tests, run it, trace one flow, add notes as you go, ask targeted questions."),
        ("behavioral", "medium", "Tell me about a time you automated something manual.", "What it saved; IBM values automation mindset."),
        ("behavioral", "medium", "Describe a failure and what it changed in how you work.", "Real failure, owned fully, with the lasting process change."),
    ],
    "Amazon": [
        ("behavioral", "medium", "Tell me about a time you took ownership of something outside your role.", "Leadership Principle: Ownership. Specific situation, your call, the result."),
        ("behavioral", "medium", "Describe a time you disagreed with your manager.", "Disagree and Commit: data-backed case, respectful, then full support of the decision."),
        ("behavioral", "medium", "Tell me about a time you failed.", "Real failure, your part in it, and the mechanism you built so it cannot repeat."),
        ("behavioral", "hard", "Give an example of when you invented or simplified something.", "Invent and Simplify: the before/after and the measured impact."),
        ("technical", "medium", "Coding: given an array, find two numbers that sum to a target.", "Hash map one-pass; narrate complexity before coding."),
        ("technical", "hard", "Design a system like an order-tracking page.", "Clarify requirements, sketch services and data flow, name one scaling trade-off."),
        ("scenario", "medium", "You find a teammate's shortcut that could risk customer data.", "Customer Obsession + Earn Trust: raise it privately first, escalate if unresolved."),
    ],
    "Google": [
        ("technical", "medium", "Coding: solve a medium array/string problem and state the complexity.", "Think out loud, brute force first, then optimize; state time and space."),
        ("technical", "hard", "Design a URL shortener or a autocomplete system.", "Requirements, high-level components, data model, one deep-dive trade-off."),
        ("technical", "medium", "Explain hash collisions and how a hash map handles them.", "Chaining vs open addressing in plain words."),
        ("behavioral", "medium", "Tell me about a time you solved an ambiguous problem.", "Googleyness: how you framed it, what you decided, what happened."),
        ("behavioral", "medium", "Describe a time you helped your team succeed without being asked.", "Initiative plus humility; credit the team."),
        ("behavioral", "medium", "Tell me about a mistake you made in a project.", "Own it, quantify the lesson, show the new habit."),
        ("scenario", "hard", "How would you measure whether a new feature is successful?", "Goal, metrics (with guardrails), experiment or analysis plan."),
    ],
    "Microsoft": [
        ("technical", "medium", "Coding: reverse words in a sentence or detect a cycle in a linked list.", "Clarify input constraints first, narrate the pointer/logic steps."),
        ("technical", "medium", "Explain the difference between processes, threads, and async.", "One line each plus when async beats threads."),
        ("technical", "hard", "Design a file-sync service like OneDrive.", "Chunks, conflict handling, offline - pick one and go deep."),
        ("behavioral", "medium", "Tell me about a time you learned from negative feedback.", "Growth mindset is the keyword they probe; be specific about the change."),
        ("behavioral", "medium", "Describe a time you had to collaborate across teams.", "How you aligned goals and handled the friction."),
        ("behavioral", "medium", "Tell me about a project you are most proud of.", "Your exact contribution and the impact, with numbers if possible."),
        ("scenario", "medium", "A service you own has rising latency. What do you check first?", "Metrics first, recent changes, dependencies, then profile - a logical order."),
    ],
    "Flipkart": [
        ("technical", "medium", "Coding: implement LRU cache or top-K frequent elements.", "Classic Flipkart asks; explain data structure choice before coding."),
        ("technical", "hard", "Machine coding: design a parking lot or split-wise style app in 90 minutes.", "Clarify requirements, clean classes, working happy path first, then extend."),
        ("technical", "medium", "How does indexing work in a database? What is a B-tree at a high level?", "Sorted structure, log-n lookups; no need for rotation math."),
        ("scenario", "medium", "Sale day traffic is 10x and one service is the bottleneck. What do you do?", "Scale reads (cache), queues for writes, degrade gracefully - prioritize the order flow."),
        ("behavioral", "medium", "Tell me about a time you shipped something with a very tight deadline.", "What you cut deliberately and how you protected quality of the core path."),
        ("behavioral", "medium", "Describe a time you disagreed with a technical decision.", "Data and prototype-based argument; commit once decided."),
        ("behavioral", "easy", "Why Flipkart?", "One genuine reason: scale problems, ownership culture, or a product you use."),
    ],
    "HDFC Bank": [
        ("behavioral", "easy", "Tell me about yourself and why banking.", "Stability plus customer trust; connect your skills to service or technology in banking."),
        ("technical", "easy", "What is the difference between savings account interest and a fixed deposit?", "Basic product fluency shows genuine interest in the domain."),
        ("technical", "medium", "For tech roles: how would you keep a customer's transaction data safe?", "Encryption at rest/in transit, least privilege, audit logs, masking - 3-4 concrete controls."),
        ("scenario", "medium", "A customer is angry about a failed transaction but the money left their account. What do you do?", "Listen fully, verify with facts, explain the reversal timeline clearly, follow up."),
        ("scenario", "medium", "You notice a process that could let an error or fraud slip through. What do you do?", "Report through the right channel immediately; banks reward control mindset."),
        ("behavioral", "medium", "Tell me about a time you handled a difficult customer or stakeholder.", "Patience, facts, resolution, and the relationship afterwards."),
        ("behavioral", "medium", "How do you handle targets or pressure?", "A real example with the routine you used; no burnout heroics."),
    ],
}


def for_company(name: str) -> dict | None:
    """Return the curated set for a canonical company name, or None."""
    rows = _SETS.get((name or "").strip())
    if not rows:
        return None
    return {
        "company": name.strip(),
        "note": _NOTE.format(name=name.strip()),
        "curated": True,
        "questions": [{"type": t, "level": lv, "question": q, "hint": h} for t, lv, q, h in rows],
    }


def companies_with_sets() -> list[str]:
    return sorted(_SETS)
