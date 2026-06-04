import json

def xp_for_level(level):
    """XP needed to go from `level` to `level+1`."""
    return int(100 * (level ** 1.5))

def check_level_up(conn, user_id):
    """Loop: while xp >= threshold, level up (full heal each time)."""
    profile = conn.execute(
        "SELECT level, xp, xp_to_next, hp, max_hp FROM player_profiles WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not profile:
        return {"leveled_up": False, "levels_gained": 0, "new_level": 1}

    level = profile["level"]
    xp = profile["xp"]
    hp = profile["hp"]
    max_hp = profile["max_hp"]
    threshold = profile["xp_to_next"] if level == 1 else xp_for_level(level)
    levels_gained = 0

    while xp >= threshold:
        xp -= threshold
        level += 1
        max_hp += 10
        hp = max_hp
        levels_gained += 1
        threshold = xp_for_level(level)

    conn.execute(
        """UPDATE player_profiles SET
            level = ?, xp = ?, xp_to_next = ?, hp = ?, max_hp = ?
        WHERE user_id = ?""",
        (level, xp, threshold, hp, max_hp, user_id),
    )
    conn.commit()

    return {
        "leveled_up": levels_gained > 0,
        "levels_gained": levels_gained,
        "new_level": level,
    }

# ── Friend helpers ──

def are_friends(conn, user_a, user_b):
    if user_a == user_b:
        return False
    row = conn.execute(
        """SELECT 1 FROM friend_requests
        WHERE ((from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?))
        AND status = 'accepted'""",
        (user_a, user_b, user_b, user_a),
    ).fetchone()
    return row is not None

def get_friends(conn, user_id):
    rows = conn.execute(
        """SELECT u.id, u.username, p.level, p.char_class, p.title, p.avatar, p.last_login
        FROM friend_requests fr
        JOIN users u ON (CASE WHEN fr.from_user = ? THEN fr.to_user ELSE fr.from_user END) = u.id
        JOIN player_profiles p ON u.id = p.user_id
        WHERE (fr.from_user = ? OR fr.to_user = ?) AND fr.status = 'accepted'""",
        (user_id, user_id, user_id),
    ).fetchall()
    return [dict(r) for r in rows]

def count_friends(conn, user_id):
    return len(get_friends(conn, user_id))

def get_friend_requests_incoming(conn, user_id):
    rows = conn.execute(
        """SELECT fr.id, fr.from_user, u.username, p.char_class, p.level, p.avatar, fr.timestamp
        FROM friend_requests fr
        JOIN users u ON fr.from_user = u.id
        JOIN player_profiles p ON u.id = p.user_id
        WHERE fr.to_user = ? AND fr.status = 'pending'
        ORDER BY fr.timestamp DESC""",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]

def get_friend_requests_outgoing(conn, user_id):
    rows = conn.execute(
        """SELECT fr.id, fr.to_user, u.username, p.char_class, p.level, p.avatar, fr.timestamp
        FROM friend_requests fr
        JOIN users u ON fr.to_user = u.id
        JOIN player_profiles p ON u.id = p.user_id
        WHERE fr.from_user = ? AND fr.status = 'pending'
        ORDER BY fr.timestamp DESC""",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]

def send_friend_request(conn, from_id, to_id):
    if from_id == to_id:
        return False, "Cannot friend yourself"
    if are_friends(conn, from_id, to_id):
        return False, "Already friends"
    existing = conn.execute(
        "SELECT 1 FROM friend_requests WHERE from_user = ? AND to_user = ? AND status = 'pending'",
        (from_id, to_id),
    ).fetchone()
    if existing:
        return False, "Request already sent"
    reverse = conn.execute(
        "SELECT 1 FROM friend_requests WHERE from_user = ? AND to_user = ? AND status = 'pending'",
        (to_id, from_id),
    ).fetchone()
    if reverse:
        return False, "This user already sent you a request"
    conn.execute(
        "INSERT INTO friend_requests (from_user, to_user, status) VALUES (?, ?, 'pending')",
        (from_id, to_id),
    )
    conn.commit()
    return True, "Friend request sent!"

def accept_friend_request(conn, request_id, user_id):
    row = conn.execute(
        "SELECT * FROM friend_requests WHERE id = ? AND to_user = ? AND status = 'pending'",
        (request_id, user_id),
    ).fetchone()
    if not row:
        return False, "Request not found"
    conn.execute("UPDATE friend_requests SET status = 'accepted' WHERE id = ?", (request_id,))
    conn.commit()
    return True, "Friend request accepted!"

def reject_friend_request(conn, request_id, user_id):
    row = conn.execute(
        "SELECT * FROM friend_requests WHERE id = ? AND to_user = ? AND status = 'pending'",
        (request_id, user_id),
    ).fetchone()
    if not row:
        return False, "Request not found"
    conn.execute("DELETE FROM friend_requests WHERE id = ?", (request_id,))
    conn.commit()
    return True, "Friend request rejected"

def remove_friend(conn, user_id, friend_id):
    if not are_friends(conn, user_id, friend_id):
        return False, "Not friends"
    conn.execute(
        """DELETE FROM friend_requests
        WHERE ((from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?))
        AND status = 'accepted'""",
        (user_id, friend_id, friend_id, user_id),
    )
    conn.commit()
    return True, "Friend removed"

# ── Quest system ──

SKILL_COMPLEMENTS = [
    ("Python", "SQL", "Python developers need SQL for backend roles. Learn basic queries and database design."),
    ("React", "TypeScript", "React projects increasingly use TypeScript for type safety and better DX."),
    ("Docker", "Kubernetes", "Docker pairs with Kubernetes for container orchestration at scale."),
    ("Machine Learning", "SQL", "ML engineers need SQL to query and prepare datasets."),
    ("JavaScript", "React", "React is the most in-demand frontend framework for JavaScript developers."),
    ("AWS", "Docker", "Cloud deployments use Docker containers on AWS ECS/EKS."),
    ("Node.js", "TypeScript", "Node.js backends commonly adopt TypeScript for maintainability."),
    ("Data Analysis", "SQL", "Data analysts need SQL to query and manipulate databases."),
]

LEVEL_ADVICE = [
    (1, "Build a portfolio project — even a small one shows initiative."),
    (2, "Start contributing to open source. One PR is enough to stand out."),
    (4, "Learn system design fundamentals — essential for mid-level roles."),
    (6, "Mentor junior developers. Teaching accelerates your own growth."),
    (9, "Consider writing or speaking at meetups. Visibility opens doors."),
]

QUESTS_PER_REGEN = 5


def generate_quests(conn, user_id):
    """Generate active quests based on profile gaps. Preserves completed quests."""
    profile = conn.execute(
        "SELECT * FROM player_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not profile:
        return []

    skills = json.loads(profile["skills"]) if profile["skills"] else []
    cv_data = json.loads(profile["cv_data"]) if profile["cv_data"] else {}
    level = profile["level"]
    old_quests = json.loads(profile["quests"]) if profile["quests"] else []
    completed = [q for q in old_quests if q.get("status") == "completed"]

    new_quests = []
    idx = 0

    # 1. Skill complement gaps
    for sk_have, sk_need, why in SKILL_COMPLEMENTS:
        if sk_have in skills and sk_need not in skills:
            new_quests.append({
                "id": f"q_skill_{idx}", "category": "skill_gap", "priority": "high",
                "title": f"Learn {sk_need}",
                "description": f"You have {sk_have} but not {sk_need}. {why}",
                "xp_reward": 100, "status": "active", "proof": "", "proof_url": "",
            })
            idx += 1

    # 2. Profile completeness
    if not cv_data.get("work_experience"):
        new_quests.append({
            "id": f"q_profile_{idx}", "category": "profile_completion", "priority": "high",
            "title": "Add work experience",
            "description": "Your profile has no work history. Add internships, freelance work, or past roles.",
            "xp_reward": 80, "status": "active", "proof": "", "proof_url": "",
        })
        idx += 1
    if not cv_data.get("projects"):
        new_quests.append({
            "id": f"q_profile_{idx}", "category": "profile_completion", "priority": "medium",
            "title": "Add a project",
            "description": "No projects listed. Build something with your current skills and add it via AI Import.",
            "xp_reward": 60, "status": "active", "proof": "", "proof_url": "",
        })
        idx += 1
    if not cv_data.get("education"):
        new_quests.append({
            "id": f"q_profile_{idx}", "category": "profile_completion", "priority": "low",
            "title": "Add your education",
            "description": "List your degree or courses. Education builds credibility.",
            "xp_reward": 40, "status": "active", "proof": "", "proof_url": "",
        })
        idx += 1

    # 3. Advancement advice based on level
    for adv_level, advice in LEVEL_ADVICE:
        if level >= adv_level and not any(q.get("title") == advice[:30] for q in completed + new_quests):
            new_quests.append({
                "id": f"q_adv_{idx}", "category": "career_advancement", "priority": "medium",
                "title": advice[:50].rsplit(" ", 1)[0] + ("..." if len(advice) > 50 else ""),
                "description": advice,
                "xp_reward": 60, "status": "active", "proof": "", "proof_url": "",
            })
            idx += 1
            break  # one advancement quest at a time

    # 4. Certifications
    have_certs = any(p.get("certifications") for p in cv_data.get("projects", []))
    if not have_certs and skills:
        new_quests.append({
            "id": f"q_cert_{idx}", "category": "certification", "priority": "medium",
            "title": "Earn a certification",
            "description": "Certifications validate your skills. Consider AWS, Azure, or a cloud certification.",
            "xp_reward": 70, "status": "active", "proof": "", "proof_url": "",
        })
        idx += 1

    # 5. Social engagement
    friend_count = count_friends(conn, user_id)
    if friend_count < 3:
        new_quests.append({
            "id": f"q_social_{idx}", "category": "social", "priority": "low",
            "title": "Connect with 3 players",
            "description": "Networking is powerful. Find 3 players on the players page and connect.",
            "xp_reward": 50, "status": "active", "proof": "", "proof_url": "",
        })
        idx += 1

    # Limit to QUESTS_PER_REGEN active quests
    active = new_quests[:QUESTS_PER_REGEN]
    return completed + active


def complete_quest(conn, user_id, quest_id, proof, proof_url=""):
    """Mark a quest as completed, award XP. Returns (success, msg, xp_gained)."""
    profile = conn.execute(
        "SELECT quests FROM player_profiles WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not profile:
        return False, "Profile not found", 0

    quests = json.loads(profile["quests"]) if profile["quests"] else []
    found = None
    for q in quests:
        if q["id"] == quest_id and q.get("status") == "active":
            found = q
            break
    if not found:
        return False, "Quest not found or already completed", 0
    if not proof.strip():
        return False, "Proof of work required", 0

    xp_gain = found.get("xp_reward", 50)
    found["status"] = "completed"
    found["proof"] = proof.strip()
    found["proof_url"] = proof_url.strip()

    conn.execute(
        "UPDATE player_profiles SET quests = ?, xp = xp + ? WHERE user_id = ?",
        (json.dumps(quests), xp_gain, user_id),
    )
    conn.commit()

    return True, "Quest completed!", xp_gain
