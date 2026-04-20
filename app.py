import math
import json
import random
import re
import sqlite3
import hashlib
from urllib.parse import quote_plus
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Emotion Flow Analyzer",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


EMOTION_META = {
    "joy": {"emoji": "😊", "color": "#f4b400", "matplotlib": "#d89b00"},
    "sadness": {"emoji": "😢", "color": "#4a90e2", "matplotlib": "#2f6db2"},
    "anger": {"emoji": "😠", "color": "#e74c3c", "matplotlib": "#c0392b"},
    "fear": {"emoji": "😨", "color": "#7b61ff", "matplotlib": "#6246ea"},
    "love": {"emoji": "😍", "color": "#ff5c8a", "matplotlib": "#d9486f"},
    "surprise": {"emoji": "😲", "color": "#ff8c42", "matplotlib": "#db6b1d"},
    "trust": {"emoji": "🤝", "color": "#14b8a6", "matplotlib": "#0f9488"},
    "anticipation": {"emoji": "⏳", "color": "#f97316", "matplotlib": "#ea580c"},
    "disgust": {"emoji": "🤢", "color": "#65a30d", "matplotlib": "#4d7c0f"},
    "confusion": {"emoji": "😕", "color": "#6366f1", "matplotlib": "#4f46e5"},
    "calm": {"emoji": "😌", "color": "#0ea5e9", "matplotlib": "#0284c7"},
    "neutral": {"emoji": "😐", "color": "#64748b", "matplotlib": "#475569"},
}

EXAMPLES = {
    "Balanced shift": (
        "I was thrilled to get the opportunity. The first day felt exciting and full of promise. "
        "Then the workload became confusing and stressful. By the evening I felt frustrated and tired. "
        "After talking with my team, I felt calmer and hopeful again."
    ),
    "Low mood": (
        "The house feels quiet now. I keep thinking about what changed. "
        "It hurts more than I expected. Still, I am trying to stay patient with myself."
    ),
    "High tension": (
        "I worked hard for weeks. Then the meeting went badly. Nobody listened to the data. "
        "I felt angry and embarrassed. Later I was shocked when they asked me to fix everything."
    ),
}
CALMING_VIDEO_LINKS = {
    "Guided Breathing": "https://www.youtube.com/watch?v=LiUnFJ8P4gM",
    "Nature Minute": "https://www.youtube.com/watch?v=nqye02H_H6I",
    "Ocean Relaxation": "https://www.youtube.com/watch?v=vTtbr6vpfrQ&list=RDvTtbr6vpfrQ&start_radio=1",
    "Quiet Lofi Music": "https://www.youtube.com/watch?v=zuCRSwWssVk",
    "Rain Ambience": "https://www.youtube.com/watch?v=zF-__3RANT4",
    "Forest Relaxation": "https://www.youtube.com/watch?v=VNu15Qqomt8",
    "Waterfall Calm": "https://www.youtube.com/watch?v=lE6RYpe9IT0&list=RDlE6RYpe9IT0&start_radio=1",
    "Peaceful Piano": "https://www.youtube.com/watch?v=WK7LqjCnNVo",
    "Deep Relaxation": "https://www.youtube.com/watch?v=BHACKCNDMW8&list=RDBHACKCNDMW8&start_radio=1",
}
FEATURED_CALMING_VIDEOS = [
    "https://www.youtube.com/watch?v=JnWV92q77Mg&list=RDJnWV92q77Mg&start_radio=1",
    "https://www.youtube.com/shorts/kOgY5DRPdWI",
    "https://www.youtube.com/watch?v=BHACKCNDMW8&list=RDBHACKCNDMW8&start_radio=1&t=46s",
    "https://www.youtube.com/watch?v=ezTAhDES8bQ",
    "https://www.youtube.com/watch?v=ztVV54sPOns&list=RDztVV54sPOns&start_radio=1",
    "https://www.youtube.com/shorts/qlVBG20NGEU",
    "https://www.youtube.com/shorts/MNv7upxu3cU",
    "https://www.youtube.com/watch?v=eKbfUtLoQwE&list=RDeKbfUtLoQwE&start_radio=1",
]
SUPPORTIVE_SPEECH_VIDEOS = [
    {
        "title": "Guided Reassurance Video",
        "embed": "https://www.youtube.com/embed/aXItOY0sLRY?loop=1&playlist=aXItOY0sLRY",
        "link": "https://www.youtube.com/watch?v=pJWY3Bkkaew",
    },
    {
        "title": "Motivational Recovery Talk",
        "embed": "https://www.youtube.com/embed/s1iG2N2q7JU?loop=1&playlist=s1iG2N2q7JU",
        "link": "https://www.youtube.com/watch?v=UrfpkvvRTns",
    },
    {
        "title": "Short Self-Compassion Talk",
        "embed": "https://www.youtube.com/embed/cgBVUfEGFFA?loop=1&playlist=cgBVUfEGFFA",
        "link": "https://www.youtube.com/watch?v=vU1-S3LgzC0&t=318s",
    },
    {
        "title": "Breathing Through Hard Moments",
        "embed": "https://www.youtube.com/embed/inpok4MKVLM?loop=1&playlist=inpok4MKVLM",
        "link": "https://www.youtube.com/watch?v=DbDoBzGY3vo",
    },
    {
        "title": "Gentle Reset Talk",
        "embed": "https://www.youtube.com/embed/2OEL4P1Rz04?loop=1&playlist=2OEL4P1Rz04",
        "link": "https://www.youtube.com/watch?v=LkdAm3KNV3w",
    },
    {
        "title": "Supportive Reflection Video",
        "embed": "https://www.youtube.com/embed/cgBVUfEGFFA?loop=1&playlist=cgBVUfEGFFA",
        "link": "https://www.youtube.com/shorts/_jp5Xso-rbE",
    },
]
POSITIVE_QUOTES = [
    "I am here for you.",
    "This feeling can change, even if it feels intense right now.",
    "You do not have to handle this moment alone.",
    "Getting through the next few minutes is enough for now.",
    "Reaching out for help is a strong and meaningful step.",
    "There are still paths forward, even if you cannot see them clearly yet.",
]
SUPPORT_BOT_OPENERS = [
    "I'm here with you. You can tell me what feels heaviest right now, and we can slow it down together.",
    "Thank you for being honest with me. We do not have to solve everything at once.",
    "You do not need to explain this perfectly. Start anywhere, and I will stay with you.",
]
DB_PATH = Path(__file__).with_name("emotion_flow.db")

POSITIVE_EMOTIONS = {"joy", "love", "surprise", "trust", "anticipation", "calm"}
NEGATIVE_EMOTIONS = {"sadness", "anger", "fear", "disgust", "confusion"}
STABLE_EMOTIONS = {"neutral", "calm", "trust"}
TOKEN_PATTERN = re.compile(r"[A-Za-z']+")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
INTENSIFIERS = {
    "very": 0.35,
    "really": 0.35,
    "extremely": 0.55,
    "so": 0.25,
    "too": 0.2,
    "deeply": 0.45,
    "incredibly": 0.5,
    "quite": 0.2,
    "totally": 0.45,
}
NEGATIONS = {"not", "never", "no", "hardly", "barely", "without"}
DIRECT_RISK_TERMS = {
    "suicide",
    "self-harm",
    "harm myself",
    "want to die",
    "don't want to live",
    "dont want to live",
    "end my life",
    "kill myself",
}
VIOLENCE_TERMS = {
    "kill",
    "murder",
    "stab",
    "shoot",
    "die",
    "death",
}
PERSON_CONTEXT_TERMS = {
    "myself",
    "self",
    "him",
    "her",
    "them",
    "someone",
    "person",
    "people",
    "friend",
    "family",
    "me",
}
EMOTION_LEXICON = {
    "joy": {
        "happy", "happiness", "joy", "joyful", "glad", "excited", "excitement", "proud", "relieved", "hopeful", "calm",
        "bright", "delighted", "cheerful", "great", "good", "amazing", "success",
        "successful", "confidence", "confident", "optimistic", "smile", "smiled", "brighter",
        "wonderful", "fun", "laugh", "birthday",
    },
    "sadness": {
        "sad", "sadness", "empty", "lonely", "hurt", "cry", "cried", "grief", "down",
        "disappointed", "disappointment", "tired", "miserable", "upset", "lost", "lose", "miss", "quiet",
        "pain", "sorrow", "hopeless", "regret", "heartbroken", "sick", "ill",
    },
    "anger": {
        "angry", "anger", "furious", "frustrated", "frustration", "annoyed", "mad", "unfair", "unfairness", "rage",
        "irritated", "resentful", "blame", "fight", "hostile", "offended", "hate",
        "argument", "shouting", "outraged", "bitter", "ignored", "fooled",
    },
    "fear": {
        "afraid", "fear", "fearful", "scared", "nervous", "worried", "worry", "anxious", "stressful",
        "stressed", "tense", "panic", "uncertain", "unsafe", "hesitant", "dread",
        "overwhelmed", "pressure", "risk", "concerned", "concern", "confusing", "racing", "lose",
    },
    "love": {
        "love", "caring", "affection", "adore", "cherish", "warm", "close",
        "grateful", "thankful", "support", "supported", "kind", "trust", "bond",
        "comfort", "gentle", "compassion", "appreciate", "appreciated", "hugged", "hug",
    },
    "surprise": {
        "surprised", "surprise", "shocked", "wow", "unexpected", "suddenly", "astonished",
        "amazed", "startled", "stunned", "curious", "unbelievable", "abruptly",
        "sudden", "discovered", "reveal", "revealed", "prank",
    },
    "trust": {
        "trust", "trusted", "safe", "secure", "steady", "reliable", "assured",
        "faith", "believe", "believed", "dependable", "supported", "protected",
        "comfortable", "certain", "accepted",
    },
    "anticipation": {
        "anticipate", "anticipation", "expect", "expected", "await", "awaiting",
        "ready", "prepared", "planning", "upcoming", "soon", "eager", "curious",
        "looking", "forward", "prospect",
    },
    "disgust": {
        "disgust", "disgusted", "gross", "awful", "nasty", "revolting", "sickening",
        "dirty", "toxic", "horrible", "repulsive", "unpleasant", "terrible",
        "ashamed", "embarrassed",
    },
    "confusion": {
        "confused", "confusion", "unclear", "puzzled", "unsure", "mixed", "lost",
        "questioning", "wondering", "uncertain", "complex", "doubt", "doubtful",
        "misunderstood", "misleading",
    },
    "calm": {
        "calm", "peaceful", "relaxed", "steady", "settled", "quiet", "still",
        "content", "balanced", "gentle", "stable", "comfortable", "rested", "fine",
    },
    "neutral": {
        "okay", "normal", "average", "regular", "neutral", "standard", "plain",
        "routine", "usual", "moderate", "general", "simple",
    },
}
PHRASE_BOOSTS = {
    "joy": {
        "pure joy": 3.0,
        "so happy": 2.4,
        "heart leaped": 2.2,
        "could barely speak": 1.2,
        "wonderful person": 1.5,
    },
    "sadness": {
        "deep sadness": 3.2,
        "turned to deep sadness": 3.6,
        "been sick": 2.6,
        "months apart": 1.2,
    },
    "anger": {
        "wave of anger": 3.0,
        "unfairness of it all": 3.2,
        "easily i had been fooled": 2.4,
    },
    "fear": {
        "fear gripped me": 3.4,
        "what if": 2.4,
        "lose her": 3.0,
        "mind started racing": 2.6,
        "racing with worry": 3.2,
    },
    "surprise": {
        "standing right there": 2.0,
        "played a prank": 2.8,
        "surprise me": 2.4,
        "mix of surprise": 3.0,
    },
    "confusion": {
        "utter confusion": 3.4,
        "unable to process": 3.0,
        "didn't know whether": 2.8,
        "how could this be happening": 2.4,
    },
    "love": {
        "nothing but pure love": 3.4,
        "she hugged me": 2.4,
    },
    "calm": {
        "sense of calm": 3.0,
        "wash over me": 1.4,
        "peaceful and content": 3.2,
    },
    "disgust": {
        "felt disgust": 3.4,
        "disgust at how easily": 3.2,
    },
    "anticipation": {
        "felt anticipation": 3.0,
        "all the fun we would have together": 2.2,
        "this week": 0.8,
    },
    "trust": {
        "trusted that everything happens for a reason": 3.8,
        "for a reason": 1.8,
    },
}


@st.cache_resource
def get_emotion_lexicon():
    return EMOTION_LEXICON


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@st.cache_resource
def init_database() -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            input_text TEXT NOT NULL,
            dominant_emotion TEXT NOT NULL,
            emoji_sequence TEXT NOT NULL,
            trend TEXT NOT NULL,
            emotion_range INTEGER NOT NULL,
            volatility TEXT NOT NULL,
            transitions_count INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            step_no INTEGER NOT NULL,
            emotion TEXT NOT NULL,
            confidence REAL NOT NULL,
            sentence_text TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS safety_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            input_text TEXT NOT NULL,
            detected_terms TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    columns = [row[1] for row in cur.execute("PRAGMA table_info(analyses)").fetchall()]
    if "user_id" not in columns:
        cur.execute("ALTER TABLE analyses ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    alert_columns = [row[1] for row in cur.execute("PRAGMA table_info(safety_alerts)").fetchall()]
    if "user_id" not in alert_columns:
        cur.execute("ALTER TABLE safety_alerts ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()
    return str(DB_PATH)


def create_user(username: str, password: str) -> tuple[bool, str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (username.strip(), hash_password(password), pd.Timestamp.now().isoformat()),
        )
        conn.commit()
        return True, "Account created successfully. You can log in now."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Choose another username."
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        """
        SELECT id, username
        FROM users
        WHERE username = ? AND password_hash = ?
        """,
        (username.strip(), hash_password(password)),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_analysis_to_db(user_id: int, text: str, results: List[Dict], fingerprint: Dict[str, str]) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    dominant_emotion = Counter(item["dominant_emotion"] for item in results).most_common(1)[0][0]
    transitions_count = len(detect_transitions(results))
    cur.execute(
        """
        INSERT INTO analyses (
            user_id, created_at, input_text, dominant_emotion, emoji_sequence, trend,
            emotion_range, volatility, transitions_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            pd.Timestamp.now().isoformat(),
            text,
            dominant_emotion,
            fingerprint["emoji_sequence"],
            fingerprint["trend"],
            int(fingerprint["range_value"]),
            fingerprint["volatility"],
            transitions_count,
        ),
    )
    analysis_id = cur.lastrowid
    cur.executemany(
        """
        INSERT INTO analysis_steps (
            analysis_id, step_no, emotion, confidence, sentence_text
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                analysis_id,
                item["sentence_no"],
                item["dominant_emotion"],
                item["confidence"],
                item["sentence"],
            )
            for item in results
        ],
    )
    conn.commit()
    conn.close()


def save_safety_alert_to_db(user_id: int, text: str, detected_terms: List[str]) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO safety_alerts (user_id, created_at, input_text, detected_terms)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            pd.Timestamp.now().isoformat(),
            text,
            ", ".join(detected_terms),
        ),
    )
    conn.commit()
    conn.close()


def fetch_recent_analyses(user_id: int, limit: int = 5) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT created_at, dominant_emotion, emoji_sequence, trend, transitions_count
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_all_analyses(user_id: int) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT id, created_at, input_text, dominant_emotion, emoji_sequence, trend,
               emotion_range, volatility, transitions_count
        FROM analyses
        WHERE user_id = ?
        ORDER BY id DESC
        """
    , (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_analysis_steps(analysis_id: int) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT step_no, emotion, confidence, sentence_text
        FROM analysis_steps
        WHERE analysis_id = ?
        ORDER BY step_no ASC
        """,
        (analysis_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def render_saved_reports_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("View All Saved Reports")
    all_reports = fetch_all_analyses(st.session_state.user["id"])
    if not all_reports:
        st.info("No saved reports yet. Run an analysis first to store reports in the database.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    summary_df = pd.DataFrame(
        [
            {
                "Saved At": report["created_at"],
                "Dominant Emotion": report["dominant_emotion"].title(),
                "Transitions": report["transitions_count"],
            }
            for report in all_reports
        ]
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    for report in all_reports:
        title = (
            f"Report #{report['id']} - {report['dominant_emotion'].title()} - "
            f"{pd.Timestamp(report['created_at']).strftime('%Y-%m-%d %H:%M')}"
        )
        with st.expander(title, expanded=False):
            st.markdown(f"**Emoji Sequence:** `{report['emoji_sequence']}`")
            st.markdown(f"**Trend:** `{report['trend']}`")
            st.markdown(f"**Emotion Range:** `{report['emotion_range']}`")
            st.markdown(f"**Volatility:** `{report['volatility']}`")
            st.markdown(f"**Transitions:** `{report['transitions_count']}`")
            st.markdown("**Input Text Preview:**")
            st.write(report["input_text"])

            steps = fetch_analysis_steps(report["id"])
            if steps:
                steps_df = pd.DataFrame(
                    [
                        {
                            "Step": step["step_no"],
                            "Emotion": step["emotion"].title(),
                            "Confidence (%)": round(step["confidence"] * 100, 1),
                            "Text": step["sentence_text"],
                        }
                        for step in steps
                    ]
                )
                st.markdown("**Step Details:**")
                st.dataframe(steps_df, use_container_width=True, hide_index=True)


def logout_user():
    st.session_state.user = None
    st.session_state.active_menu = "Chat"
    st.session_state.safety_alert_active = False
    st.session_state.safety_alert_matches = []
    st.session_state.analysis_results = None
    st.session_state.analysis_frequency = None
    st.session_state.analysis_fingerprint = None
    st.session_state.analysis_text = ""


def render_auth_screen():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Login or Register")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_clicked = st.form_submit_button("Login", use_container_width=True, type="primary")
        if login_clicked:
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.session_state.active_menu = "Chat"
                st.success(f"Welcome, {user['username']}.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with register_tab:
        with st.form("register_form", clear_on_submit=False):
            new_username = st.text_input("Choose Username", key="register_username")
            new_password = st.text_input("Choose Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm")
            register_clicked = st.form_submit_button("Create Account", use_container_width=True, type="primary")
        if register_clicked:
            if not new_username.strip() or not new_password:
                st.error("Username and password are required.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                ok, message = create_user(new_username, new_password)
                if ok:
                    st.success(message)
                else:
                    st.error(message)
    st.markdown("</div>", unsafe_allow_html=True)


def inject_styles():
    st.markdown(
        """
        <style>
            html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
                background:
                    radial-gradient(circle at top left, rgba(255, 199, 95, 0.35), transparent 32%),
                    radial-gradient(circle at top right, rgba(123, 97, 255, 0.26), transparent 28%),
                    linear-gradient(135deg, #0f172a 0%, #14304c 45%, #1d4a63 100%) !important;
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(255, 199, 95, 0.35), transparent 32%),
                    radial-gradient(circle at top right, rgba(123, 97, 255, 0.26), transparent 28%),
                    linear-gradient(135deg, #0f172a 0%, #14304c 45%, #1d4a63 100%) !important;
                background-attachment: fixed;
                color: #0f172a;
            }
            .block-container {
                padding-top: 1.4rem;
                padding-bottom: 2.2rem;
                max-width: 1120px;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            [data-testid="stSidebar"][aria-expanded="true"] ~ [data-testid="stAppViewContainer"] .block-container,
            [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stAppViewContainer"] .block-container {
                margin-left: auto !important;
                margin-right: auto !important;
            }
            [data-testid="stSidebar"] {
                min-width: 280px !important;
                max-width: 280px !important;
                background: #0a0f17 !important;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }
            [data-testid="stSidebar"][aria-expanded="false"] {
                min-width: 0 !important;
                max-width: 0 !important;
                width: 0 !important;
                overflow: hidden !important;
                border-right: none !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                background: #0a0f17 !important;
            }
            [data-testid="stSidebar"] .block-container {
                padding-top: 0.45rem;
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            .nav-brand {
                color: #f8fafc;
                font-size: 1rem;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin: 0.4rem 0 0.85rem 0.35rem;
            }
            .sidebar-menu [data-testid="stRadio"] > div {
                gap: 0.85rem;
            }
            .sidebar-menu [data-testid="stRadio"] label {
                background: #ffffff !important;
                border: 1px solid rgba(15, 23, 42, 0.10) !important;
                border-radius: 20px !important;
                min-height: 3.35rem !important;
                padding: 0.95rem 1rem !important;
                align-items: center !important;
                margin: 0 !important;
            }
            .sidebar-menu [data-testid="stRadio"] label:hover {
                background: #f8fafc !important;
            }
            .sidebar-menu [data-testid="stRadio"] label p,
            .sidebar-menu [data-testid="stRadio"] label span,
            .sidebar-menu [data-testid="stRadio"] label div {
                color: #000000 !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #000000 !important;
                font-weight: 700 !important;
            }
            .sidebar-menu [data-testid="stRadio"] input:checked + div,
            .sidebar-menu [data-testid="stRadio"] input:checked + div p,
            .sidebar-menu [data-testid="stRadio"] input:checked + div span {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            [data-testid="stSidebar"] hr {
                border-color: rgba(255, 255, 255, 0.08) !important;
            }
            .hero {
                padding: 0.8rem 0 1.4rem 0;
                text-align: left;
            }
            .hero h1 {
                color: #f8fafc;
                font-size: 3.2rem;
                margin-bottom: 0.35rem;
                letter-spacing: -0.04em;
                font-weight: 900;
            }
            .hero-copy {
                color: rgba(248, 250, 252, 0.88);
                font-size: 1.02rem;
                max-width: 760px;
                line-height: 1.6;
            }
            .glass-card {
                background: #ffffff;
                border: 1px solid #dbe4ee;
                border-radius: 24px;
                padding: 1.4rem;
                box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
                margin-bottom: 1.2rem;
            }
            .metric-pill {
                background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
                border: 1px solid #dbe4ee;
                border-radius: 20px;
                padding: 1rem;
                min-height: 118px;
                text-align: center;
            }
            .metric-label {
                color: #475569;
                font-size: 0.92rem;
                font-weight: 600;
            }
            .metric-value {
                color: #0f172a;
                font-size: 1.7rem;
                font-weight: 800;
                margin-top: 0.35rem;
            }
            .timeline-box {
                overflow-x: auto;
                white-space: nowrap;
                padding-bottom: 0.3rem;
            }
            .timeline-step {
                display: inline-flex;
                align-items: center;
                margin-right: 0.35rem;
            }
            .emoji-node {
                display: inline-flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-width: 96px;
                padding: 0.7rem;
                border-radius: 20px;
                background: #ffffff;
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
            }
            .emoji-label {
                margin-top: 0.35rem;
                color: #1e293b;
                font-size: 0.84rem;
                font-weight: 700;
            }
            .emoji-confidence {
                color: #475569;
                font-size: 0.79rem;
                font-weight: 600;
            }
            .timeline-arrow {
                color: #000000;
                font-size: 1.9rem;
                font-weight: 900;
                padding: 0 0.25rem;
            }
            .fingerprint {
                border-radius: 20px;
                padding: 1rem 1.15rem;
                background: linear-gradient(180deg, #fff8eb 0%, #f8fbff 100%);
                border: 1px solid #dbe4ee;
                color: #0f172a;
            }
            .fingerprint,
            .fingerprint div,
            .fingerprint strong,
            .fingerprint span {
                color: #000000 !important;
            }
            .fingerprint-sequence {
                font-size: 1.8rem;
                margin-bottom: 0.55rem;
            }
            .trend-chip {
                display: inline-block;
                margin-top: 0.6rem;
                padding: 0.42rem 0.8rem;
                border-radius: 999px;
                color: white;
                font-weight: 700;
            }
            .transition-row {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                flex-wrap: wrap;
                background: #f8fafc;
                border: 1px solid #dbe4ee;
                border-radius: 18px;
                padding: 0.85rem 1rem;
                margin-bottom: 0.75rem;
                color: #0f172a;
            }
            .transition-badge {
                color: white;
                border-radius: 999px;
                padding: 0.35rem 0.75rem;
                font-weight: 700;
                font-size: 0.9rem;
            }
            .footer {
                text-align: center;
                color: rgba(248, 250, 252, 0.82);
                padding: 1rem 0 0.5rem 0;
            }
            .breathing-wrap {
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                gap: 0.75rem;
                background: #f8fafc;
                border-radius: 22px;
                padding: 1.5rem 1rem;
                margin: 1rem 0;
                border: 1px solid #dbe4ee;
            }
            .breathing-circle {
                width: 120px;
                height: 120px;
                border-radius: 999px;
                background: radial-gradient(circle at 30% 30%, #38bdf8, #2563eb);
                box-shadow: 0 10px 40px rgba(37, 99, 235, 0.28);
                animation: breathe 6s ease-in-out infinite;
            }
            .breathing-text {
                color: #0f172a;
                font-weight: 700;
                text-align: center;
            }
            .support-heading {
                color: #f8fafc;
                font-size: 2rem;
                font-weight: 800;
                margin: 1rem 0 0.75rem 0;
            }
            .support-copy {
                color: rgba(248, 250, 252, 0.95);
                font-size: 1rem;
                line-height: 1.7;
                margin-bottom: 0.8rem;
            }
            .support-chat-note {
                color: #f8fafc;
                font-size: 0.98rem;
                line-height: 1.6;
                margin: 0.15rem 0 1rem 0;
                font-weight: 500;
            }
            .support-chat-bubble {
                border-radius: 16px;
                padding: 0.75rem 0.85rem;
                margin-bottom: 0.65rem;
                line-height: 1.55;
                font-size: 0.95rem;
            }
            .support-chat-bubble.assistant {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #f8fafc;
            }
            .support-chat-bubble.user {
                background: rgba(59, 130, 246, 0.18);
                border: 1px solid rgba(96, 165, 250, 0.22);
                color: #f8fafc;
            }
            .support-chat-sidebar-box {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 22px;
                padding: 1rem;
            }
            .support-chat-panel-wrap {
                padding-top: 4.35rem;
            }
            .support-chat-sidebar-box .support-chat-note,
            .support-chat-sidebar-box .support-chat-bubble,
            .support-chat-sidebar-box .support-chat-bubble strong {
                color: #f8fafc !important;
            }
            .support-chat-sidebar-scroll {
                max-height: 34vh;
                overflow-y: auto;
                padding-right: 0.25rem;
                margin-bottom: 0.85rem;
            }
            .support-chat-header {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 0.35rem;
            }
            .support-chat-title {
                color: #ffffff;
                font-size: 1.05rem;
                font-weight: 800;
                line-height: 1.3;
            }
            div[data-testid="stElementContainer"]:has(.floating-chat-launcher-anchor) {
                position: fixed;
                right: 1.4rem;
                bottom: 1.4rem;
                width: 92px;
                z-index: 999;
                padding: 0 !important;
                margin: 0 !important;
                background: transparent !important;
            }
            div[data-testid="stElementContainer"]:has(.floating-chat-launcher-anchor) div[data-testid="stButton"] > button {
                width: 82px !important;
                height: 82px !important;
                min-height: 82px !important;
                border-radius: 24px !important;
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
                border: 1px solid rgba(255, 255, 255, 0.18) !important;
                box-shadow: 0 18px 32px rgba(34, 197, 94, 0.30) !important;
                color: #ffffff !important;
                font-size: 2rem !important;
                font-weight: 800 !important;
            }
            div[data-testid="stElementContainer"]:has(.floating-chat-panel-anchor) {
                position: fixed;
                right: 0.9rem;
                top: 5.2rem;
                bottom: 1rem;
                width: 380px;
                max-width: calc(100vw - 1.2rem);
                z-index: 999;
                background: rgba(10, 15, 23, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
                box-shadow: 0 24px 48px rgba(15, 23, 42, 0.38);
                padding: 1rem 1rem 0.75rem 1rem;
                backdrop-filter: blur(12px);
                display: flex;
                flex-direction: column;
            }
            .floating-chat-title {
                color: #ffffff;
                font-size: 1.05rem;
                font-weight: 800;
                margin-bottom: 0.15rem;
            }
            .floating-chat-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
                margin-bottom: 0.6rem;
            }
            .floating-chat-scroll {
                flex: 1 1 auto;
                min-height: 180px;
                max-height: none;
                overflow-y: auto;
                padding-right: 0.2rem;
                margin-bottom: 0.75rem;
            }
            div[data-testid="stElementContainer"]:has(.floating-chat-panel-anchor) .support-chat-note,
            div[data-testid="stElementContainer"]:has(.floating-chat-panel-anchor) .support-chat-bubble,
            div[data-testid="stElementContainer"]:has(.floating-chat-panel-anchor) .support-chat-bubble strong,
            div[data-testid="stElementContainer"]:has(.floating-chat-panel-anchor) label {
                color: #f8fafc !important;
            }
            div[data-testid="stElementContainer"]:has(.floating-chat-panel-anchor) textarea {
                min-height: 88px !important;
            }
            .support-block {
                color: rgba(248, 250, 252, 0.96);
                line-height: 1.75;
            }
            .support-block strong {
                color: #ffffff;
            }
            .support-block code {
                color: #fef08a;
                background: rgba(15, 23, 42, 0.38);
                padding: 0.15rem 0.35rem;
                border-radius: 8px;
            }
            .media-card {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 22px;
                padding: 1rem;
                margin: 0.5rem 0 1rem 0;
                backdrop-filter: blur(10px);
            }
            .media-card div[data-testid="stButton"] > button {
                background: #ffffff !important;
                border: 1px solid #d1d5db !important;
                color: #000000 !important;
            }
            .media-card div[data-testid="stButton"] > button:hover {
                background: #f8fafc !important;
                border: 1px solid #cbd5e1 !important;
            }
            .media-card div[data-testid="stButton"] > button div,
            .media-card div[data-testid="stButton"] > button p,
            .media-card div[data-testid="stButton"] > button span,
            .media-card div[data-testid="stButton"] > button * {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                opacity: 1 !important;
                font-weight: 700 !important;
            }
            div[data-testid="stTextArea"] textarea {
                background: #ffffff !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 18px !important;
                font-size: 1rem !important;
            }
            div[data-testid="stTextArea"] textarea::placeholder {
                color: #64748b !important;
            }
            div[data-testid="stButton"] > button {
                border-radius: 16px !important;
                border: 1px solid #cbd5e1 !important;
                background: #ffffff !important;
                color: #0f172a !important;
                font-weight: 700 !important;
                box-shadow: none !important;
                opacity: 1 !important;
            }
            div[data-testid="stButton"] > button * {
                color: #0f172a !important;
                opacity: 1 !important;
            }
            div[data-testid="stButton"] > button[kind="primary"] {
                background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
                border: none !important;
            }
            div[data-testid="stButton"] > button[kind="primary"] * {
                color: #ffffff !important;
            }
            .media-card button[key="calm_video_button"],
            .media-card button[key="support_video_button"],
            .media-card button[key="calm_video_button"] *,
            .media-card button[key="support_video_button"] *,
            .media-card button[key="calm_video_button"] p,
            .media-card button[key="support_video_button"] p,
            .media-card button[key="calm_video_button"] span,
            .media-card button[key="support_video_button"] span {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                opacity: 1 !important;
            }
            [data-testid="stTabs"] button[role="tab"],
            [data-testid="stTabs"] button[role="tab"] *,
            [data-testid="stTabs"] button[role="tab"] p,
            [data-testid="stTabs"] button[role="tab"] span {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                opacity: 1 !important;
            }
            button[key="login_button"],
            button[key="register_button"],
            button[key="calm_video_button"],
            button[key="support_video_button"] {
                color: #0f172a !important;
            }
            button[key="login_button"] *,
            button[key="register_button"] *,
            button[key="calm_video_button"] *,
            button[key="support_video_button"] * {
                color: #0f172a !important;
                opacity: 1 !important;
            }
            div[data-testid="stMarkdownContainer"] h1,
            div[data-testid="stMarkdownContainer"] h2,
            div[data-testid="stMarkdownContainer"] h3,
            div[data-testid="stMarkdownContainer"] h4,
            div[data-testid="stMarkdownContainer"] p,
            div[data-testid="stMarkdownContainer"] li,
            div[data-testid="stMarkdownContainer"] strong,
            .stSubheader,
            .stCaption,
            label {
                color: #f8fafc !important;
            }
            div[data-baseweb="notification"] {
                border-radius: 18px !important;
                border: 1px solid #dbe4ee !important;
            }
            div[data-baseweb="notification"] * {
                color: #f8fafc !important;
            }
            div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
                color: #0f172a !important;
            }
            div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button * {
                color: #0f172a !important;
                opacity: 1 !important;
            }
            div[data-baseweb="notification"] svg {
                fill: currentColor !important;
            }
            div[data-testid="stInfo"] {
                background: rgba(14, 165, 233, 0.18) !important;
            }
            div[data-testid="stWarning"] {
                background: rgba(234, 179, 8, 0.22) !important;
            }
            div[data-testid="stError"] {
                background: rgba(244, 114, 182, 0.20) !important;
            }
            div[data-testid="stSuccess"] {
                background: rgba(34, 197, 94, 0.18) !important;
            }
            .glass-card div[data-testid="stMarkdownContainer"] h1,
            .glass-card div[data-testid="stMarkdownContainer"] h2,
            .glass-card div[data-testid="stMarkdownContainer"] h3,
            .glass-card div[data-testid="stMarkdownContainer"] h4,
            .glass-card div[data-testid="stMarkdownContainer"] p,
            .glass-card div[data-testid="stMarkdownContainer"] li,
            .glass-card .stSubheader,
            .glass-card label {
                color: #0f172a !important;
            }
            @keyframes breathe {
                0% { transform: scale(0.78); opacity: 0.72; }
                50% { transform: scale(1.08); opacity: 1; }
                100% { transform: scale(0.78); opacity: 0.72; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def prepare_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(text) if sentence.strip()]
    if len(sentences) == 1:
        sentences = [sentence.strip() for sentence in re.split(r"[.!?;\n]+", text) if sentence.strip()]
    return [sentence for sentence in sentences if len(sentence.split()) >= 2]


def detect_emergency_terms(text: str) -> List[str]:
    lowered = text.lower()
    matches = set()

    for term in DIRECT_RISK_TERMS:
        if term in lowered:
            matches.add(term)

    words = set(tokenize(lowered))
    violence_hits = words.intersection(VIOLENCE_TERMS)
    context_hits = words.intersection(PERSON_CONTEXT_TERMS)

    if violence_hits and context_hits:
        matches.update(violence_hits)

    return sorted(matches)


def next_positive_quote():
    st.session_state.quote_index = (st.session_state.quote_index + 1) % len(POSITIVE_QUOTES)

def next_calming_video():
    if len(FEATURED_CALMING_VIDEOS) <= 1:
        return
    choices = [idx for idx in range(len(FEATURED_CALMING_VIDEOS)) if idx != st.session_state.video_index]
    st.session_state.video_index = random.choice(choices)


def next_supportive_video():
    if len(SUPPORTIVE_SPEECH_VIDEOS) <= 1:
        return
    choices = [idx for idx in range(len(SUPPORTIVE_SPEECH_VIDEOS)) if idx != st.session_state.speech_index]
    st.session_state.speech_index = random.choice(choices)


def build_support_bot_reply(message: str) -> str:
    lowered = message.lower().strip()
    if not lowered:
        return "You can tell me anything you are feeling. I will listen gently and stay with you."
    high_risk_chat_terms = DIRECT_RISK_TERMS.union(
        {
            "do not want to live",
            "i want to die",
            "i dont want to live",
            "i don't want to live",
            "can't go on",
            "cant go on",
            "no reason to live",
        }
    )
    if any(term in lowered for term in high_risk_chat_terms):
        return (
            "I'm really sorry you're feeling this overwhelmed. I'm glad you told me directly. "
            "This sounds serious, and I want to respond carefully: please contact a trusted person right now and stay with someone if you can. "
            "If you are in India, you can call Tele-MANAS at 14416 or Kiran at 1800-599-0019 right away."
        )
    if any(word in lowered for word in {"alone", "lonely", "empty", "nobody"}):
        return (
            "That sounds painfully lonely. You should not have to carry this by yourself. "
            "If you can, message one trusted person right now and say, 'I need you with me for a bit.'"
        )
    if any(word in lowered for word in {"scared", "afraid", "panic", "anxious", "anxiety"}):
        return (
            "That sounds really overwhelming. Let's make this moment smaller. "
            "Try one slow breath in for 4 counts and out for 6 counts. "
            "We only need to get through the next minute, not the whole day."
        )
    if any(word in lowered for word in {"sad", "cry", "hurt", "pain", "down"}):
        return (
            "I'm really sorry you're hurting. You do not need to fix everything right now. "
            "Let's think about one very small next step that could help you feel a little safer or steadier."
        )
    if any(word in lowered for word in {"angry", "frustrated", "mad", "upset"}):
        return (
            "That makes sense. When feelings get this intense, your body can stay on high alert. "
            "If possible, pause for a minute, drink some water, and let your breathing slow down before doing anything else."
        )
    if any(word in lowered for word in {"tired", "exhausted", "done"}):
        return (
            "It sounds like you have been carrying too much for too long. Rest is allowed. "
            "Can you move somewhere quieter, sit down, and give yourself one small pause?"
        )
    return random.choice(
        [
            "Thank you for telling me. I know this may not be easy to say out loud, and I am glad you said it.",
            "I hear you. Let's keep this simple and gentle, and focus only on what helps right now.",
            "That sounds really hard. We can slow it down and take one small step at a time together.",
            "I'm with you. You do not have to carry the full weight of this moment all at once.",
        ]
    )


def ensure_support_chat_history():
    if "support_chat_history" not in st.session_state:
        st.session_state.support_chat_history = [
            {"role": "assistant", "content": random.choice(SUPPORT_BOT_OPENERS)}
        ]


def submit_support_chat_message():
    user_message = st.session_state.get("support_chat_sidebar_input", "").strip()
    if not user_message:
        return
    st.session_state.support_chat_history.append({"role": "user", "content": user_message})
    st.session_state.support_chat_history.append(
        {"role": "assistant", "content": build_support_bot_reply(user_message)}
    )
    st.session_state.support_chat_sidebar_input = ""


def render_support_chatbot_sidebar_panel():
    ensure_support_chat_history()
    if "support_chat_open" not in st.session_state:
        st.session_state.support_chat_open = False

    st.markdown('<div class="support-chat-panel-wrap">', unsafe_allow_html=True)
    st.markdown("### 🤖 Support Chatbot")
    if not st.session_state.support_chat_open:
        if st.button("💬 Open Chatbot", use_container_width=True, key="open_support_chatbot_sidebar"):
            st.session_state.support_chat_open = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="support-chat-sidebar-box">', unsafe_allow_html=True)
    st.markdown('<div class="support-chat-header">', unsafe_allow_html=True)
    top_col1, top_col2 = st.columns([4.5, 1])
    with top_col1:
        st.markdown('<div class="support-chat-title">🤝 Talk to Support Bot</div>', unsafe_allow_html=True)
    with top_col2:
        if st.button("✕", use_container_width=True, key="close_support_chatbot_sidebar"):
            st.session_state.support_chat_open = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="support-chat-note">This is a gentle support chat for emotional check-ins. It is not a replacement for professional help.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="support-chat-sidebar-scroll">', unsafe_allow_html=True)
    for item in st.session_state.support_chat_history:
        role_class = "assistant" if item["role"] == "assistant" else "user"
        label = "Support Bot" if item["role"] == "assistant" else "You"
        st.markdown(
            f"""
            <div class="support-chat-bubble {role_class}">
                <strong>{label}</strong><br>{item["content"]}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)
    st.text_area(
        "Share what you are feeling right now",
        key="support_chat_sidebar_input",
        height=110,
        placeholder="Type how you feel, and the support bot will respond gently...",
    )
    st.button("📨 Send Message", use_container_width=True, key="support_chat_send", on_click=submit_support_chat_message)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_safety_support(alert_matches: List[str]):
    st.error(
        "Emergency alert: high-risk language detected in the text "
        f"({', '.join(alert_matches)})."
    )
    st.warning("Emotion analysis has been paused because the text may indicate a safety risk.")
    st.markdown('<div class="support-heading">Safety Support</div>', unsafe_allow_html=True)
    st.markdown('<div class="support-copy">Take one calm minute before doing anything else. Focus on the video below and let your breathing slow down a little.</div>', unsafe_allow_html=True)
    support_tab, motivation_tab, quote_tab, help_tab = st.tabs(
        ["Support Videos", "Motivation Videos", "Positive Quotes", "Emergency Help"]
    )
    with support_tab:
        media_col1, media_col2 = st.columns(2)
        with media_col1:
            st.video(FEATURED_CALMING_VIDEOS[st.session_state.video_index])
            st.button("Next Support Video", use_container_width=True, on_click=next_calming_video, key="calm_video_button")
        with media_col2:
            st.markdown("**Quick links**")
            st.markdown(f"[Open guided breathing audio]({CALMING_VIDEO_LINKS['Guided Breathing']})")
            st.markdown(f"[Open 1-minute nature calm video]({CALMING_VIDEO_LINKS['Nature Minute']})")
            st.markdown(f"[Open ocean relaxation video]({CALMING_VIDEO_LINKS['Ocean Relaxation']})")
            st.markdown(f"[Open quiet lofi stream]({CALMING_VIDEO_LINKS['Quiet Lofi Music']})")
            st.markdown(f"[Open rain ambience]({CALMING_VIDEO_LINKS['Rain Ambience']})")
    with motivation_tab:
        current_speech = SUPPORTIVE_SPEECH_VIDEOS[st.session_state.speech_index]
        st.button("Next Motivation Video", use_container_width=True, on_click=next_supportive_video, key="support_video_button")
        st.markdown(
            f"""
            <iframe
                width="100%"
                height="320"
                src="{current_speech["embed"]}"
                title="{current_speech["title"]}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                referrerpolicy="strict-origin-when-cross-origin"
                allowfullscreen>
            </iframe>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f'[Open supportive video in YouTube]({current_speech["link"]})')
    with quote_tab:
        st.info(
            "I'm really sorry you're feeling like this. When someone uses language about ending life or serious harm, "
            "it often means something feels overwhelming right now, not that there are no other paths forward."
        )
        st.markdown(
            """
            <div class="breathing-wrap">
                <div class="breathing-circle"></div>
                <div class="breathing-text">Breathe with the circle.<br>Slow inhale as it grows, slow exhale as it gets smaller.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.success(
            "You matter, this moment can change, and reaching out right now is a strong step."
        )
        st.markdown(
            '**Try this instead:** `I am overwhelmed right now, but I want help and I want things to get better.`'
        )
        quote_col1, quote_col2 = st.columns([1, 2])
        with quote_col1:
            st.button("Show another positive quote", use_container_width=True, on_click=next_positive_quote)
        with quote_col2:
            st.info(POSITIVE_QUOTES[st.session_state.quote_index])
        st.subheader("Gentle Distraction Ideas")
        music_col, video_col, book_col = st.columns(3)
        with music_col:
            st.markdown("**Music**")
            st.markdown("- Soft piano or instrumental music")
            st.markdown("- Nature sounds like rain or ocean waves")
            st.markdown("- Calm lo-fi beats")
            st.markdown("- Slow breathing or meditation audio")
        with video_col:
            st.markdown("**Calming Videos**")
            st.markdown("- Guided breathing video")
            st.markdown("- Ocean relaxation video")
            st.markdown("- Rain ambience video")
        with book_col:
            st.markdown("**Books**")
            st.markdown("- *The Comfort Book* by Matt Haig")
            st.markdown("- *The Boy, the Mole, the Fox and the Horse* by Charlie Mackesy")
            st.markdown("- A favorite book that feels familiar and safe")
            st.markdown("- Short poems or uplifting quotes")
    with help_tab:
        st.markdown("---")
        st.markdown(
            """
            <div class="support-block">
                <p><strong>Before anything else: are you safe right now?</strong></p>
                <p>If you feel at risk of acting on this, please reach out immediately to someone who can be with you or talk to you in real time.</p>
                <p><strong>If this reflects a real immediate danger:</strong></p>
                <ul>
                    <li>Call local emergency services now.</li>
                    <li>In India, call Tele-MANAS: <code>14416</code> or <code>1-800-891-4416</code>.</li>
                    <li>In India, call Kiran Mental Health Helpline: <code>1800-599-0019</code>.</li>
                    <li>In India, call AASRA 24/7: <code>022-27546669</code>.</li>
                    <li>Reach out to a trusted friend, family member, teacher, or colleague right now and tell them you need support.</li>
                </ul>
                <p><strong>If calling feels like too much, send this message:</strong> <code>I am not feeling safe right now. Can you stay with me or call me?</code></p>
                <p>You do not have to solve everything right now. Sometimes the goal is only to get through the next few minutes safely.</p>
                <p>Try one small step now: sit in a different room, drink some water, or take five slow breaths with a longer exhale than inhale.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption("If this is only demo text, the app stopped because it detected safety-related language.")


def build_support_page_url(alert_matches: List[str]) -> str:
    terms = quote_plus(",".join(alert_matches))
    return f"?page=support&terms={terms}"


def open_support_tab(alert_matches: List[str]) -> None:
    support_url = build_support_page_url(alert_matches)
    components.html(
        f"""
        <script>
            const supportUrl = "{support_url}";
            const parentWindow = window.parent;
            const pathname = parentWindow.location.pathname || "/";
            const fullUrl = `${{pathname}}${{supportUrl}}`;
            const opened = parentWindow.open(fullUrl, "_blank");
            if (!opened) {{
                const anchor = parentWindow.document.createElement("a");
                anchor.href = fullUrl;
                anchor.target = "_blank";
                anchor.rel = "noopener noreferrer";
                parentWindow.document.body.appendChild(anchor);
                anchor.click();
                anchor.remove();
            }}
        </script>
        """,
        height=0,
    )


def render_sidebar_navigation() -> str:
    with st.sidebar:
        st.markdown('<div class="nav-brand">✨ Menu</div>', unsafe_allow_html=True)
        current = st.session_state.get("active_menu", "Chat")
        label_map = {
            "💬 Chat": "Chat",
            "🕘 History": "History",
            "↪️ Logout": "Logout",
        }
        reverse_map = {value: key for key, value in label_map.items()}
        current_label = reverse_map.get(current, "💬 Chat")
        st.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)
        selected_label = st.radio(
            "Sidebar Menu",
            list(label_map.keys()),
            index=list(label_map.keys()).index(current_label),
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    return label_map[selected_label]


def tokenize(sentence: str) -> List[str]:
    return TOKEN_PATTERN.findall(sentence.lower())


def token_forms(token: str) -> set[str]:
    forms = {token}
    for suffix in ("ness", "ment", "tion", "sion", "ity", "ing", "ed", "ly", "s", "es"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            forms.add(token[: -len(suffix)])
    if token.endswith("ied") and len(token) > 4:
        forms.add(token[:-3] + "y")
    return forms


def score_sentence(sentence: str) -> List[Dict]:
    tokens = tokenize(sentence)
    scores = {emotion: 0.15 for emotion in EMOTION_META}
    matched_any = False
    lowered_sentence = sentence.lower()
    emotion_lexicon = get_emotion_lexicon()

    for idx, token in enumerate(tokens):
        forms = token_forms(token)
        for emotion, keywords in emotion_lexicon.items():
            if not forms.intersection(keywords):
                continue

            matched_any = True
            weight = 1.0
            prev_tokens = tokens[max(0, idx - 2):idx]

            for prev in prev_tokens:
                if prev in INTENSIFIERS:
                    weight += INTENSIFIERS[prev]
                if prev in NEGATIONS:
                    weight *= 0.35

            if token.endswith("ed") and emotion in {"sadness", "anger", "fear"}:
                weight += 0.15

            scores[emotion] += weight

    for emotion, phrases in PHRASE_BOOSTS.items():
        for phrase, boost in phrases.items():
            if phrase in lowered_sentence:
                matched_any = True
                scores[emotion] += boost

    if not matched_any:
        scores["neutral"] += 1.4
        if len(tokens) <= 5:
            scores["calm"] += 0.2

    if "?" in lowered_sentence:
        scores["confusion"] += 0.35
        scores["anticipation"] += 0.2
    if "!" in lowered_sentence:
        scores["surprise"] += 0.35
        scores["joy"] += 0.15

    if "but" in tokens:
        scores["confusion"] += 0.2
    if "healthy" in tokens:
        scores["joy"] += 0.8
        scores["calm"] += 0.4

    total = sum(scores.values())
    normalized = [
        {"label": emotion, "score": value / total}
        for emotion, value in scores.items()
    ]
    normalized.sort(key=lambda item: item["score"], reverse=True)
    return normalized


def analyze_text_by_sentence(text: str) -> Tuple[List[Dict], Counter]:
    """
    Analyze text sentence by sentence for emotional content.

    Args:
        text: Input text to analyze.

    Returns:
        A tuple containing:
        - a list of per-sentence emotion results
        - a Counter of dominant emotion frequencies
    """
    sentences = prepare_sentences(text)
    if not sentences:
        return [], Counter()

    sentence_results: List[Dict] = []
    frequency: Counter = Counter()

    for idx, sentence in enumerate(sentences, start=1):
        normalized_scores = score_sentence(sentence)
        dominant = normalized_scores[0]
        frequency[dominant["label"]] += 1
        sentence_results.append(
            {
                "sentence_no": idx,
                "sentence": sentence,
                "dominant_emotion": dominant["label"],
                "confidence": max(dominant["score"], 0.2),
                "top3": normalized_scores[:3],
            }
        )

    return sentence_results, frequency


@st.cache_data(show_spinner=False)
def analyze_text_cached(text: str) -> Tuple[List[Dict], Dict[str, int]]:
    results, frequency = analyze_text_by_sentence(text)
    return results, dict(frequency)


def safe_analyze_text(text: str) -> Tuple[List[Dict] | None, Counter | None]:
    try:
        results, frequency_dict = analyze_text_cached(text)
        frequency = Counter(frequency_dict)
        if not results:
            st.warning("Text too short for meaningful analysis. Please add more content.")
            return None, None
        return results, frequency
    except Exception as exc:
        st.error(f"Analysis error: {exc}")
        return None, None


def export_analysis_report(results: List[Dict], frequency: Counter, fingerprint: Dict[str, str]) -> str:
    report = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "fingerprint": fingerprint,
        "sentence_analysis": results,
        "emotion_frequencies": dict(frequency),
    }
    return json.dumps(report, indent=2)


def test_emotion_detection():
    test_cases = [
        ("I'm so happy and excited!", "joy"),
        ("I feel sad and lonely today.", "sadness"),
        ("This is incredibly frustrating!", "anger"),
    ]

    for text, expected in test_cases:
        results, _ = analyze_text_by_sentence(text)
        detected = results[0]["dominant_emotion"]
        assert detected == expected, f"Failed: {text}"


def detect_transitions(results: List[Dict]) -> List[Dict]:
    transitions: List[Dict] = []
    for current, nxt in zip(results, results[1:]):
        if current["dominant_emotion"] == nxt["dominant_emotion"]:
            continue
        confidence_delta = nxt["confidence"] - current["confidence"]
        shift_type = "positive" if nxt["dominant_emotion"] in POSITIVE_EMOTIONS else "negative"
        if current["dominant_emotion"] in NEGATIVE_EMOTIONS and nxt["dominant_emotion"] in POSITIVE_EMOTIONS:
            shift_type = "recovery"
        if current["dominant_emotion"] in POSITIVE_EMOTIONS and nxt["dominant_emotion"] in NEGATIVE_EMOTIONS:
            shift_type = "drop"
        if nxt["dominant_emotion"] in STABLE_EMOTIONS:
            shift_type = "stabilizing"
        if current["dominant_emotion"] in STABLE_EMOTIONS and nxt["dominant_emotion"] not in STABLE_EMOTIONS:
            shift_type = "emerging"
        transitions.append(
            {
                "from": current,
                "to": nxt,
                "confidence_delta": confidence_delta,
                "shift_type": shift_type,
            }
        )
    return transitions


def classify_trend(results: List[Dict]) -> str:
    if len(results) <= 1:
        return "Consistent"

    emotions = [item["dominant_emotion"] for item in results]
    if len(set(emotions)) == 1:
        return "Consistent"
    if emotions[0] in NEGATIVE_EMOTIONS and emotions[-1] in POSITIVE_EMOTIONS:
        return "Improving"
    if emotions[0] in POSITIVE_EMOTIONS and emotions[-1] in NEGATIVE_EMOTIONS:
        return "Worsening"
    return "Mixed"


def build_fingerprint(results: List[Dict], frequency: Counter) -> Dict[str, str]:
    if not results:
        return {
            "emoji_sequence": "",
            "top_summary": "",
            "path_summary": "",
            "trend": "Mixed",
            "range_value": "0",
            "volatility": "Low",
        }

    emoji_sequence = " ".join(EMOTION_META[item["dominant_emotion"]]["emoji"] for item in results)
    most_common = frequency.most_common()
    top_count = most_common[0][1]
    top_emotions = [emotion for emotion, count in most_common if count == top_count]
    top_summary = " / ".join(
        f"{EMOTION_META[emotion]['emoji']} {emotion.title()}" for emotion in top_emotions
    )
    transitions = detect_transitions(results)
    transition_count = len(transitions)
    path_summary = (
        f"{results[0]['dominant_emotion'].title()} → {results[-1]['dominant_emotion'].title()}"
    )

    if transition_count == 0:
        volatility = "Low"
    elif transition_count <= 2:
        volatility = "Medium"
    else:
        volatility = "High"

    return {
        "emoji_sequence": emoji_sequence,
        "top_summary": top_summary,
        "path_summary": path_summary,
        "trend": classify_trend(results),
        "range_value": str(len(frequency)),
        "volatility": volatility,
    }


def render_timeline(results: List[Dict]):
    html_parts = ['<div class="timeline-box">']
    for idx, item in enumerate(results):
        meta = EMOTION_META[item["dominant_emotion"]]
        font_size = 2.1 + (item["confidence"] * 2.4)
        html_parts.append(
            f"""
            <div class="timeline-step">
                <div class="emoji-node" style="border: 2px solid {meta['color']};">
                    <div style="font-size:{font_size:.2f}rem; line-height: 1;">{meta['emoji']}</div>
                    <div class="emoji-label">{item['dominant_emotion'].title()}</div>
                    <div class="emoji-confidence">{item['confidence'] * 100:.1f}% confidence</div>
                </div>
            """
        )
        if idx < len(results) - 1:
            html_parts.append('<div class="timeline-arrow">→</div>')
        html_parts.append("</div>")
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_transitions(results: List[Dict]):
    transitions = detect_transitions(results)
    if not transitions:
        st.success("No emotion shifts detected. The tone stayed steady across the full text.")
        return

    for transition in transitions:
        current = transition["from"]
        nxt = transition["to"]
        current_meta = EMOTION_META[current["dominant_emotion"]]
        next_meta = EMOTION_META[nxt["dominant_emotion"]]
        st.markdown(
            f"""
            <div class="transition-row">
                <strong>Emotion shift detected</strong>
                <span class="transition-badge" style="background:{current_meta['color']};">
                    {current_meta['emoji']} {current['dominant_emotion'].title()}
                </span>
                <span style="font-size:1.15rem;">→</span>
                <span class="transition-badge" style="background:{next_meta['color']};">
                    {next_meta['emoji']} {nxt['dominant_emotion'].title()}
                </span>
                <span><strong>Shift:</strong> {transition['shift_type'].title()}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_breakdown(results: List[Dict]):
    for item in results:
        meta = EMOTION_META[item["dominant_emotion"]]
        title = (
            f"Sentence {item['sentence_no']} {meta['emoji']} "
            f"{item['dominant_emotion'].title()} ({item['confidence'] * 100:.1f}%)"
        )
        with st.expander(title, expanded=False):
            st.markdown(f"**Original sentence:** {item['sentence']}")
            st.markdown(
                f"**Dominant emotion:** {meta['emoji']} `{item['dominant_emotion'].title()}` "
                f"at **{item['confidence'] * 100:.2f}%** confidence"
            )
            top3_df = pd.DataFrame(
                [
                    {
                        "Emotion": f"{EMOTION_META[row['label']]['emoji']} {row['label'].title()}",
                        "Confidence (%)": round(row["score"] * 100, 2),
                    }
                    for row in item["top3"]
                ]
            )
            st.dataframe(top3_df, use_container_width=True, hide_index=True)


def render_metrics(results: List[Dict], frequency: Counter):
    dominant_emotion = frequency.most_common(1)[0][0]
    avg_confidence = sum(item["confidence"] for item in results) / len(results)
    transition_count = len(detect_transitions(results))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Dominant Emotion</div>
                <div class="metric-value">{EMOTION_META[dominant_emotion]['emoji']} {dominant_emotion.title()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Average Confidence</div>
                <div class="metric-value">{avg_confidence * 100:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Emotion Shifts</div>
                <div class="metric-value">{transition_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Emotion Range</div>
                <div class="metric-value">{len(frequency)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    inject_styles()
    init_database()

    if "quote_index" not in st.session_state:
        st.session_state.quote_index = 0
    if "video_index" not in st.session_state:
        st.session_state.video_index = 0
    if "speech_index" not in st.session_state:
        st.session_state.speech_index = 0

    current_page = st.query_params.get("page", "chat")
    if current_page == "support":
        raw_terms = st.query_params.get("terms", "")
        alert_matches = [item.strip() for item in raw_terms.split(",") if item.strip()]
        main_col, side_col = st.columns([3.15, 1.2], gap="large")
        with main_col:
            st.markdown(
                """
                <div class="hero">
                    <h1>Safety Support Hub</h1>
                    <div class="hero-copy">
                        Support videos, motivation, positive quotes, and emergency help are all collected here.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_safety_support(alert_matches or ["high-risk language"])
        with side_col:
            render_support_chatbot_sidebar_panel()
        return

    st.markdown(
        """
        <div class="hero">
            <h1>Emotion Flow Analyzer</h1>
            <div class="hero-copy">
                Detect emotions in text, view emotional flow, and present the results with a cleaner visual story.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "user" not in st.session_state:
        st.session_state.user = None
    if st.session_state.user is None:
        render_auth_screen()
        st.markdown(
            """
            <div class="footer">
                
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if "active_menu" not in st.session_state:
        st.session_state.active_menu = "Chat"

    menu_choice = render_sidebar_navigation()
    st.session_state.active_menu = menu_choice

    if menu_choice == "Logout":
        logout_user()
        st.rerun()

    if menu_choice == "History":
        render_saved_reports_page()
        st.markdown(
            """
            <div class="footer">
                
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if "text_input" not in st.session_state:
        st.session_state.text_input = ""
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "analysis_frequency" not in st.session_state:
        st.session_state.analysis_frequency = None
    if "analysis_fingerprint" not in st.session_state:
        st.session_state.analysis_fingerprint = None
    if "analysis_text" not in st.session_state:
        st.session_state.analysis_text = ""
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    if "safety_alert_active" not in st.session_state:
        st.session_state.safety_alert_active = False
    if "safety_alert_matches" not in st.session_state:
        st.session_state.safety_alert_matches = []
    if "last_saved_signature" not in st.session_state:
        st.session_state.last_saved_signature = ""

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Enter Text")
    text_input = st.text_area(
        "Type or paste text",
        value=st.session_state.text_input,
        height=190,
        label_visibility="collapsed",
        placeholder=(
            "Example: I was nervous before the presentation. Then the room responded well. "
            "By the end, I felt relieved and proud."
        ),
    )

    st.markdown("#### Example Inputs")
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    with ex_col1:
        if st.button("Balanced shift", use_container_width=True):
            st.session_state.text_input = EXAMPLES["Balanced shift"]
            st.rerun()
    with ex_col2:
        if st.button("Low mood", use_container_width=True):
            st.session_state.text_input = EXAMPLES["Low mood"]
            st.rerun()
    with ex_col3:
        if st.button("High tension", use_container_width=True):
            st.session_state.text_input = EXAMPLES["High tension"]
            st.rerun()

    analyze_clicked = st.button("Analyze Emotions", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if analyze_clicked:
        st.session_state.text_input = text_input

        if not text_input.strip():
            st.error("Enter some text before running the analysis.")
            return

        alert_matches = detect_emergency_terms(text_input)
        if alert_matches:
            st.session_state.video_index = random.randrange(len(FEATURED_CALMING_VIDEOS))
            st.session_state.speech_index = random.randrange(len(SUPPORTIVE_SPEECH_VIDEOS))
            st.session_state.safety_alert_active = True
            st.session_state.safety_alert_matches = alert_matches
            st.session_state.analysis_results = None
            st.session_state.analysis_frequency = None
            st.session_state.analysis_fingerprint = None
            save_safety_alert_to_db(st.session_state.user["id"], text_input, alert_matches)
            open_support_tab(alert_matches)
            st.stop()
        st.session_state.safety_alert_active = False
        st.session_state.safety_alert_matches = []

        with st.spinner("Analyzing text emotions..."):
            results, frequency = safe_analyze_text(text_input)

        if not results or not frequency:
            st.warning("No valid text segments were found. Try entering longer text.")
            return

        fingerprint = build_fingerprint(results, frequency)
        st.session_state.analysis_results = results
        st.session_state.analysis_frequency = dict(frequency)
        st.session_state.analysis_fingerprint = fingerprint
        st.session_state.analysis_text = text_input
        st.session_state.analysis_history.append(
            {
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": (text_input[:100] + "...") if len(text_input) > 100 else text_input,
                "fingerprint": fingerprint,
            }
        )
        save_signature = f"{hash(text_input)}::{fingerprint['emoji_sequence']}"
        if st.session_state.last_saved_signature != save_signature:
            save_analysis_to_db(st.session_state.user["id"], text_input, results, fingerprint)
            st.session_state.last_saved_signature = save_signature

    elif st.session_state.safety_alert_active:
        render_safety_support(st.session_state.safety_alert_matches)
        st.stop()

    has_saved_analysis = (
        st.session_state.analysis_results
        and st.session_state.analysis_frequency
        and st.session_state.analysis_text == text_input
    )

    if has_saved_analysis:
        results = st.session_state.analysis_results
        frequency = Counter(st.session_state.analysis_frequency)

        confidence_threshold = 0.3

        filtered_results = [result for result in results if result["confidence"] >= confidence_threshold]
        if not filtered_results:
            st.warning("No emotions matched the selected confidence threshold. Lower the threshold to view results.")
            return

        filtered_frequency = Counter(result["dominant_emotion"] for result in filtered_results)
        filtered_fingerprint = build_fingerprint(filtered_results, filtered_frequency)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Overview")
        render_metrics(filtered_results, filtered_frequency)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Emoji Timeline")
        render_timeline(filtered_results)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Emotion Progress Table")
        journey_df = pd.DataFrame(
            [
                {
                    "Step": item["sentence_no"],
                    "Emotion": item["dominant_emotion"].title(),
                    "Confidence (%)": round(item["confidence"] * 100, 1),
                }
                for item in filtered_results
            ]
        )
        st.dataframe(journey_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Fingerprint Summary")
        st.markdown('<div class="fingerprint">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="fingerprint-sequence">{filtered_fingerprint["emoji_sequence"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Transition Detection")
        render_transitions(filtered_results)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="footer">
            
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
