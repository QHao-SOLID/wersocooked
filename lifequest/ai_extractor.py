import json
import os
import random
import re

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = "deepseek-chat"

SKILL_KEYWORDS = {
    "python": ["Python", "Django", "Flask", "pandas", "numpy", "FastAPI", "PyTorch", "TensorFlow"],
    "javascript": ["JavaScript", "React", "Vue", "Angular", "Node.js", "TypeScript", "jQuery"],
    "java": ["Java", "Spring Boot", "Hibernate", "Maven", "Gradle"],
    "data": ["SQL", "Machine Learning", "Data Analysis", "Tableau", "Power BI", "Statistics"],
    "web": ["HTML", "CSS", "Responsive Design", "REST API", "GraphQL"],
    "devops": ["Docker", "Kubernetes", "AWS", "Azure", "CI/CD", "Linux"],
    "mobile": ["Android", "iOS", "React Native", "Flutter", "Kotlin", "Swift"],
    "soft": ["Communication", "Teamwork", "Leadership", "Problem Solving", "Time Management"],
}

CLASS_MAP = {
    "Warrior": {"icon": "⚔", "desc": "Backend, infrastructure, DevOps"},
    "Mage": {"icon": "🔮", "desc": "AI/ML, data science, research"},
    "Rogue": {"icon": "🗡", "desc": "Frontend, mobile, UI/UX, security"},
    "Paladin": {"icon": "🛡", "desc": "PM, leadership, product"},
    "Ranger": {"icon": "🏹", "desc": "Full-stack, generalist"},
    "Bard": {"icon": "🎵", "desc": "Design, creative, communication"},
}

CLASS_STATS = {
    "Warrior": {"strength": 5, "intelligence": 2, "dexterity": 3, "wisdom": 2, "charisma": 3},
    "Mage": {"strength": 1, "intelligence": 5, "dexterity": 2, "wisdom": 4, "charisma": 3},
    "Rogue": {"strength": 2, "intelligence": 3, "dexterity": 5, "wisdom": 3, "charisma": 2},
    "Paladin": {"strength": 3, "intelligence": 3, "dexterity": 2, "wisdom": 4, "charisma": 5},
    "Ranger": {"strength": 3, "intelligence": 3, "dexterity": 4, "wisdom": 3, "charisma": 3},
    "Bard": {"strength": 1, "intelligence": 3, "dexterity": 3, "wisdom": 3, "charisma": 5},
}

CLASS_SKILL_TREES = {
    "Warrior": [
        {"id": "w1", "name": "Git", "desc": "Version control mastery", "level": 1, "deps": []},
        {"id": "w2", "name": "Docker", "desc": "Containerize anything", "level": 2, "deps": ["w1"]},
        {"id": "w3", "name": "Linux", "desc": "Terminal combat veteran", "level": 2, "deps": ["w1"]},
        {"id": "w4", "name": "AWS", "desc": "Cloud infrastructure", "level": 3, "deps": ["w2", "w3"]},
        {"id": "w5", "name": "CI/CD", "desc": "Automated deployment", "level": 4, "deps": ["w4"]},
        {"id": "w6", "name": "Kubernetes", "desc": "Orchestrate armies of containers", "level": 5, "deps": ["w5"]},
    ],
    "Mage": [
        {"id": "m1", "name": "Python", "desc": "Arcane coding arts", "level": 1, "deps": []},
        {"id": "m2", "name": "SQL", "desc": "Query the database of knowledge", "level": 2, "deps": ["m1"]},
        {"id": "m3", "name": "Machine Learning", "desc": "Train magical models", "level": 3, "deps": ["m1", "m2"]},
        {"id": "m4", "name": "Deep Learning", "desc": "Neural network sorcery", "level": 4, "deps": ["m3"]},
        {"id": "m5", "name": "NLP", "desc": "Speak the language of machines", "level": 4, "deps": ["m3"]},
        {"id": "m6", "name": "AI Research", "desc": "Push the boundaries of magic", "level": 5, "deps": ["m4", "m5"]},
    ],
    "Rogue": [
        {"id": "r1", "name": "JavaScript", "desc": "Stealthy scripting", "level": 1, "deps": []},
        {"id": "r2", "name": "React", "desc": "Reactive UI daggers", "level": 2, "deps": ["r1"]},
        {"id": "r3", "name": "CSS", "desc": "Style camouflage", "level": 2, "deps": ["r1"]},
        {"id": "r4", "name": "Performance", "desc": "Speed optimization", "level": 3, "deps": ["r2", "r3"]},
        {"id": "r5", "name": "Security", "desc": "Find vulnerabilities", "level": 4, "deps": ["r4"]},
        {"id": "r6", "name": "Mobile Dev", "desc": "Strike from any device", "level": 5, "deps": ["r5"]},
    ],
    "Paladin": [
        {"id": "p1", "name": "Communication", "desc": "Inspire your party", "level": 1, "deps": []},
        {"id": "p2", "name": "Agile", "desc": "Lead with agility", "level": 2, "deps": ["p1"]},
        {"id": "p3", "name": "Project Management", "desc": "Coordinate quests", "level": 3, "deps": ["p2"]},
        {"id": "p4", "name": "Strategy", "desc": "Long-term vision", "level": 4, "deps": ["p3"]},
        {"id": "p5", "name": "Mentoring", "desc": "Level up your allies", "level": 4, "deps": ["p3"]},
        {"id": "p6", "name": "Executive Leadership", "desc": "Command respect", "level": 5, "deps": ["p4", "p5"]},
    ],
    "Ranger": [
        {"id": "ra1", "name": "Python", "desc": "Multi-purpose tool", "level": 1, "deps": []},
        {"id": "ra2", "name": "JavaScript", "desc": "Frontier scripting", "level": 1, "deps": []},
        {"id": "ra3", "name": "REST API", "desc": "Connect distant lands", "level": 2, "deps": ["ra1", "ra2"]},
        {"id": "ra4", "name": "Database", "desc": "Store your findings", "level": 3, "deps": ["ra3"]},
        {"id": "ra5", "name": "DevOps", "desc": "Survive any terrain", "level": 4, "deps": ["ra4"]},
        {"id": "ra6", "name": "Architecture", "desc": "Design entire worlds", "level": 5, "deps": ["ra5"]},
    ],
    "Bard": [
        {"id": "b1", "name": "Design", "desc": "Visual storytelling", "level": 1, "deps": []},
        {"id": "b2", "name": "Writing", "desc": "Craft compelling tales", "level": 1, "deps": []},
        {"id": "b3", "name": "UX Research", "desc": "Understand your audience", "level": 2, "deps": ["b1", "b2"]},
        {"id": "b4", "name": "Branding", "desc": "Create a legend", "level": 3, "deps": ["b3"]},
        {"id": "b5", "name": "Content Strategy", "desc": "Plan the narrative", "level": 4, "deps": ["b4"]},
        {"id": "b6", "name": "Creative Direction", "desc": "Lead the vision", "level": 5, "deps": ["b5"]},
    ],
}


def _get_deepseek_client():
    if not DEEPSEEK_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    except ImportError:
        return None


def _call_deepseek(prompt, temp=0.3):
    client = _get_deepseek_client()
    if not client:
        return None
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=temp,
        max_tokens=2048,
    )
    return json.loads(resp.choices[0].message.content)


def _extract_pdf_text(filepath):
    import PyPDF2
    reader = PyPDF2.PdfReader(filepath)
    lines = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            for line in t.split("\n"):
                s = line.strip()
                if s and len(s) > 2:
                    lines.append(s)
    return lines


def _mock_extract(filepath):
    lines = _extract_pdf_text(filepath)
    full_text = " ".join(lines).lower()

    all_skills_map = {}
    for cat_skills in SKILL_KEYWORDS.values():
        for s in cat_skills:
            all_skills_map[s.lower()] = s
    found = []
    for sk_lower, sk_orig in all_skills_map.items():
        if sk_lower in full_text:
            found.append(sk_orig)
    if not found:
        all_s = list(all_skills_map.values())
        found = random.sample(all_s, min(4, len(all_s)))

    meta = {"name": "", "email": "", "phone": "", "social_media": [], "location": ""}
    for line in lines[:8]:
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", line)
        if email_match:
            meta["email"] = email_match.group()
        phone_match = re.search(r"[\+\d][\d\s\-\(\)]{7,20}[\d]", line)
        if phone_match:
            meta["phone"] = phone_match.group().strip()[:25]
        if any(w in line.lower() for w in ["linkedin", "github", "twitter"]):
            meta["social_media"].append(line.strip()[:50])
        if not meta["name"] and len(line.strip().split()) in (2, 3) and not any(
            w in line.lower() for w in ["page", "pdf", "curriculum", "resume", "cv"]
        ):
            cleaned = re.sub(r"[^a-zA-Z\s]", "", line).strip()
            if 5 < len(cleaned) < 40:
                meta["name"] = cleaned

    role = "Unknown"
    for line in lines[:8]:
        if any(w in line.lower() for w in ["engineer", "developer", "designer", "manager", "analyst", "lead", "architect"]):
            role = re.sub(r"[^a-zA-Z0-9\s\-/]", "", line).strip()[:60]
            break

    exp = "mid"
    if any(w in full_text for w in ["junior", "entry", "intern", "fresher"]):
        exp = "entry"
    elif any(w in full_text for w in ["senior", "lead", "principal", "head", "director"]):
        exp = "senior"

    work_experience = []
    for i, line in enumerate(lines):
        if any(w in line.lower() for w in ["engineer", "developer", "manager", "analyst", "intern"]):
            org = ""
            for j in range(max(0, i - 2), i):
                if any(w in lines[j].lower() for w in ["at ", "company", "corp", "ltd", "inc", "llc", "organization"]):
                    org = lines[j][:40]
                    break
            work_experience.append({
                "organisation": org or "Previous Employer",
                "role": re.sub(r"[^a-zA-Z0-9\s\-/]", "", line).strip()[:50],
                "achievements": "Accomplished key deliverables and improved processes." if len(work_experience) < 2 else "",
                "skills_obtained": random.sample(found, min(2, len(found))) if found else [],
                "location": "",
                "duration": "2022 - 2024",
            })

    education = []
    for line in lines:
        if any(w in line.lower() for w in ["university", "college", "institute", "school of", "bachelor", "master", "phd", "bsc", "msc", "b.tech", "m.tech"]):
            edu = {
                "institution": re.sub(r"[^a-zA-Z0-9\s]", "", line).strip()[:50],
                "course": "",
                "results": "",
                "subjects": [],
                "activities": [],
                "location": "",
                "duration": "",
            }
            # look ahead for degree info
            for j in range(lines.index(line) + 1, min(lines.index(line) + 5, len(lines))):
                lw = lines[j].lower()
                if not edu["course"] and any(w in lw for w in ["computer", "engineering", "science", "business", "arts", "bachelor", "master"]):
                    edu["course"] = lines[j].strip()[:50]
                if not edu["results"] and any(w in lw for w in ["gpa", "cgpa", "grade", "percentage", "score"]):
                    edu["results"] = lines[j].strip()[:40]
                if any(w in lw for w in ["club", "society", "sport", "volunteer", "event"]):
                    edu["activities"].append(lines[j].strip()[:40])
            education.append(edu)
            break

    return {
        "meta": meta,
        "skills": found,
        "experience_level": exp,
        "years_experience": 3,
        "top_skills": found[:3],
        "role": role,
        "industry": "Technology",
        "work_experience": work_experience,
        "education": education,
        "leadership": [],
        "projects": [],
        "personality_traits": ["Analytical", "Problem Solver"],
        "rpg_class": "Warrior",
    }


def extract_cv(filepath):
    lines = _extract_pdf_text(filepath)
    full_text = "\n".join(lines)

    if not full_text.strip():
        return {"skills": [], "error": "Could not extract text from PDF"}

    result = _call_deepseek(f"""Extract structured data from this CV/resume as JSON only.
Use null for missing fields, empty arrays for lists with no items.

Schema:
{{
  "meta": {{
    "name": "Full name",
    "email": "email address",
    "phone": "phone number",
    "social_media": ["LinkedIn URL", "GitHub URL", ...],
    "location": "City, Country"
  }},
  "skills": ["skill1", "skill2", ...],
  "experience_level": "entry|mid|senior|lead",
  "years_experience": number,
  "top_skills": ["top 5 most relevant"],
  "role": "current or most recent job title",
  "industry": "industry name",
  "work_experience": [
    {{
      "organisation": "Company name",
      "role": "Job title",
      "achievements": "Key accomplishments",
      "skills_obtained": ["skill1", "skill2"],
      "location": "City, Country",
      "duration": "Start - End"
    }}
  ],
  "education": [
    {{
      "institution": "School/University name",
      "course": "Degree / course name",
      "results": "Grades / GPA / classification",
      "subjects": ["subject1", "subject2"],
      "activities": ["club", "sport", "volunteer", ...],
      "location": "City, Country",
      "duration": "Start - End"
    }}
  ],
  "leadership": [
    {{
      "place": "Organization / event name",
      "role": "Position held",
      "notes": "What was done",
      "duration": "Start - End"
    }}
  ],
  "projects": [
    {{
      "certifications": ["cert name"],
      "project_name": "Project title",
      "project_type": "personal|academic|professional|open_source",
      "notes": "Description",
      "duration": "Start - End",
      "proof_link": "URL or reference ID"
    }}
  ],
  "personality_traits": ["trait1", "trait2"],
  "rpg_class": "Warrior|Mage|Rogue|Paladin|Ranger|Bard"
}}

RPG class rules:
- Warrior = backend, infra, DevOps, sysadmin
- Mage = AI/ML, data science, research, analytics
- Rogue = frontend, mobile, UI/UX, security
- Paladin = PM, leadership, product, scrum
- Ranger = full-stack, generalist, versatile
- Bard = design, creative, communication, marketing

CV:
{full_text[:8000]}""")

    if result:
        return result

    return _mock_extract(filepath)


def generate_skill_tree(skills, rpg_class):
    if not skills:
        return {"nodes": [], "class": rpg_class, "stat_allocation": CLASS_STATS.get(rpg_class, CLASS_STATS["Warrior"])}

    result = _call_deepseek(f"""Generate an RPG skill tree from these professional skills for a {rpg_class} class.
Return JSON:
{{
  "class": "{rpg_class}",
  "nodes": [
    {{
      "id": "node1",
      "name": "skill_name",
      "description": "rpg_style description",
      "level": 1-5,
      "dependencies": [],
      "skill_match": "original skill name from list"
    }}
  ],
  "stat_allocation": {{
    "strength": 1-5,
    "intelligence": 1-5,
    "dexterity": 1-5,
    "wisdom": 1-5,
    "charisma": 1-5
  }}
}}
Each skill from the list should map to a node. Dependencies reference other node IDs.
Skills: {json.dumps(skills)}""", temp=0.5)

    if result and "nodes" in result:
        return result

    tree = CLASS_SKILL_TREES.get(rpg_class, CLASS_SKILL_TREES["Warrior"])
    matched_nodes = []
    for node in tree:
        if node["name"] in skills:
            node["skill_match"] = node["name"]
            node["unlocked"] = True
            matched_nodes.append(node)
    if not matched_nodes:
        matched_nodes = [
            {"id": "n1", "name": skills[0], "description": "Your primary skill", "level": 1, "dependencies": [], "skill_match": skills[0], "unlocked": True}
        ]

    return {
        "class": rpg_class,
        "nodes": matched_nodes,
        "stat_allocation": CLASS_STATS.get(rpg_class, CLASS_STATS["Warrior"]),
    }


def process_text_entry(text):
    """Classify and extract structured entry from arbitrary text.
    Returns {section_type, entry, skills_extracted}."""
    if not text.strip():
        return {"section_type": "projects", "entry": {}, "skills_extracted": []}

    result = _call_deepseek(f"""Classify this text and extract structured data as JSON only.

Rules:
- Classify into exactly one section: "work_experience", "education", "leadership", or "projects"
- "projects" is the default if unclear (includes certifications, open source, side projects)
- Extract fields matching the section type
- Also extract any skill keywords mentioned

Output schema:
{{
  "section_type": "work_experience|education|leadership|projects",
  "entry": {{
    // For work_experience:
    "organisation": "",
    "role": "",
    "achievements": "",
    "skills_obtained": [],
    "location": "",
    "duration": ""
    // For education:
    "institution": "",
    "course": "",
    "results": "",
    "subjects": [],
    "activities": [],
    "location": "",
    "duration": ""
    // For leadership:
    "place": "",
    "role": "",
    "notes": "",
    "duration": ""
    // For projects (default):
    "project_name": "",
    "project_type": "personal|academic|professional|open_source",
    "notes": "",
    "duration": "",
    "proof_link": "",
    "certifications": []
  }},
  "skills_extracted": ["skill1", "skill2"]
}}

Text: {text[:4000]}""")

    if result and "section_type" in result:
        return result

    return _mock_process_text(text)


def _mock_process_text(text):
    """Heuristic mock fallback for process_text_entry."""
    t = text.lower()
    skills = []
    all_skills_map = {}
    for cat_skills in SKILL_KEYWORDS.values():
        for s in cat_skills:
            all_skills_map[s.lower()] = s
    for sk_lower, sk_orig in all_skills_map.items():
        if sk_lower in t:
            skills.append(sk_orig)
    if not skills:
        all_s = list(all_skills_map.values())
        skills = random.sample(all_s, min(3, len(all_s)))

    section_type = "projects"
    entry = {"project_name": "", "project_type": "personal", "notes": text[:500], "duration": "", "proof_link": "", "certifications": []}

    if any(w in t for w in ["experience", "worked", "employed", "company", "job", "role", "position"]):
        section_type = "work_experience"
        entry = {"organisation": "", "role": "", "achievements": text[:300], "skills_obtained": skills, "location": "", "duration": ""}
        for line in text.split("\n")[:5]:
            if any(w in line.lower() for w in ["at ", "company", "corp", "ltd", "inc"]):
                entry["organisation"] = line.strip()[:50]
    elif any(w in t for w in ["university", "college", "school", "bachelor", "master", "phd", "degree", "course"]):
        section_type = "education"
        entry = {"institution": "", "course": "", "results": "", "subjects": skills[:3], "activities": [], "location": "", "duration": ""}
        for line in text.split("\n")[:5]:
            if any(w in line.lower() for w in ["university", "college", "institute"]):
                entry["institution"] = line.strip()[:50]
    elif any(w in t for w in ["lead", "volunteer", "president", "organized", "club", "society", "mentor"]):
        section_type = "leadership"
        entry = {"place": "", "role": "", "notes": text[:300], "duration": ""}
    elif any(w in t for w in ["certif", "credential", "badge", "course"]):
        section_type = "projects"
        entry["certifications"] = [text.split("\n")[0].strip()[:60]]
        entry["project_name"] = "Certification"

    if not entry.get("project_name") and section_type == "projects":
        entry["project_name"] = text.split("\n")[0].strip()[:60] or "Untitled"

    return {"section_type": section_type, "entry": entry, "skills_extracted": skills}
