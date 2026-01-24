__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import json
import os
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

# Corrected Secret Key
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "advocate_ai_v3.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, password TEXT, joined_date TEXT)')
    
    # Ensure password column exists if table was created older versions
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
        temperature=0.2,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE", 
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE", 
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE", 
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
        }
    )

def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{safe_text}'); msg.lang = '{lang_code}'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

# ==============================================================================
# 3. GOOGLE OAUTH CONFIG
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f:
        json.dump({"web": auth_config}, f)
    
    authenticator = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='advocate_ai_cookie',
        cookie_key='legal_app_secret_key',
        redirect_uri=auth_config['redirect_uris'][0],
    )
except Exception as e:
    st.error(f"OAuth Config Missing: {e}")
    st.stop()

authenticator.check_authentication()

if st.session_state.get('connected'):
    uinfo = st.session_state.get('user_info', {})
    if 'email' in uinfo:
        st.session_state.logged_in = True
        st.session_state.user_email = uinfo['email']
        st.session_state.username = uinfo.get('name', uinfo['email'].split('@')[0])
        db_register_user(st.session_state.user_email, st.session_state.username)

# ==============================================================================
# 4. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]

        st.divider()
        st.subheader("🏛️ System Configuration")
        with st.expander("Custom Instructions & Behavior", expanded=True):
            sys_persona = st.text_input("Core Persona:", value="#You are a Pakistani law analyst")
            custom_instructions = st.text_area("Custom System Instructions:", 
                placeholder="e.g. Focus on inheritance law, always cite PPC 302, etc.")
            use_irac = st.toggle("Enable IRAC Style", value=True)
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Current Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        new_case = st.text_input("New Case Name")
        if st.button("➕ Create"):
            if new_case:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_case, "2026-01-24"))
                conn.commit(); conn.close(); st.rerun()

        if st.button("🗑️ Delete"):
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("DELETE FROM cases WHERE email=? AND case_name=?", (st.session_state.user_email, active_case))
            conn.commit(); conn.close(); st.rerun()

        if st.button("🚪 Logout"):
            authenticator.logout()
            st.session_state.logged_in = False
            st.rerun()

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Start legal consultation...")

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"): st.write(query)
        
        with st.chat_message("assistant"):
            try:
                irac_style = """Structure your response strictly using the IRAC method:
                - ISSUE: Clearly state the legal question.
                - RULE: Cite relevant sections of the Pakistan Penal Code (PPC) or Constitution.
                - ANALYSIS: Apply the law to the client's specific facts.
                - CONCLUSION: Provide a clear legal observation or next step.""" if use_irac else ""

                full_prompt = f"{sys_persona}\n{irac_style}\nADDITIONAL: {custom_instructions}\nLANG: {target_lang}\nClient Query: {query}"
                response = load_llm().invoke(full_prompt).content
                st.markdown(response)
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                play_voice_js(response, lang_code)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ==============================================================================
# 5. LIBRARY & ABOUT (LEGAL STATUTES UPDATED)
# ==============================================================================
def render_library():
    st.header("📚 Legal Library")
    st.info("Direct access to Pakistan's Primary Legal Statutes.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇵🇰 Statutes & Codes")
        st.markdown("""
        * **Pakistan Penal Code (PPC):** The core document defining crimes and punishments.
        * **Code of Criminal Procedure (CrPC):** Procedures for criminal law enforcement.
        * **Civil Procedure Code (CPC):** The framework for civil litigation.
        * **Qanun-e-Shahadat Order (QSO):** The law of evidence in Pakistan.
        """)
        
    with col2:
        st.subheader("📜 Constitutional Documents")
        st.markdown("""
        * **Constitution of 1973:** The supreme law of Pakistan.
        * **Amendments:** Track the 1st through 26th Amendments.
        * **Fundamental Rights:** Article 8 to 28 details.
        """)

    st.divider()
    st.write("🔍 *Note: Use the Chambers AI to search specific clauses within these statutes.*")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    team = [
        {"Name": "Saim Ahmed", "Contact": "03700297696", "Email": "saimahmed.work733@gmail.com"},
        {"Name": "Huzaifa Khan", "Contact": "03102526567", "Email": "m.huzaifa.khan471@gmail.com"},
        {"Name": "Mustafa Khan", "Contact": "03460222290", "Email": "muhammadmustafakhan430@gmail.com"},
        {"Name": "Ibrahim Sohail", "Contact": "03212046403", "Email": "ibrahimsohailkhan10@gmail.com"},
        {"Name": "Daniyal Faraz", "Contact": "03333502530", "Email": "daniyalfarazkhan2012@gmail.com"},
    ]
    st.table(team)

# ==============================================================================
# 6. LOGIN / SIGNUP PAGE
# ==============================================================================
def render_login():
    st.title("⚖️ Alpha Apex Login")
    tab1, tab2 = st.tabs(["Google Login", "Manual Access"])
    
    with tab1:
        auth_url = authenticator.get_authorization_url()
        st.link_button("Login with Google", auth_url)

    with tab2:
        mode = st.radio("Select Mode", ["Login", "Signup"], horizontal=True)
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if mode == "Signup":
            name = st.text_input("Full Name")
            if st.button("Create Account"):
                if "@" in email and password and name:
                    db_register_user(email, name, password)
                    st.success("Account created! Switch to Login mode.")
                else: st.error("Please fill all fields correctly.")
        else:
            if st.button("Login"):
                username = db_check_login(email, password)
                if username:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.username = username
                    st.rerun()
                else: st.error("Invalid credentials.")

# ==============================================================================
# 7. MAIN FLOW
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_login()
else:
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()
