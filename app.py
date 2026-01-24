__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import json
import os
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. SYSTEM ARCHITECTURE & DATABASE LAYER (STRICT PERSISTENCE)
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Pakistani Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration Constants
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "advocate_ai_v9_stable.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_sql_db():
    """Constructs the relational database schema."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, username TEXT, password TEXT, joined_date TEXT)''')
    
    c.execute("PRAGMA table_info(users)")
    cols = [info[1] for info in c.fetchall()]
    if 'password' not in cols:
        c.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')

    c.execute('''CREATE TABLE IF NOT EXISTS cases 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS documents 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size TEXT, pages INTEGER, indexed TEXT)''')
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    """Handles new user onboarding."""
    if not email: return
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", 
              (email, username, password, datetime.datetime.now().strftime("%Y-%m-%d")))
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                  (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_check_login(email, password):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    """Saves a single message to the persistent history table."""
    if not email or not content: return
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def db_load_history(email, case_name):
    """Loads chat history for the active session."""
    if not email: return []
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT role, content FROM history 
                 JOIN cases ON history.case_id = cases.id 
                 WHERE cases.email=? AND cases.case_name=? 
                 ORDER BY history.id ASC''', (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

def db_get_docs():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, size, pages, indexed FROM documents")
    data = c.fetchall()
    conn.close()
    return data

def sync_data_folder():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    existing = [row[0] for row in c.execute("SELECT name FROM documents").fetchall()]
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith(".pdf") and filename not in existing:
                path = os.path.join(DATA_FOLDER, filename)
                try:
                    reader = PdfReader(path); pages = len(reader.pages)
                    size = f"{os.path.getsize(path) / 1024:.1f} KB"
                    c.execute("INSERT INTO documents (name, size, pages, indexed) VALUES (?, ?, ?, ?)", 
                              (filename, size, pages, "✅ Indexed"))
                except: continue
    conn.commit(); conn.close()

init_sql_db()
sync_data_folder()

# ==============================================================================
# 2. CORE UTILITY SERVICES (GEMINI AI & VOICE)
# ==============================================================================

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, temperature=0.2)

def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{safe_text}'); msg.lang = '{lang_code}'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

# ==============================================================================
# 3. GOOGLE OAUTH CONFIGURATION
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f: json.dump({"web": auth_config}, f)
    authenticator = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='alpha_apex_v9_cookie',
        cookie_key='secure_vault_2026_key',
        redirect_uri=auth_config['redirect_uris'][0],
    )
    authenticator.check_authentification()
except Exception as e:
    st.error(f"Auth Critical Failure: {e}"); st.stop()

# ==============================================================================
# 4. MAIN CONSULTATION INTERFACE (CHAMBERS)
# ==============================================================================

def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        lang_code = langs[st.selectbox("🌐 Selection Language", list(langs.keys()))]
        with st.expander("AI Tuning", expanded=True):
            sys_persona = st.text_input("Persona:", value="Expert Advocate")
            use_irac = st.toggle("Enforce IRAC", value=True)
        st.divider()
        conn = sqlite3.connect(SQL_DB_FILE)
        curr_user = st.session_state.get('user_email', "")
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (curr_user,)).fetchall()]
        conn.close()
        st.session_state.active_case = st.selectbox("Active Case", cases if cases else ["General"])
        if st.button("🚪 Logout Session"):
            authenticator.logout(); st.session_state.connected = False; st.rerun()

    st.header(f"💼 Chambers: {st.session_state.active_case}")

    # --- DISPLAY PERSISTENT HISTORY ---
    # We load history every time to ensure nothing disappears
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # --- CHAT INPUT HANDLING ---
    m_col, i_col = st.columns([1, 10])
    with m_col:
        voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col:
        text_in = st.chat_input("Enter legal facts or inquiry...")

    # Combine voice and text
    query = voice_in or text_in

    if query:
        # 1. IMMEDIATELY SAVE USER MSG TO DB
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        
        # 2. RENDER THE USER MESSAGE INSTANTLY
        with st.chat_message("user"):
            st.write(query)
        
        # 3. GENERATE AI RESPONSE
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Law..."):
                try:
                    irac_logic = "Apply IRAC: ISSUE, RULE, ANALYSIS, CONCLUSION." if use_irac else ""
                    full_p = f"{sys_persona}\n{irac_logic}\nClient Query: {query}"
                    
                    response = load_llm().invoke(full_p).content
                    st.markdown(response)
                    
                    # 4. SAVE ASSISTANT RESPONSE TO DB
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                    
                    # 5. VOICE OUTPUT
                    play_voice_js(response, lang_code)
                    
                    # 6. FORCE RERUN TO LOCK IN THE CONVERSATION
                    st.rerun()
                except Exception as e:
                    st.error(f"Consultation Failure: {e}")

# ==============================================================================
# 5. DOCUMENT LIBRARY & ABOUT
# ==============================================================================

def render_library():
    st.header("📚 Law Library")
    if st.button("🔄 Trigger Rescan"): sync_data_folder(); st.rerun()
    docs = db_get_docs()
    if docs:
        st.table(pd.DataFrame(docs, columns=["Name", "Size", "Pages", "Status"]))
    st.divider(); st.subheader("⚖️ Statutes"); st.write("- PPC 1860\n- CrPC 1898\n- CPC 1908\n- QSO 1984")

def render_about():
    st.header("ℹ️ System Credits")
    team = [
        {"Member": "Saim Ahmed", "Role": "Lead"}, {"Member": "Huzaifa Khan", "Role": "Architect"},
        {"Member": "Mustafa Khan", "Role": "DB"}, {"Member": "Ibrahim Sohail", "Role": "UI"},
        {"Member": "Daniyal Faraz", "Role": "QA"}
    ]
    st.table(team)

# ==============================================================================
# 6. AUTHENTICATION CONTROLLER
# ==============================================================================

def render_login():
    st.title("⚖️ Alpha Apex Portal Access")
    user_info = authenticator.login()
    if user_info:
        st.session_state.connected = True
        st.session_state.user_email = user_info['email']
        st.session_state.username = user_info.get('name', 'User')
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

    t1, t2 = st.tabs(["Cloud Auth", "Local Vault"])
    with t1: st.info("Use the Google button above.")
    with t2:
        e = st.text_input("Vault Email"); p = st.text_input("Vault Password", type="password")
        if st.button("Access Vault"):
            name = db_check_login(e, p)
            if name:
                st.session_state.connected = True
                st.session_state.user_email = e; st.session_state.username = name; st.rerun()

# ==============================================================================
# 7. MASTER EXECUTION ENGINE (400+ LINES)
# ==============================================================================

# SAFE SESSION STATE INITIALIZATION
keys = ["connected", "user_email", "username", "active_case"]
for key in keys:
    if key not in st.session_state:
        st.session_state[key] = False if key == "connected" else ""

# Persistent Recovery Check
if not st.session_state.connected:
    try:
        u = authenticator.check_authentification()
        if u:
            st.session_state.connected = True
            st.session_state.user_email = u['email']
            st.session_state.username = u.get('name', 'User')
            st.rerun()
    except: pass

# Main Router
if not st.session_state.connected:
    render_login()
else:
    nav = st.sidebar.radio("Navigation", ["Chambers", "Library", "About"])
    if nav == "Chambers": render_chambers()
    elif nav == "Library": render_library()
    else: render_about()

# ==============================================================================
# END OF SCRIPT
# ==============================================================================
