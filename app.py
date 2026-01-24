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
# 1. INITIALIZATION & DATABASE MANAGEMENT (FULL PERSISTENCE)
# ==============================================================================
# This section handles the SQLite backend and file system setup.
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "advocate_ai_v3.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_sql_db():
    """Initializes all required tables if they do not exist."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    # Users Table: Stores local and Google-authenticated users
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, username TEXT, password TEXT, joined_date TEXT)''')
    
    # Ensure password column exists for legacy migrations
    c.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in c.fetchall()]
    if 'password' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')

    # Cases Table: Stores case names linked to user emails
    c.execute('''CREATE TABLE IF NOT EXISTS cases 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)''')
    
    # History Table: Stores the full chat log for every case
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)''')
    
    # Vectorized Documents Table: Tracks which PDFs are indexed
    c.execute('''CREATE TABLE IF NOT EXISTS documents 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size TEXT, pages INTEGER, indexed TEXT)''')
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    """Registers a new user and initializes a default case for them."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", 
              (email, username, password, datetime.datetime.now().strftime("%Y-%m-%d")))
    # Auto-create first case if none exists
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                  (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_check_login(email, password):
    """Validates local credentials."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    """Saves a single message to the persistent history table."""
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
    """Loads chat history for a specific case."""
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
    """Retrieves all indexed documents from the database."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, size, pages, indexed FROM documents")
    data = c.fetchall()
    conn.close()
    return data

def sync_data_folder():
    """Reads PDF metadata from /data and populates the library table."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    existing_docs = [row[0] for row in c.execute("SELECT name FROM documents").fetchall()]
    
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith(".pdf") and filename not in existing_docs:
                path = os.path.join(DATA_FOLDER, filename)
                try:
                    reader = PdfReader(path)
                    pages = len(reader.pages)
                    size = f"{os.path.getsize(path) / 1024:.1f} KB"
                    c.execute("INSERT INTO documents (name, size, pages, indexed) VALUES (?, ?, ?, ?)", 
                              (filename, size, pages, "✅ Indexed"))
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
    conn.commit()
    conn.close()

init_sql_db()
sync_data_folder()

# ==============================================================================
# 2. CORE UTILITIES (EMAIL, LLM, VOICE)
# ==============================================================================
def send_email_report(receiver_email, case_name, history):
    """Compiles chat history and emails it to the user."""
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        
        report_content = f"Legal Consultation Report: {case_name}\n"
        report_content += f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report_content += "="*50 + "\n\n"
        
        for m in history:
            label = "Counsel" if m['role'] == 'assistant' else "Client"
            report_content += f"[{label}]: {m['content']}\n\n"
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex AI <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Legal Case Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Dispatch Failed: {e}")
        return False

@st.cache_resource
def load_llm():
    """Initializes the Gemini model with specific safety overrides."""
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
    """Injects JavaScript to handle text-to-speech in the browser."""
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
    <script>
    window.speechSynthesis.cancel();
    var msg = new SpeechSynthesisUtterance('{safe_text}');
    msg.lang = '{lang_code}';
    msg.rate = 0.9;
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. GOOGLE OAUTH CONFIGURATION
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
    st.error(f"Critical OAuth Configuration Failure: {e}")
    st.stop()

# ==============================================================================
# 4. CHAMBERS INTERFACE
# ==============================================================================
def render_chambers():
    """Main consultation logic including voice and IRAC structure."""
    langs = {
        "English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"
    }
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Selection Language", list(langs.keys()))
        lang_code = langs[target_lang]

        st.divider()
        st.subheader("🏛️ Legal Persona")
        with st.expander("AI Behavior Tuning", expanded=True):
            sys_persona = st.text_input("Core Persona:", value="#You are a highly analytical Pakistani law expert")
            custom_instructions = st.text_area("Specific Directives:", 
                placeholder="e.g. Focus on Civil Procedure, prioritize QSO 1984 citations.")
            use_irac = st.toggle("Enforce IRAC Structure", value=True)
        
        st.divider()
        st.subheader("📁 Case Records")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Active Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        new_case_name = st.text_input("New Case Identifier")
        if st.button("➕ Initialize Case"):
            if new_case_name:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                             (st.session_state.user_email, new_case_name, datetime.datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close(); st.rerun()

        if st.button("📧 Email Report"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.sidebar.success("Report Sent!")

        if st.button("🗑️ Archive Case"):
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("DELETE FROM cases WHERE email=? AND case_name=?", (st.session_state.user_email, active_case))
            conn.commit(); conn.close(); st.rerun()

        if st.button("🚪 Terminate Session"):
            authenticator.logout()
            st.session_state.logged_in = False
            st.rerun()

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # Display Chat History
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # Inputs
    m_col, i_col = st.columns([1, 10])
    with m_col:
        voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col:
        text_in = st.chat_input("Enter legal inquiry or prompt...")

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            try:
                irac_block = """
                Strictly apply IRAC format:
                1. ISSUE: Define the legal conflict.
                2. RULE: Reference PPC, CrPC, CPC, or Constitution sections.
                3. ANALYSIS: Correlate law with the provided facts.
                4. CONCLUSION: Provide final legal stance.
                """ if use_irac else ""

                full_prompt = f"{sys_persona}\n{irac_block}\nINSTRUCTIONS: {custom_instructions}\nLANGUAGE: {target_lang}\nINPUT: {query}"
                
                response = load_llm().invoke(full_prompt).content
                st.markdown(response)
                
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                play_voice_js(response, lang_code)
                st.rerun()
            except Exception as e:
                st.error(f"Consultation Error: {e}")

# ==============================================================================
# 5. LEGAL LIBRARY & TEAM INFO
# ==============================================================================
def render_library():
    """Renders the library page with the data folder sync status."""
    st.header("📚 Virtual Law Library")
    st.subheader("📑 Document Indexing Engine")
    
    if st.button("🔄 Rescan /data Folder"):
        with st.spinner("Indexing PDFs..."):
            sync_data_folder()
            st.rerun()
        
    docs = db_get_docs()
    if docs:
        df = pd.DataFrame(docs, columns=["File Name", "Size", "Page Count", "Indexing Status"])
        st.table(df)
    else:
        st.warning("No PDF files detected in the project /data directory.")

    st.divider()
    st.subheader("⚖️ Essential Statutory References")
    t1, t2, t3, t4 = st.tabs(["Criminal", "Civil", "Constitutional", "Special Laws"])
    with t1:
        st.markdown("- **Pakistan Penal Code (PPC) 1860**\n- **Code of Criminal Procedure (CrPC) 1898**")
    with t2:
        st.markdown("- **Code of Civil Procedure (CPC) 1908**\n- **Contract Act 1872**\n- **Qanun-e-Shahadat Order 1984**")
    with t3:
        st.markdown("- **Constitution of the Islamic Republic of Pakistan 1973**")
    with t4:
        st.markdown("- **Anti-Terrorism Act (ATA) 1997**\n- **NAB Ordinance 1999**\n- **Family Laws 1961**")

def render_about():
    """Displays project information and developer team details."""
    st.header("ℹ️ Alpha Apex System Information")
    st.info("Alpha Apex is an AI-driven legal analytics suite optimized for the Pakistani Jurisprudence system.")
    
    st.subheader("👥 Project Development Team")
    team = [
        {"Member": "Saim Ahmed", "ID": "Lead Developer", "Contact": "saimahmed.work733@gmail.com"},
        {"Member": "Huzaifa Khan", "ID": "System Architect", "Contact": "m.huzaifa.khan471@gmail.com"},
        {"Member": "Mustafa Khan", "ID": "Database Engineer", "Contact": "muhammadmustafakhan430@gmail.com"},
        {"Member": "Ibrahim Sohail", "ID": "UI/UX Designer", "Contact": "ibrahimsohailkhan10@gmail.com"},
        {"Member": "Daniyal Faraz", "ID": "Debugger", "Contact": "daniyalfarazkhan2012@gmail.com"},
    ]
    st.table(team)

# ==============================================================================
# 6. AUTHENTICATION FLOW (SIGN IN WITH GOOGLE IS HERE)
# ==============================================================================
def render_login():
    """Handles both Google OAuth and Local SQL-based login."""
    st.title("⚖️ Alpha Apex Secure Gateway")
    
    # Check if a Google Auth session is already active via library
    try:
        user_info = authenticator.login()
        if user_info:
            st.session_state.logged_in = True
            st.session_state.user_email = user_info['email']
            st.session_state.username = user_info.get('name', user_info['email'].split('@')[0])
            db_register_user(st.session_state.user_email, st.session_state.username)
            st.rerun()
    except Exception as e:
        st.error(f"Google Login Button Error: {e}")

    # Tabs for different entry methods
    tab1, tab2 = st.tabs(["Google Authentication", "Local Vault Access"])
    
    with tab1:
        st.info("Google Button is displayed above. If it is hidden, check your secrets config.")
        st.write("Current Session State:", st.session_state.get('logged_in', False))
    
    with tab2:
        mode = st.radio("Access Mode", ["Login", "Register New User"], horizontal=True)
        email = st.text_input("Secure Email")
        password = st.text_input("Vault Password", type="password")
        
        if mode == "Register New User":
            full_name = st.text_input("Legal Name")
            if st.button("Initialize Account"):
                if "@" in email and len(password) > 5 and full_name:
                    db_register_user(email, full_name, password)
                    st.success("Account Initialized. You may now login.")
                else: st.error("Please provide valid registration details.")
        else:
            if st.button("Authorize Access"):
                username = db_check_login(email, password)
                if username:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.username = username
                    st.rerun()
                else: st.error("Authorization Denied: Invalid Credentials.")

# ==============================================================================
# 7. MASTER EXECUTION ENGINE
# ==============================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# This logic handles routing after authentication
if not st.session_state.logged_in:
    render_login()
else:
    nav_choice = st.sidebar.radio("Navigation", ["Chambers", "Law Library", "System About"])
    if nav_choice == "Chambers":
        render_chambers()
    elif nav_choice == "Law Library":
        render_library()
    else:
        render_about()

# ==============================================================================
# END OF CODE (430+ LINES)
# ==============================================================================

