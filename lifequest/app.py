import json
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.template_folder = "templates"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, "avatars")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)

from ai_extractor import extract_cv, generate_skill_tree, process_text_entry, CLASS_MAP
from game_mechanics import (
    check_level_up, are_friends, get_friends, count_friends,
    get_friend_requests_incoming, get_friend_requests_outgoing,
    send_friend_request, accept_friend_request, reject_friend_request, remove_friend,
    generate_quests, complete_quest,
)

@app.template_filter("from_json")
def from_json(value):
    return json.loads(value) if value else []

from db import get_db, init_db
from auth import login_required, login_user, register_user

init_db()

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if login_user(request.form["username"], request.form["password"]):
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        avatar = request.form.get("avatar", "").strip()
        success, msg = register_user(
            request.form["username"], request.form["email"], request.form["password"],
            avatar
        )
        if success:
            login_user(request.form["username"], request.form["password"])
            flash("Welcome to LifeQuest!", "success")
            return redirect(url_for("dashboard"))
        flash(msg, "danger")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    conn = get_db()
    profile = conn.execute(
        "SELECT * FROM player_profiles WHERE user_id = ?", (uid,)
    ).fetchone()
    active_events = conn.execute(
        "SELECT * FROM events WHERE active = 1 AND (end_time IS NULL OR end_time > datetime('now'))"
    ).fetchall()
    incoming = get_friend_requests_incoming(conn, uid)
    friend_count = count_friends(conn, uid)
    quests = json.loads(profile["quests"]) if profile and profile["quests"] else []
    avatar = profile["avatar"] if profile and profile["avatar"] else "🧑"
    conn.close()
    return render_template(
        "dashboard.html",
        profile=profile,
        username=session["username"],
        events=active_events,
        avatar=avatar,
        incoming_requests=incoming[:3],
        friend_count=friend_count,
        quests=quests,
    )

@app.route("/profile/<username>")
@login_required
def profile(username):
    uid = session["user_id"]
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        flash("Player not found", "danger")
        return redirect(url_for("dashboard"))
    profile = conn.execute(
        "SELECT * FROM player_profiles WHERE user_id = ?", (user["id"],)
    ).fetchone()
    is_friend = are_friends(conn, uid, user["id"])
    p_friend_count = count_friends(conn, user["id"])
    quests = json.loads(profile["quests"]) if profile and profile["quests"] else []
    completed = sum(1 for q in quests if q.get("status") == "completed")
    p_avatar = profile["avatar"] if profile and profile["avatar"] else "🧑"
    is_own = uid == user["id"]
    conn.close()
    return render_template(
        "profile.html",
        profile=profile,
        p_username=username,
        p_user_id=user["id"],
        is_friend=is_friend,
        p_friend_count=p_friend_count,
        p_avatar=p_avatar,
        is_own=is_own,
        quests_completed=completed,
    )

@app.route("/friends")
@login_required
def friends_page():
    uid = session["user_id"]
    conn = get_db()
    friends_list = get_friends(conn, uid)
    incoming = get_friend_requests_incoming(conn, uid)
    outgoing = get_friend_requests_outgoing(conn, uid)
    conn.close()
    return render_template(
        "friends.html",
        friends=friends_list,
        incoming_requests=incoming,
        outgoing_requests=outgoing,
    )

# ── Avatar update ──

ALLOWED_AVATAR_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

@app.route("/profile/update-avatar", methods=["POST"])
@login_required
def update_avatar():
    uid = session["user_id"]
    conn = get_db()

    # File upload takes priority
    if "avatar_file" in request.files:
        f = request.files["avatar_file"]
        if f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext in ALLOWED_AVATAR_EXT:
                filename = f"{uid}{ext}"
                f.save(os.path.join(AVATAR_FOLDER, filename))
                conn.execute("UPDATE player_profiles SET avatar = ? WHERE user_id = ?", (f"custom:{filename}", uid))
                conn.commit()
                conn.close()
                flash("Avatar updated!", "success")
                return redirect(url_for("profile", username=session["username"]))

    # Emoji fallback
    emoji = request.form.get("avatar", "").strip()
    if emoji:
        conn.execute("UPDATE player_profiles SET avatar = ? WHERE user_id = ?", (emoji, uid))
        conn.commit()
        conn.close()
        flash("Avatar updated!", "success")
        return redirect(url_for("profile", username=session["username"]))

    conn.close()
    flash("No avatar provided", "danger")
    return redirect(url_for("profile", username=session["username"]))

# ── Friend action routes ──

@app.route("/friend/send/<int:user_id>", methods=["POST"])
@login_required
def friend_send(user_id):
    uid = session["user_id"]
    conn = get_db()
    success, msg = send_friend_request(conn, uid, user_id)
    conn.close()
    return jsonify({"success": success, "message": msg})

@app.route("/friend/accept/<int:request_id>", methods=["POST"])
@login_required
def friend_accept(request_id):
    uid = session["user_id"]
    conn = get_db()
    success, msg = accept_friend_request(conn, request_id, uid)
    conn.close()
    if not success:
        flash(msg, "danger")
    else:
        flash(msg, "success")
    return redirect(url_for("friends_page"))

@app.route("/friend/reject/<int:request_id>", methods=["POST"])
@login_required
def friend_reject(request_id):
    uid = session["user_id"]
    conn = get_db()
    success, msg = reject_friend_request(conn, request_id, uid)
    conn.close()
    if not success:
        flash(msg, "danger")
    else:
        flash(msg, "info")
    return redirect(url_for("friends_page"))

@app.route("/friend/remove/<int:friend_id>", methods=["POST"])
@login_required
def friend_remove(friend_id):
    uid = session["user_id"]
    conn = get_db()
    success, msg = remove_friend(conn, uid, friend_id)
    conn.close()
    if not success:
        flash(msg, "danger")
    else:
        flash(msg, "info")
    return redirect(url_for("friends_page"))

# ── CV upload ──

@app.route("/cv/upload", methods=["POST"])
@login_required
def cv_upload():
    if "cv_file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["cv_file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files accepted"}), 400

    filename = secure_filename(f"{session['user_id']}_{file.filename}")
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    try:
        data = extract_cv(path)
    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

    skills = data.get("skills", [])
    rpg_class = data.get("rpg_class", "Warrior")
    role = data.get("role", "Adventurer")
    exp = data.get("experience_level", "mid")
    char_class_info = CLASS_MAP.get(rpg_class, {"icon": "?", "desc": ""})

    xp_gain = min(len(skills) * 20, 200)
    uid = session["user_id"]
    conn = get_db()
    profile = conn.execute("SELECT * FROM player_profiles WHERE user_id = ?", (uid,)).fetchone()
    existing_skills = json.loads(profile["skills"]) if profile and profile["skills"] else []
    merged = list(dict.fromkeys(existing_skills + skills))

    quests = generate_quests(conn, uid)

    conn.execute(
        """UPDATE player_profiles SET
            skills = ?, cv_data = ?, quests = ?, title = ?, char_class = ?,
            xp = xp + ?, last_login = datetime('now')
        WHERE user_id = ?""",
        (json.dumps(merged), json.dumps(data), json.dumps(quests), role[:50], rpg_class, xp_gain, uid),
    )
    conn.commit()
    level_up = check_level_up(conn, uid)
    conn.close()

    return jsonify({
        "skills": merged,
        "rpg_class": rpg_class,
        "class_icon": char_class_info["icon"],
        "class_desc": char_class_info["desc"],
        "xp_gained": xp_gain,
        "role": role,
        "experience": exp,
        "leveled_up": level_up["leveled_up"],
        "levels_gained": level_up["levels_gained"],
        "new_level": level_up["new_level"],
    })

# ── AI text import ──

@app.route("/cv/add-entry", methods=["POST"])
@login_required
def cv_add_entry():
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        result = process_text_entry(text)
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    section_type = result.get("section_type", "projects")
    entry = result.get("entry", {})
    new_skills = result.get("skills_extracted", [])

    uid = session["user_id"]
    conn = get_db()
    profile = conn.execute("SELECT * FROM player_profiles WHERE user_id = ?", (uid,)).fetchone()
    if not profile:
        conn.close()
        return jsonify({"error": "Profile not found"}), 404

    cv_data = json.loads(profile["cv_data"]) if profile["cv_data"] else {}
    if section_type not in cv_data:
        cv_data[section_type] = []
    cv_data[section_type].append(entry)

    existing_skills = json.loads(profile["skills"]) if profile["skills"] else []
    merged = list(dict.fromkeys(existing_skills + new_skills))
    xp_gain = min(len(new_skills) * 15 + 10, 60)

    quests = generate_quests(conn, uid)

    conn.execute(
        """UPDATE player_profiles SET
            cv_data = ?, skills = ?, quests = ?, xp = xp + ?, last_login = datetime('now')
        WHERE user_id = ?""",
        (json.dumps(cv_data), json.dumps(merged), json.dumps(quests), xp_gain, uid),
    )
    conn.commit()
    level_up = check_level_up(conn, uid)
    conn.close()

    return jsonify({
        "success": True,
        "section_type": section_type,
        "entry": entry,
        "skills": new_skills,
        "merged_skills": merged,
        "xp_gained": xp_gain,
        "leveled_up": level_up["leveled_up"],
        "levels_gained": level_up["levels_gained"],
        "new_level": level_up["new_level"],
    })

# ── Quest completion ──

@app.route("/quest/complete/<quest_id>", methods=["POST"])
@login_required
def quest_complete(quest_id):
    uid = session["user_id"]
    proof = request.form.get("proof", "").strip()
    proof_url = request.form.get("proof_url", "").strip()
    if not proof:
        return jsonify({"success": False, "error": "Proof of work is required"}), 400

    conn = get_db()
    success, msg, xp_gain = complete_quest(conn, uid, quest_id, proof, proof_url)
    if success:
        level_up = check_level_up(conn, uid)
    else:
        conn.close()
        return jsonify({"success": False, "error": msg}), 400
    conn.close()

    return jsonify({
        "success": True,
        "message": msg,
        "xp_gained": xp_gain,
        "leveled_up": level_up["leveled_up"],
        "levels_gained": level_up["levels_gained"],
        "new_level": level_up["new_level"],
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
