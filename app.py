# ==============================================================================
# ALPHA APEX - SOVEREIGN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 22.0 (LOCAL VAULT EDITION - NO OAUTH)
# ARCHITECTS: SAIM AHMED, HUZAIFA KHAN, MUSTAFA KHAN, IBRAHIM SOHAIL, DANIYAL FARAZ
# ==============================================================================

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import json
import os
import time
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. UI ENGINE & ADVANCED SHADER ARCHITECTURE
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Sovereign Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_sovereign_shaders(theme_mode):
    """
    Restores the heavy-duty CSS architecture.
    Handles transitions, chat bubble geometry, and sidebar glassmorphism.
    """
    shader_css = """
    <style>
        /* Global Cinematic Transitions */
        * { transition: background-color 0.7s cubic-bezier(0.4, 0, 0.2, 1), color 0.7s ease !important; }
        .stApp { transition: background 0.7s ease !important; }
        
        /* High-Fidelity Chat Geometry */
        .stChatMessage {
            border-radius: 22px !important;
            padding: 1.8rem !important;
            margin-bottom: 1.3rem !important;
            box-shadow: 0 10px 20px rgba(0,0,0,0.12) !important;
            animation: slideIn 0.5s ease-out;
            border: 1px solid rgba(128,128,128,0.1) !important;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Button & Input Polish */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.2px !important;
            background: linear-gradient(45deg, #2c3e50, #4ca1af) !important;
            color: white !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton>button:hover {
            transform: scale(1.02) !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
        }

        /* Sidebar Geometry */
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128,128,128,0.2) !important;
            padding-top: 2rem !important;
        }

        /* Input Container Alignment */
        .stTextInput>div>div>input {
            border-radius: 10px !important;
        }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += """
        <style>
            .stApp { background: linear-gradient(135deg, #0f172a 0%, #020617 100%) !important; color: #f1f5f9 !important; }
            .stChatMessage { background: #1e293b !important; }
            .stTextInput>div>div>input { background-color: #0f172a !important; color: white !important; }
            h1, h2, h3 { color: #38bdf8 !important; }
        </style>
        """
    else:
        shader_css += """
        <style>
            .stApp { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important; color: #0f172a !important; }
            .stChatMessage { background: #ffffff !important; border: 1px solid #cbd5e1 !important; }
            h1, h2, h3 { color: #0284c7 !important; }
        </style>
        """
    st.markdown(shader_css, unsafe_allow_html=True)

# Global Configuration
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_sovereign_vault_v22.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (RDBMS)
# ==============================================================================

def init_relational_db():
    """Builds the comprehensive SQL schema for local vault management."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Table 1: Sovereign User Vault
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    username TEXT, 
                    password TEXT, 
                    joined_on TEXT,
                    tier TEXT DEFAULT 'Senior Advocate'
                 )''')
    
    # Table 2: Chamber Registry
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email TEXT, 
                    case_name TEXT, 
                    created_on TEXT
                 )''')
    
    # Table 3: Consultation Logs
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    case_id INTEGER, 
                    role TEXT, 
                    content TEXT, 
                    timestamp TEXT
                 )''')
    
    # Table 4: Law Library Metadata
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    size TEXT, 
                    pages INTEGER, 
                    indexed_on TEXT
                 )''')
    
    conn.commit()
    conn.close()

def db_register_user(email, username, password):
    """Registers a user into the local SQL vault and initializes their chamber."""
    if not email or not password: return False
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO users (email, username, password, joined_on) VALUES (?,?,?,?)", 
                  (email, username, password, now))
        c.execute("INSERT INTO cases (email, case_name, created_on) VALUES (?,?,?)", 
                  (email, "General Consultation", now))
        conn.commit(); conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close(); return False

def db_authenticate_user(email, password):
    """Verifies credentials against the local SQL database."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone(); conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    """Logs interactions to the persistent history table."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    case_res = c.fetchone()
    if case_res:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (case_res[0], role, content, ts))
        conn.commit()
    conn.close()

def db_load_history(email, case_name):
    """Retrieves context for the current active chamber."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute('''SELECT h.role, h.content FROM history h 
                 JOIN cases c ON h.case_id = c.id 
                 WHERE c.email=? AND c.case_name=? ORDER BY h.id ASC''', (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]; conn.close()
    return data

init_relational_db()

# ==============================================================================
# 3. SERVICE ARCHITECTURE: AI, VOICE, AND SMTP
# ==============================================================================

@st.cache_resource
def load_ai_engine():
    """Initializes Gemini with senior legal advisory parameters."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY, 
        temperature=0.2,
        max_output_tokens=3500
    )

def trigger_voice_synthesis(text, lang):
    """JS Injection for real-time browser audio feedback."""
    clean = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js = f"<script>window.speechSynthesis.cancel(); var u = new SpeechSynthesisUtterance('{clean}'); u.lang='{lang}'; window.speechSynthesis.speak(u);</script>"
    components.html(js, height=0)

def dispatch_email_report(recipient, case_name, history):
    """SMTP Dispatch for sending consultation logs to user."""
    try:
        s_user = st.secrets["EMAIL_USER"]
        s_pass = st.secrets["EMAIL_PASS"]
        
        report = f"ALPHA APEX CASE SUMMARY\nCase: {case_name}\n" + ("="*30) + "\n\n"
        for m in history:
            role = "AI ADVOCATE" if m['role'] == 'assistant' else "CLIENT"
            report += f"[{role}]: {m['content']}\n\n"
            
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{s_user}>"
        msg['To'] = recipient
        msg['Subject'] = f"Legal Consult: {case_name}"
        msg.attach(MIMEText(report, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(s_user, s_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail Dispatch Error: {e}"); return False

def sync_library():
    """Indexes the local PDF library in the data folder."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    existing = [r[0] for r in c.execute("SELECT name FROM documents").fetchall()]
    if os.path.exists(DATA_FOLDER):
        for f in os.listdir(DATA_FOLDER):
            if f.lower().endswith(".pdf") and f not in existing:
                try:
                    pdf = PdfReader(os.path.join(DATA_FOLDER, f))
                    sz = f"{os.path.getsize(os.path.join(DATA_FOLDER, f))/1024:.1f} KB"
                    ts = datetime.datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO documents (name, size, pages, indexed_on) VALUES (?,?,?,?)", 
                              (f, sz, len(pdf.pages), ts))
                except: continue
    conn.commit(); conn.close()

# ==============================================================================
# 4. UI MODULES: SOVEREIGN CHAMBERS
# ==============================================================================

def render_chambers():
    """Primary consultation room with side-by-side voice input."""
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        mode = st.radio("UI Mode", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_sovereign_shaders(mode)
        
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        st.subheader("📁 Case Records")
        u_email = st.session_state.user_email
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        cases = [r[0] for r in c.execute("SELECT case_name FROM cases WHERE email=?", (u_email,)).fetchall()]
        conn.close()
        
        st.session_state.active_case = st.selectbox("Active Chamber", cases if cases else ["General Consultation"])
        
        if st.button("➕ New Case"):
            st.session_state.create_case = True
        
        if st.session_state.get('create_case'):
            c_name = st.text_input("Case Name")
            if st.button("Initialize") and c_name:
                conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
                c.execute("INSERT INTO cases (email, case_name, created_on) VALUES (?,?,?)", 
                          (u_email, c_name, str(datetime.date.today())))
                conn.commit(); conn.close(); st.session_state.create_case = False; st.rerun()

        st.divider()
        if st.button("📧 Send Brief"):
            hist = db_load_history(u_email, st.session_state.active_case)
            if dispatch_email_report(u_email, st.session_state.active_case, hist):
                st.success("Brief Dispatched.")

        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # 1. Historical Messages
    history_log = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for msg in history_log:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    # 2. Side-by-Side Prompt Area
    input_cols = st.columns([0.83, 0.17])
    with input_cols[0]:
        user_query = st.text_input("Enter facts...", placeholder="State your inquiry...", label_visibility="collapsed", key="txt_in")
    with input_cols[1]:
        v_query = speech_to_text(language=lang_code, key='mic_in', just_once=True, use_container_width=True)

    final_q = v_query or user_query

    if final_q:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_q)
        with st.chat_message("user"): st.write(final_q)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Statutes..."):
                try:
                    p = f"Persona: Senior Advocate. Structure: IRAC. Lang: {target_lang}. Query: {final_q}"
                    res = load_ai_engine().invoke(p).content
                    st.markdown(res)
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", res)
                    trigger_voice_synthesis(res, lang_code)
                    st.rerun()
                except Exception as e: st.error(f"AI Failure: {e}")

def render_library():
    st.header("📚 Law Library")
    if st.button("🔄 Sync"): sync_library(); st.rerun()
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    docs = c.execute("SELECT name, size, pages, indexed_on FROM documents").fetchall()
    conn.close()
    if docs: st.table(pd.DataFrame(docs, columns=["Name", "Size", "Pages", "Sync Date"]))

def render_login_portal():
    """RESTORED: Complete Sovereign Login & Signup Interface (Bypasses Google)."""
    st.title("⚖️ Alpha Apex Sovereign Login")
    st.markdown("#### Internal Database Access Gateway")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with tab1:
        le = st.text_input("Email")
        lp = st.text_input("Password", type="password")
        if st.button("Access Vault"):
            uname = db_authenticate_user(le, lp)
            if uname:
                st.session_state.logged_in = True
                st.session_state.user_email = le
                st.session_state.username = uname
                st.rerun()
            else: st.error("Access Denied: Invalid Credentials")
            
    with tab2:
        re = st.text_input("Signup Email")
        ru = st.text_input("Full Name")
        rp = st.text_input("Create Password", type="password")
        if st.button("Register Sovereign Account"):
            if db_register_user(re, ru, rp):
                st.success("Account Created! Please switch to Login tab.")
            else: st.error("Registration Failed: Email already exists.")

# ==============================================================================
# 5. MASTER EXECUTION ENGINE
# ==============================================================================

if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login_portal()
else:
    nav = st.sidebar.radio("Navigation", ["Chambers", "Library", "About"])
    if nav == "Chambers": render_chambers()
    elif nav == "Library": render_library()
    else:
        st.header("ℹ️ Development Team")
        st.table([["Saim Ahmed", "Lead"], ["Huzaifa Khan", "AI"], ["Mustafa Khan", "DB"], ["Ibrahim Sohail", "UX"], ["Daniyal Faraz", "QA"]])

# ==============================================================================
# END OF SCRIPT - VERBOSE & COMPREHENSIVE
# ==============================================================================
