# ==============================================================================
# ALPHA APEX - OMNIPOTENCE ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 21.0 (MAXIMUM VERBOSITY - SOVEREIGN PRODUCTION)
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
import base64
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ==============================================================================
# 1. THEME ENGINE & ADVANCED SHADER ARCHITECTURE (GLOBAL SCOPE)
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Omnipotence Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_omnipotence_shaders(theme_mode):
    """
    Injects a high-fidelity CSS architecture into the Streamlit DOM.
    Includes glassmorphism effects, neural transitions, and layout overrides.
    """
    shader_css = """
    <style>
        /* Global Animation Layer - Cinematic Transitions */
        * { transition: background-color 0.8s cubic-bezier(0.4, 0, 0.2, 1), color 0.8s ease !important; }
        .stApp { transition: background 0.8s ease !important; }
        
        /* Glassmorphism Sidebar */
        [data-testid="stSidebar"] {
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        /* High-Fidelity Chat Geometry */
        .stChatMessage {
            border-radius: 24px !important;
            padding: 2rem !important;
            margin-bottom: 1.5rem !important;
            box-shadow: 0 12px 24px rgba(0,0,0,0.15) !important;
            animation: slideUpFade 0.6s ease-out;
            border: 1px solid rgba(128,128,128,0.1) !important;
        }

        @keyframes slideUpFade {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Precision Button Styling */
        .stButton>button {
            border-radius: 14px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            background: linear-gradient(45deg, #1e293b, #334155) !important;
            color: white !important;
            border: none !important;
            height: 3rem !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3) !important;
            background: linear-gradient(45deg, #334155, #475569) !important;
        }

        /* Side-by-Side Component Alignment Logic */
        .voice-input-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            width: 100%;
        }

        /* Scrollbar Aesthetics */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += """
        <style>
            .stApp { background: radial-gradient(circle at top left, #0f172a, #020617) !important; color: #f1f5f9 !important; }
            .stChatMessage { background: rgba(30, 41, 59, 0.7) !important; backdrop-filter: blur(10px); }
            .stTextInput>div>div>input { background-color: #0f172a !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
            h1, h2, h3 { color: #38bdf8 !important; text-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }
        </style>
        """
    else:
        shader_css += """
        <style>
            .stApp { background: radial-gradient(circle at top left, #f8fafc, #e2e8f0) !important; color: #0f172a !important; }
            .stChatMessage { background: #ffffff !important; border: 1px solid #cbd5e1 !important; }
            .stTextInput>div>div>input { background-color: #ffffff !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; }
            h1, h2, h3 { color: #0284c7 !important; }
        </style>
        """
    st.markdown(shader_css, unsafe_allow_html=True)

# Configuration Global Constants
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_omnipotence_v21.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    try:
        os.makedirs(DATA_FOLDER)
    except Exception as e:
        st.error(f"SYSTEM FAILURE: Directory Creation Error: {e}")

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (RDBMS)
# ==============================================================================

def init_omnipotent_db():
    """Builds the exhaustive multi-table SQL architecture."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Table 1: Master User Registry
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    username TEXT, 
                    password TEXT, 
                    joined_on TEXT,
                    tier TEXT DEFAULT 'Enterprise',
                    status TEXT DEFAULT 'Active'
                 )''')
    
    # Table 2: Chamber Registry (Case Management)
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email TEXT, 
                    case_name TEXT, 
                    created_on TEXT,
                    category TEXT DEFAULT 'Civil'
                 )''')
    
    # Table 3: Transactional Consultation History
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    case_id INTEGER, 
                    role TEXT, 
                    content TEXT, 
                    timestamp TEXT,
                    tokens_used INTEGER DEFAULT 0
                 )''')
    
    # Table 4: Digital Jurisprudence Library
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    size TEXT, 
                    pages INTEGER, 
                    indexed_date TEXT,
                    full_text_status TEXT DEFAULT 'Processed'
                 )''')
    
    conn.commit()
    conn.close()

def db_register_user_full(email, username, password=""):
    """Comprehensive registration logic with automated chamber initialization."""
    if not email: return
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Atomic Insertion
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_on) VALUES (?,?,?,?)", 
              (email, username, password, now_ts))
    
    # Auto-Chamber Creation
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_on) VALUES (?,?,?)", 
                  (email, "Primary Consultation Chamber", now_ts))
    
    conn.commit(); conn.close()

def db_verify_vault_access(email, password):
    """Secure lookup in the local SQL Vault."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=? AND status='Active'", (email, password))
    res = c.fetchone(); conn.close()
    return res[0] if res else None

def db_log_transaction(email, case_name, role, content):
    """Persistent logging of every consultation message."""
    if not email or not content: return
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    case_id_res = c.fetchone()
    
    if case_id_res:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (case_id_res[0], role, content, ts))
        conn.commit()
    conn.close()

def db_fetch_historical_context(email, case_name):
    """Retrieves full chat history for UI rendering and context injection."""
    if not email: return []
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    query = '''
        SELECT h.role, h.content FROM history h 
        JOIN cases c ON h.case_id = c.id 
        WHERE c.email=? AND c.case_name=? 
        ORDER BY h.id ASC
    '''
    c.execute(query, (email, case_name))
    records = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
    conn.close(); return records

init_omnipotent_db()

# ==============================================================================
# 3. SERVICE ARCHITECTURE: AI, VOICE, & SMTP GATEWAY
# ==============================================================================

@st.cache_resource
def load_analytical_intelligence():
    """Initializes the Gemini 1.5 Flash Model with Senior Advocate Parameters."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        GOOGLE_API_KEY=API_KEY, 
        temperature=0.1,
        max_output_tokens=4000,
        top_p=0.95
    )

def inject_neural_voice(text, lang_code):
    """Injects a JavaScript Audio Synthesis Layer for high-quality voice feedback."""
    clean_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_blob = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var utterance = new SpeechSynthesisUtterance('{clean_text}');
            utterance.lang = '{lang_code}';
            utterance.pitch = 1.0;
            utterance.rate = 1.05;
            utterance.volume = 1.0;
            window.speechSynthesis.speak(utterance);
        }})();
    </script>
    """
    components.html(js_blob, height=0)

def dispatch_secure_email_report(target_email, case_title, chat_log):
    """Full SMTP Gateway implementation for dispatching legal briefs."""
    try:
        smtp_u = st.secrets["EMAIL_USER"]
        smtp_p = st.secrets["EMAIL_PASS"]
        
        brief_body = f"OFFICIAL LEGAL BRIEF FROM ALPHA APEX\n"
        brief_body += f"CASE IDENTIFIER: {case_title}\n"
        brief_body += f"DATE GENERATED: {datetime.date.today()}\n"
        brief_body += "="*40 + "\n\n"
        
        for entry in chat_log:
            header = "ASSISTANT COUNSEL" if entry['role'] == 'assistant' else "CLIENT"
            brief_body += f"[{header}]: {entry['content']}\n\n"
            
        brief_body += "\n" + "="*40 + "\nDISCLAIMER: AI-generated summaries require human review."
        
        mail = MIMEMultipart()
        mail['From'] = f"Alpha Apex Intelligence <{smtp_u}>"
        mail['To'] = target_email
        mail['Subject'] = f"Legal Consultation Brief: {case_title}"
        mail.attach(MIMEText(brief_body, 'plain'))
        
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(smtp_u, smtp_p)
        session.send_message(mail)
        session.quit()
        return True
    except Exception as exc:
        st.error(f"MAIL GATEWAY ERROR: {exc}"); return False

def sync_jurisprudence_library():
    """Deep-scans the project data directory and synchronizes PDF metadata to SQL."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    known_docs = [r[0] for r in c.execute("SELECT name FROM documents").fetchall()]
    
    if os.path.exists(DATA_FOLDER):
        for entry in os.listdir(DATA_FOLDER):
            if entry.lower().endswith(".pdf") and entry not in known_docs:
                f_path = os.path.join(DATA_FOLDER, entry)
                try:
                    pdf_handle = PdfReader(f_path)
                    f_size = f"{os.path.getsize(f_path)/1024:.2f} KB"
                    f_date = datetime.datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO documents (name, size, pages, indexed_date) VALUES (?,?,?,?)", 
                              (entry, f_size, len(pdf_handle.pages), f_date))
                except Exception as doc_err:
                    st.warning(f"Could not index {entry}: {doc_err}")
                    continue
    conn.commit(); conn.close()

# ==============================================================================
# 4. AUTHENTICATION & PUBLIC GATEWAY HANDSHAKE
# ==============================================================================
try:
    auth_secrets = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f: json.dump({"web": auth_secrets}, f)
    
    portal_auth = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='alpha_apex_omnipotence_session',
        cookie_key='omnipotence_secure_access_2026',
        redirect_uri=auth_secrets['redirect_uris'][0],
    )
    portal_auth.check_authentification()
except Exception as auth_crit:
    st.error(f"AUTHENTICATION ARCHITECTURE FAILURE: {auth_crit}"); st.stop()

# ==============================================================================
# 5. UI MODULES: LEGAL CHAMBERS, LIBRARY, & SETTINGS
# ==============================================================================

def render_omnipotent_chambers():
    """Main workstation for legal consultation with side-by-side voice input."""
    languages = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        st.caption("Omnipotence Edition v21.0")
        
        # Shader Controller
        st.subheader("🎨 UI Shader Engine")
        ui_mode = st.radio("Shader Selection", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_omnipotence_shaders(ui_mode)
        
        st.divider()
        st.subheader("🏛️ Consultation Protocol")
        target_lang = st.selectbox("🌐 Lexical Language", list(languages.keys()))
        l_code = languages[target_lang]
        
        st.divider()
        st.subheader("📁 Case Navigator")
        cur_email = st.session_state.user_email
        db_conn = sqlite3.connect(SQL_DB_FILE); db_c = db_conn.cursor()
        available_cases = [r[0] for r in db_c.execute("SELECT case_name FROM cases WHERE email=?", (cur_email,)).fetchall()]
        db_conn.close()
        
        st.session_state.active_chamber = st.selectbox("Active Chamber", available_cases if available_cases else ["Primary Consultation Chamber"])
        
        if st.button("➕ Create New Case"):
            st.session_state.spawn_case = True
            
        if st.session_state.get('spawn_case'):
            new_id = st.text_input("Case Identifier")
            if st.button("Confirm Init") and new_id:
                db_conn = sqlite3.connect(SQL_DB_FILE); db_c = db_conn.cursor()
                db_c.execute("INSERT INTO cases (email, case_name, created_on) VALUES (?,?,?)", 
                             (cur_email, new_id, datetime.datetime.now().strftime("%Y-%m-%d")))
                db_conn.commit(); db_conn.close()
                st.session_state.spawn_case = False; st.rerun()

        st.divider()
        if st.button("📧 Email Brief"):
            log_to_send = db_fetch_historical_context(cur_email, st.session_state.active_chamber)
            if dispatch_secure_email_report(cur_email, st.session_state.active_chamber, log_to_send):
                st.toast("Legal Brief Dispatched Successfully!"); time.sleep(1)

        if st.button("🚪 Hard System Logout"):
            for session_key in list(st.session_state.keys()): del st.session_state[session_key]
            portal_auth.logout(); st.rerun()

    # --- MAIN VIEWPORT: CONSULTATION ROOM ---
    st.header(f"💼 Case Room: {st.session_state.active_chamber}")
    st.info("System optimized for Pakistan Penal Code (PPC) and Civil Procedure Code (CPC) analysis.")

    # Render Persistent Transactional History
    transaction_log = db_fetch_historical_context(st.session_state.user_email, st.session_state.active_chamber)
    for msg in transaction_log:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    st.write("") # Visual Spacing
    
    # --- RESTORED: SIDE-BY-SIDE PROMPT & VOICE ---
    input_column_layout = st.columns([0.82, 0.18])
    
    with input_column_layout[0]:
        user_inquiry = st.text_input(
            "Legal Fact Input", 
            placeholder="Type your legal query or facts here...", 
            label_visibility="collapsed", 
            key="master_text_input"
        )
    
    with input_column_layout[1]:
        # Speech to text component placed precisely adjacent to text field
        v_inquiry = speech_to_text(
            language=l_code, 
            key='omni_mic', 
            just_once=True, 
            use_container_width=True
        )

    # Master Input Concatenation
    active_prompt = v_inquiry or user_inquiry

    if active_prompt:
        # Step 1: SQL Persistence
        db_log_transaction(st.session_state.user_email, st.session_state.active_chamber, "user", active_prompt)
        
        with st.chat_message("user"):
            st.write(active_prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Statutes & Jurisprudence..."):
                try:
                    # Advanced IRAC Prompt Engineering
                    prompt_logic = (
                        "Persona: You are a Senior Advocate of the High Court of Pakistan. "
                        "Task: Analyze the user's query with extreme legal precision. "
                        "Strict Structure: Use IRAC (Issue, Rule, Analysis, Conclusion). "
                        "Citations: Cite relevant sections of PPC, CrPC, CPC, or QSO where applicable. "
                        f"Target Language: {target_lang}. \n"
                        f"Inquiry: {active_prompt}"
                    )
                    
                    ai_result = load_analytical_intelligence().invoke(prompt_logic).content
                    st.markdown(ai_result)
                    
                    # Step 2: SQL Persistence for AI Response
                    db_log_transaction(st.session_state.user_email, st.session_state.active_chamber, "assistant", ai_result)
                    
                    # Step 3: Synthesis Trigger
                    inject_neural_voice(ai_result, l_code)
                    st.rerun()
                except Exception as ai_err:
                    st.error(f"ANALYTICAL FAILURE: {ai_err}")

def render_omnipotent_library():
    """Restored: Complete Digital Asset Management Dashboard."""
    st.header("📚 Virtual Jurisprudence Library")
    st.write("Authorized legal documents and statutes are indexed here for RAG-based analysis.")
    
    if st.button("🔄 Rescan Local /data Directory"):
        sync_jurisprudence_library(); st.rerun()
        
    db_conn = sqlite3.connect(SQL_DB_FILE); db_c = db_conn.cursor()
    lib_data = db_c.execute("SELECT name, size, pages, indexed_date FROM documents").fetchall()
    db_conn.close()
    
    if lib_data:
        st.table(pd.DataFrame(lib_data, columns=["Filename", "File Size", "Pages", "Sync Date"]))
    else:
        st.warning("Jurisprudence Library is currently empty. Please upload PDFs to the /data folder.")

def render_entry_portal():
    """RESTORED: High-Volume Multi-Authentication Entry Portal."""
    st.title("⚖️ Alpha Apex Public Gateway")
    st.markdown("### Public Legal Intelligence Access Point")
    
    # Primary Login Method: Google OAuth 2.0
    st.write("To move to **Production**, click the login button below.")
    google_profile = portal_auth.login()
    
    if google_profile:
        st.session_state.connected = True
        st.session_state.user_email = google_profile['email']
        st.session_state.username = google_profile.get('name', 'Advocate')
        db_register_user_full(st.session_state.user_email, st.session_state.username)
        st.rerun()

    st.divider()
    st.subheader("Sovereign Vault Access")
    
    portal_tabs = st.tabs(["🔐 Vault Login", "📝 Register New Vault"])
    
    with portal_tabs[0]:
        v_email = st.text_input("Vault Email Identifier")
        v_pass = st.text_input("Vault Security Key", type="password")
        if st.button("Authorize Vault Entry"):
            v_name = db_verify_vault_access(v_email, v_pass)
            if v_name:
                st.session_state.connected = True
                st.session_state.user_email = v_email
                st.session_state.username = v_name
                st.rerun()
            else:
                st.error("ACCESS DENIED: Invalid Vault Credentials.")
            
    with portal_tabs[1]:
        st.info("Local Vault registration establishes a sovereign identity on our private database.")
        reg_email = st.text_input("Primary Email")
        reg_name = st.text_input("Full Professional Name")
        reg_pass = st.text_input("Define Security Key", type="password")
        if st.button("Establish Vault Account"):
            db_register_user_full(reg_email, reg_name, reg_pass)
            st.success("VAULT ACCOUNT CREATED. Proceed to the Login tab.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE (MAIN LOOP)
# ==============================================================================

if "connected" not in st.session_state: st.session_state.connected = False

# Auto-recovery logic for returning sessions
if not st.session_state.connected:
    try:
        check_u = portal_auth.check_authentification()
        if check_u:
            st.session_state.connected = True
            st.session_state.user_email = check_u['email']
            st.session_state.username = check_u.get('name', 'Advocate')
            st.rerun()
    except: pass

# Global Router Logic
if not st.session_state.connected:
    render_entry_portal()
else:
    # Authenticated Navigation
    nav_route = st.sidebar.radio("Main Navigation", ["Legal Chambers", "Jurisprudence Library", "System About"])
    
    if nav_route == "Legal Chambers":
        render_omnipotent_chambers()
    elif nav_route == "Jurisprudence Library":
        render_omnipotent_library()
    else:
        st.header("ℹ️ Alpha Apex Development Credentials")
        st.markdown("""
        The Alpha Apex system is a specialized Legal LLM Orchestration framework developed to provide 
        statutory analysis and IRAC-structured legal summaries.
        """)
        st.divider()
        dev_team = [
            {"Developer": "Saim Ahmed", "Focus": "System Architecture & Public Handshake"},
            {"Developer": "Huzaifa Khan", "Focus": "Analytical Model Tuning & IRAC Logic"},
            {"Developer": "Mustafa Khan", "Focus": "SQL RDBMS Persistence & Vault Logic"},
            {"Developer": "Ibrahim Sohail", "Focus": "UI Shader Engine & Voice Synthesis"},
            {"Developer": "Daniyal Faraz", "Focus": "SMTP Gateway & Quality Assurance"}
        ]
        st.table(dev_team)

# ==============================================================================
# END OF SCRIPT - 500+ LINES OF OMNIPOTENCE PRODUCTION CODE
# ==============================================================================

