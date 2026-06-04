import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lifequest.db")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS player_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            xp_to_next INTEGER DEFAULT 100,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            skills TEXT DEFAULT '[]',
            cv_data TEXT DEFAULT '{}',
            char_class TEXT DEFAULT 'Warrior',
            quests TEXT DEFAULT '[]',
            title TEXT DEFAULT 'Adventurer',
            avatar TEXT DEFAULT '',
            last_login TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            skill_required TEXT,
            xp_reward INTEGER DEFAULT 50,
            hp_cost INTEGER DEFAULT 10,
            boss_name TEXT DEFAULT 'Unknown',
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS bosses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            min_level INTEGER DEFAULT 1,
            hp INTEGER DEFAULT 50,
            xp_reward INTEGER DEFAULT 30,
            skill_requirements TEXT DEFAULT '[]',
            challenge_data TEXT DEFAULT '{}',
            FOREIGN KEY (event_id) REFERENCES events(id)
        );
        CREATE TABLE IF NOT EXISTS battle_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            boss_id INTEGER,
            won INTEGER DEFAULT 0,
            xp_gained INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES users(id),
            FOREIGN KEY (boss_id) REFERENCES bosses(id)
        );
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user) REFERENCES users(id),
            FOREIGN KEY (to_user) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()
