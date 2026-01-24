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
# 1. SYSTEM ARCHITECTURE & DATABASE LAYER (FULL PERSISTENCE)
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Pakistani Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration Constants
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "advocate_ai_v8_enterprise.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_sql_db():
    """
    Constructs the relational database schema. 
    Handles Users, Cases, Chat History, and Document Metadata.
    """
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # User Management Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, username TEXT, password TEXT, joined_date TEXT)''')
    
    # Migration Check: Ensure password field exists for local vault logins
    c.execute("PRAGMA table_info(users)")
    cols = [info[1] for info in c.fetchall()]
    if 'password' not in cols:
        c.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')

    # Case Management Table
    c.execute('''CREATE TABLE IF NOT EXISTS cases 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)''')
    
    # Message Persistence Table
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)''')
    
    # Document Library Table
    c.execute('''CREATE TABLE IF NOT EXISTS documents 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size TEXT, pages INTEGER, indexed TEXT)''')
    
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    """Handles new user onboarding and default case initialization."""
    if not email:
        return
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", 
              (email, username, password, datetime.datetime.now().strftime("%Y-%m-%d")))
    
    # Verify if user has at least one active case
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                  (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_check_login(email, password):
    """Internal credential verification for the Local Vault mode."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    """Persists a chat exchange to the SQLite history table."""
    if not email:
        return
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
    """Retrieves full conversation logs for the UI renderer."""
    if not email:
        return []
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
    """Fetches all indexed documents for the Library view."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, size, pages, indexed FROM documents")
    data = c.fetchall()
    conn.close()
    return data

def sync_data_folder():
    """
    Automated File System Sync: 
    Scans the /data directory for new PDFs and indexes their metadata.
    """
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    existing = [row[0] for row in c.execute("SELECT name FROM documents").fetchall()]
    
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith(".pdf") and filename not in existing:
                path = os.path.join(DATA_FOLDER, filename)
                try:
                    reader = PdfReader(path)
                    pages = len(reader.pages)
                    size = f"{os.path.getsize(path) / 1024:.1f} KB"
                    c.execute("INSERT INTO documents (name, size, pages, indexed) VALUES (?, ?, ?, ?)", 
                              (filename, size, pages, "✅ Indexed"))
                except Exception as e:
                    print(f"Error indexing {filename}: {e}")
                    continue
    conn.commit()
    conn.close()

# Initialize Database on Startup
init_sql_db()
sync_data_folder()

# ==============================================================================
# 2. CORE UTILITY SERVICES (LLM, EMAIL, VOICE)
# ==============================================================================

@st.cache_resource
def load_llm():
    """Loads the Generative AI engine with specialized legal safety parameters."""
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

def send_email_report(receiver_email, case_name, history):
    """Formats and dispatches legal reports via SMTP."""
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        
        body = f"Alpha Apex Legal Consultation Report\nCase Name: {case_name}\n"
        body += f"Generated On: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        body += "="*50 + "\n\n"
        for m in history:
            label = "Counsel" if m['role'] == 'assistant' else "Client"
            body += f"[{label}]: {m['content']}\n\n"
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex AI <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Legal Record: {case_name}"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Dispatch Failed: {e}")
        return False

def play_voice_js(text, lang_code):
    """Injected JavaScript for Client-Side Text-to-Speech synthesis."""
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
    <script>
    window.speechSynthesis.cancel();
    var msg = new SpeechSynthesisUtterance('{safe_text}');
    msg.lang = '{lang_code}';
    msg.rate = 1.0;
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. GOOGLE OAUTH & SESSION STABILIZER
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f:
        json.dump({"web": auth_config}, f)
    
    authenticator = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='alpha_apex_secure_cookie',
        cookie_key='legal_vault_key_2026',
        redirect_uri=auth_config['redirect_uris'][0],
    )
    # Intercept Google Redirect token
    authenticator.check_authentification()
except Exception as e:
    st.error(f"OAUTH CONFIG ERROR: {e}")
    st.stop()

# ==============================================================================
# 4. MAIN USER INTERFACES
# ==============================================================================

def render_chambers():
    """The core legal consultation workspace."""
    langs = {
        "English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"
    }
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Selection Language", list(langs.keys()))
        lang_code = langs[target_lang]

        st.divider()
        st.subheader("🏛️ AI Configuration")
        with st.expander("System Persona Tuning", expanded=True):
            sys_persona = st.text_input("Core Persona:", value="#You are a highly analytical Pakistani law expert")
            custom_directives = st.text_area("Specific Directives:", placeholder="e.g. Focus on Civil Law citations.")
            use_irac = st.toggle("Enforce IRAC Logic", value=True)
        
        st.divider()
        st.subheader("📁 Case Records")
        conn = sqlite3.connect(SQL_DB_FILE)
        # Use safe session get to prevent KeyErrors
        curr_user = st.session_state.get('user_email', "")
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (curr_user,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Active Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        new_case = st.text_input("Initialize New Case")
        if st.button("➕ Create Case") and new_case:
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                         (curr_user, new_case, datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); conn.close(); st.rerun()

        if st.button("📧 Email Transcript"):
            hist = db_load_history(curr_user, st.session_state.active_case)
            if send_email_report(curr_user, st.session_state.active_case, hist):
                st.sidebar.success("Transcript Dispatched!")

        if st.button("🚪 Logout Session"):
            authenticator.logout()
            st.session_state.connected = False
            st.rerun()

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # Display message history
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # Consultation Inputs
    m_col, i_col = st.columns([1, 10])
    with m_col:
        voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col:
        text_in = st.chat_input("State your legal query or case facts...")

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            try:
                irac_block = """
                Strictly apply IRAC structure:
                1. ISSUE: Define the legal conflict.
                2. RULE: Reference PPC, CrPC, QSO, or CPC sections.
                3. ANALYSIS: Correlate law with the provided facts.
                4. CONCLUSION: Provide final legal stance.
                """ if use_irac else ""

                full_prompt = f"{sys_persona}\n{irac_block}\nDIRECTIVES: {custom_directives}\nLANG: {target_lang}\nQUERY: {query}"
                
                response = load_llm().invoke(full_prompt).content
                st.markdown(response)
                
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                play_voice_js(response, lang_code)
                st.rerun()
            except Exception as e:
                st.error(f"Consultation Error: {e}")

def render_library():
    """Displays the indexed document repository and statutory references."""
    st.header("📚 Virtual Law Library")
    st.info("The system automatically syncs with the project '/data' directory.")
    
    if st.button("🔄 Rescan Library Folder"):
        sync_data_folder()
        st.rerun()
        
    docs = db_get_docs()
    if docs:
        df = pd.DataFrame(docs, columns=["Document Name", "File Size", "Total Pages", "Status"])
        st.table(df)
    else:
        st.warning("No PDF files currently detected in '/data'.")

    st.divider()
    st.subheader("⚖️ Primary Statutory References")
    t1, t2, t3, t4 = st.tabs(["Criminal", "Civil", "Constitutional", "Special"])
    with t1:
        st.write("- **Pakistan Penal Code (PPC) 1860**\n- **Code of Criminal Procedure (CrPC) 1898**")
    with t2:
        st.write("- **Code of Civil Procedure (CPC) 1908**\n- **Qanun-e-Shahadat Order (QSO) 1984**\n- **Contract Act 1872**")
    with t3:
        st.write("- **Constitution of the Islamic Republic of Pakistan 1973**")
    with t4:
        st.write("- **Anti-Terrorism Act 1997**\n- **NAB Ordinance 1999**\n- **Family Laws 1961**")

def render_about():
    """System information and development credits."""
    st.header("ℹ️ Alpha Apex Information")
    st.success("Platform status: Active | Engine: Gemini 1.5-Flash | Persistence: SQLite-v3")
    
    st.subheader("👥 Project Development Team")
    team = [
        {"Member": "Saim Ahmed", "Role": "Full Stack Lead", "Contact": "saimahmed.work733@gmail.com"},
        {"Member": "Huzaifa Khan", "Role": "System Architect", "Contact": "m.huzaifa.khan471@gmail.com"},
        {"Member": "Mustafa Khan", "Role": "Database Engineer", "Contact": "muhammadmustafakhan430@gmail.com"},
        {"Member": "Ibrahim Sohail", "Role": "UI/UX Designer", "Contact": "ibrahimsohailkhan10@gmail.com"},
        {"Member": "Daniyal Faraz", "Role": "QA & Security Specialist", "Contact": "daniyalfarazkhan2012@gmail.com"},
    ]
    st.table(team)
    st.info("Developed as a specialized tool for Pakistani Jurisprudence analysis.")

# ==============================================================================
# 5. AUTHENTICATION CONTROLLER (MULTI-MODE LOGIC)
# ==============================================================================

def render_login():
    """Handles both Google OAuth and Local SQL-based login."""
    st.title("⚖️ Alpha Apex Secure Gateway")
    
    # Render the Google Sign-In Button
    user_info = authenticator.login()
    
    # Process Google User Info if returned
    if user_info:
        st.session_state.connected = True
        st.session_state.user_email = user_info['email']
        st.session_state.username = user_info.get('name', user_info['email'].split('@')[0])
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

    tab1, tab2 = st.tabs(["Cloud Authentication", "Local Vault Access"])
    
    with tab1:
        st.info("Use the 'Sign in with Google' button above for direct cloud access.")
        st.write("Session Status:", "Unlocked" if st.session_state.get('connected') else "Locked")
    
    with tab2:
        mode = st.radio("Access Type", ["Login", "Register"], horizontal=True)
        email = st.text_input("Vault Email")
        password = st.text_input("Vault Password", type="password")
        
        if mode == "Register":
            name = st.text_input("Full Legal Name")
            if st.button("Initialize Account") and email and password:
                db_register_user(email, name, password)
                st.success("Local registration complete. You may now login.")
        else:
            if st.button("Authorize Access"):
                username = db_check_login(email, password)
                if username:
                    st.session_state.connected = True
                    st.session_state.user_email = email
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Credentials.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE (400+ LINES TOTAL)
# ==============================================================================

# SAFE INITIALIZATION OF ALL SESSION STATE KEYS (PREVENTS KEYERROR)
if "connected" not in st.session_state:
    st.session_state.connected = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "username" not in st.session_state:
    st.session_state.username = ""
if "active_case" not in st.session_state:
    st.session_state.active_case = "General Consultation"

# PERSISTENT SESSION RECOVERY (COOKIE CHECK)
if not st.session_state.connected:
    try:
        # Check background auth status from cookie
        u_info = authenticator.check_authentification()
        if u_info:
            st.session_state.connected = True
            st.session_state.user_email = u_info['email']
            st.session_state.username = u_info.get('name', 'User')
            st.rerun()
    except Exception:
        pass

# ROUTING LOGIC
if not st.session_state.connected:
    render_login()
else:
    nav_option = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    
    if nav_option == "Chambers":
        render_chambers()
    elif nav_option == "Legal Library":
        render_library()
    else:
        render_about()

# ==============================================================================
# END OF SCRIPT - VERIFIED STABLE FOR STREAMLIT CLOUD
# ==============================================================================
