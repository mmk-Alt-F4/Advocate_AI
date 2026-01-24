__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import time
import json
import re
import os
import glob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

# Professional Black Styling
st.markdown("""
    <style>
    .main .block-container { padding-bottom: 150px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #333; }
    [data-testid="stSidebar"] { 
        background-color: #000000; 
        border-right: 1px solid #333; 
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { 
        color: #ffffff !important; 
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #222;
        color: white;
        border: 1px solid #444;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets")
    st.stop()

SQL_DB_FILE = "advocate_ai_v3.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    # Create tables
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    
    # Check for password column and add if missing (Multi-user resilience)
    c.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in c.fetchall()]
    if 'password' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')
        
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", 
              (email, username, password, datetime.datetime.now().strftime("%Y-%m-%d")))
    
    # Ensure every user has at least one default case
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                  (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_save_message(email, case_name, role, content):
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
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC", (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

init_sql_db()

# ==============================================================================
# 2. CORE UTILITIES
# ==============================================================================
def send_email_report(receiver_email, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        report_content = f"Legal Report: {case_name}\n" + "="*30 + "\n\n"
        for m in history:
            role = "Counsel" if m['role'] == 'assistant' else "Client"
            report_content += f"[{role}]: {m['content']}\n\n"
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Legal Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Failed: {e}")
        return False

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY, 
        temperature=0.3,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )

def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. GOOGLE AUTHENTICATION (REFACTORED)
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f:
        json.dump({"web": auth_config}, f)
    
    # Initialize Google Authenticator
    authenticator = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='advocate_ai_cookie',
        cookie_key='legal_app_secret_key',
        redirect_uri=auth_config['redirect_uris'][0],
    )
except Exception as e:
    st.error(f"Auth Setup Error: {e}")
    st.stop()

# Handle Redirect Callback
authenticator.check_authentication()

if st.session_state.get('connected'):
    uinfo = st.session_state.get('user_info', {})
    if 'email' in uinfo:
        st.session_state.user_email = uinfo['email']
        st.session_state.username = uinfo.get('name', uinfo['email'].split('@')[0])
        st.session_state.logged_in = True
        db_register_user(st.session_state.user_email, st.session_state.username)

# ==============================================================================
# 4. PAGE RENDERERS
# ==============================================================================
def render_chambers():
    langs = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK", 
        "Pashto": "ps-PK", 
        "Balochi": "bal-PK"
    }
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        st.subheader("📁 Case Management")
        
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        if not cases: 
            cases = ["General Consultation"]
        
        if "active_case" not in st.session_state or st.session_state.active_case not in cases:
            st.session_state.active_case = cases[0]
            
        active_case = st.selectbox("Select Case", cases, index=cases.index(st.session_state.active_case))
        st.session_state.active_case = active_case

        # Case Actions
        new_case_name = st.text_input("New Case Name")
        if st.button("➕ Create New Case"):
            if new_case_name:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                             (st.session_state.user_email, new_case_name, str(datetime.date.today())))
                conn.commit(); conn.close()
                st.session_state.active_case = new_case_name
                st.rerun()

        rename_to = st.text_input("Rename Current Case to:")
        if st.button("✏️ Rename Case"):
            if rename_to and active_case:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("UPDATE cases SET case_name=? WHERE email=? AND case_name=?", 
                             (rename_to, st.session_state.user_email, active_case))
                conn.commit(); conn.close()
                st.session_state.active_case = rename_to
                st.rerun()

        if st.button("🗑️ Delete Current Case"):
            if len(cases) > 1:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("DELETE FROM cases WHERE email=? AND case_name=?", 
                             (st.session_state.user_email, active_case))
                conn.commit(); conn.close()
                st.rerun()
            else:
                st.warning("General Consultation cannot be deleted.")

        st.divider()
        if st.button("📧 Email Chat History"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.success("Sent!")

        if st.button("🚪 Log Out"):
            authenticator.logout()
            st.session_state.logged_in = False
            st.rerun()

    # Chambers Layout
    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # Quick Action Buttons
    c1, c2, c3 = st.columns(3)
    quick_q = None
    if c1.button("🧠 Infer Legal Path"): quick_q = "What is the recommended legal path for this situation?"
    if c2.button("📜 Give Ruling"): quick_q = "Based on the facts provided, give a preliminary legal observation."
    if c3.button("📝 Summarize"): quick_q = "Please summarize our entire case history."
    st.divider()

    # Load and display history
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): 
            st.write(m["content"])

    # Chat Input Section
    m_col, i_col = st.columns([1, 8])
    with m_col: 
        voice_in = speech_to_text(language=lang_code, key='mic_input', just_once=True)
    with i_col: 
        text_in = st.chat_input("Consult Alpha Apex Legal Intelligence...")

    query = quick_q or voice_in or text_in
    if query:
        # Save User Message
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"): 
            st.write(query)
        
        # AI Response
        with st.chat_message("assistant"):
            with st.spinner("Consulting Legal Frameworks..."):
                try:
                    # Detailed Prompting
                    prompt = f"You are Alpha Apex, an expert High Court Advocate. Use professional legal terminology. Respond in {target_lang}. User Query: {query}"
                    response = load_llm().invoke(prompt).content
                    st.write(response)
                    
                    # Save AI Message
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                    play_voice_js(response, lang_code)
                    
                    # Small delay before rerun to ensure DB update
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"AI System Error: {e}")

def render_library():
    st.header("📚 Legal Library")
    st.info("Browse Pakistan Penal Code (PPC), CrPC, and the Constitution of Pakistan.")
    st.write("This section provides access to indexed legal documents and statutes.")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    st.write("Alpha Apex is an AI-powered Justice Platform specifically designed for the legal landscape of Pakistan.")
    st.markdown("""
    **Core Features:**
    * IRAC-based legal analysis.
    * Multi-lingual support (Urdu, Sindhi, Punjabi, Pashto, Balochi).
    * Integrated Case Management.
    """)

# ==============================================================================
# 5. MAIN FLOW CONTROL
# ==============================================================================
if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("⚖️ Alpha Apex Login")
        st.write("Welcome to the Pakistan's AI Advocate Chambers.")
        
        # Google OAuth Button
        if not st.session_state.get('connected'):
            auth_url = authenticator.get_authorization_url()
            st.link_button("Login with Google", auth_url)
        
        st.divider()
        st.subheader("Manual Email Access")
        email_field = st.text_input("Enter Registered Email")
        if st.button("Access Chambers"):
            if "@" in email_field:
                st.session_state.logged_in = True
                st.session_state.user_email = email_field
                db_register_user(email_field, email_field.split("@")[0])
                st.rerun()
            else:
                st.error("Please enter a valid email address.")
else:
    # Navigation Sidebar
    with st.sidebar:
        st.divider()
        page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    
    if page == "Chambers": 
        render_chambers()
    elif page == "Legal Library": 
        render_library()
    else: 
        render_about()
