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
# 1. GLOBAL UI ENGINE & DYNAMIC SHADER SYSTEM
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Sovereign Enterprise Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_full_spectrum_shaders(theme_mode):
    """
    Restores the complete CSS architecture.
    Includes smooth transitions, custom chat bubble geometry, 
    and high-contrast typography for legal reading.
    """
    shader_css = """
    <style>
        /* Global Animation Layer */
        * { transition: background-color 0.6s cubic-bezier(0.4, 0, 0.2, 1), color 0.6s ease !important; }
        
        /* App Main Body */
        .stApp { transition: background 0.6s ease !important; }
        
        /* Chat Message Restoration */
        .stChatMessage {
            padding: 1.5rem !important;
            margin-bottom: 1.2rem !important;
            border-radius: 18px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
        }
        
        /* Button & Sidebar Polish */
        .stButton>button {
            border-radius: 12px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.7px !important;
            text-transform: uppercase !important;
        }
        
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(0,0,0,0.15) !important;
            padding-top: 2rem !important;
        }
    </style>
    """
    
    if theme_mode == "Dark Mode":
        shader_css += """
        <style>
            .stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important; color: #c9d1d9 !important; }
            [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d !important; }
            .stChatMessage { background-color: #1c2128 !important; border: 1px solid #30363d !important; }
            h1, h2, h3, h4, h5, h6, p, span { color: #f0f6fc !important; }
            .stTextInput>div>div>input { background-color: #0d1117 !important; color: white !important; }
        </style>
        """
    else:
        shader_css += """
        <style>
            .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%) !important; color: #1f2328 !important; }
            [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #d0d7de !important; }
            .stChatMessage { background-color: #ffffff !important; border: 1px solid #d0d7de !important; }
            .stTextInput>div>div>input { background-color: #ffffff !important; color: #1f2328 !important; }
        </style>
        """
    st.markdown(shader_css, unsafe_allow_html=True)

# Configuration Constants
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_full_restore_v18.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    try:
        os.makedirs(DATA_FOLDER)
    except Exception as e:
        st.error(f"File System Alert: Could not initialize data directory. {e}")

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE LAYER (SQLITE3)
# ==============================================================================

def init_relational_db():
    """Restores the complete multi-table relational schema."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Table 1: User Identity Vault
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    username TEXT, 
                    password TEXT, 
                    joined_date TEXT,
                    account_type TEXT DEFAULT 'Public'
                 )''')
    
    # Table 2: Case Management Records
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email TEXT, 
                    case_name TEXT, 
                    created_at TEXT
                 )''')
    
    # Table 3: Transactional History (Chat Logs)
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    case_id INTEGER, 
                    role TEXT, 
                    content TEXT, 
                    timestamp TEXT
                 )''')
    
    # Table 4: Legal Document Library
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    size TEXT, 
                    pages INTEGER, 
                    indexed_on TEXT
                 )''')
    
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    """Atomically registers users and initializes their default legal chamber."""
    if not email: return
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert User
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", 
              (email, username, password, now))
    
    # Verify and Create Default Consultation Case
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                  (email, "General Consultation", now))
    
    conn.commit(); conn.close()

def db_verify_vault(email, password):
    """Local auth check for non-Google users."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone(); conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    """Ensures message persistence across app reruns and server refreshes."""
    if not email or not content: return
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
    """Fetches the full interaction log for the current session context."""
    if not email: return []
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute('''SELECT history.role, history.content FROM history 
                 JOIN cases ON history.case_id = cases.id 
                 WHERE cases.email=? AND cases.case_name=? 
                 ORDER BY history.id ASC''', (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]; conn.close()
    return data

init_relational_db()

# ==============================================================================
# 3. SERVICE ARCHITECTURE: AI, VOICE, AND SMTP
# ==============================================================================

@st.cache_resource
def load_analytical_engine():
    """Initializes Gemini with specific legal parameters and token limits."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY, 
        temperature=0.2,
        max_output_tokens=3500
    )

def play_voice_synthesis(text, lang_code):
    """Injects JavaScript to handle real-time browser-based voice feedback."""
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_payload = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{safe_text}');
        msg.lang = '{lang_code}';
        msg.rate = 1.0;
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_payload, height=0)

def send_legal_report(recipient, case_name, history):
    """RESTORED: SMTP Gateway for dispatching case reports via email."""
    try:
        s_email = st.secrets["EMAIL_USER"]
        s_pass = st.secrets["EMAIL_PASS"]
        
        report = f"ALPHA APEX CASE REPORT\nCase: {case_name}\nDate: {datetime.date.today()}\n\n"
        for m in history:
            role = "AI COUNSEL" if m['role'] == 'assistant' else "CLIENT"
            report += f"{role}: {m['content']}\n\n"
            
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Intelligence <{s_email}>"
        msg['To'] = recipient
        msg['Subject'] = f"Legal Consult: {case_name}"
        msg.attach(MIMEText(report, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(s_email, s_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Dispatcher Error: {e}")
        return False

def sync_library_assets():
    """RESTORED: Scans the /data folder and updates the SQL document registry."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    existing = [r[0] for r in c.execute("SELECT name FROM documents").fetchall()]
    
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith(".pdf") and filename not in existing:
                path = os.path.join(DATA_FOLDER, filename)
                try:
                    pdf = PdfReader(path)
                    sz = f"{os.path.getsize(path)/1024:.1f} KB"
                    ts = datetime.datetime.now().strftime("%Y-%m-%d")
                    c.execute("INSERT INTO documents (name, size, pages, indexed_on) VALUES (?,?,?,?)", 
                              (filename, sz, len(pdf.pages), ts))
                except: continue
    conn.commit(); conn.close()

# ==============================================================================
# 4. AUTHENTICATION & PUBLIC PRODUCTION GATEWAY
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f: json.dump({"web": auth_config}, f)
    
    authenticator = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='alpha_apex_v18_production_cookie',
        cookie_key='restored_enterprise_key_2026',
        redirect_uri=auth_config['redirect_uris'][0],
    )
    authenticator.check_authentification()
except Exception as e:
    st.error(f"Auth Infrastructure Alert: {e}"); st.stop()

# ==============================================================================
# 5. CORE UI MODULES: CHAMBERS, LIBRARY, & VAULT
# ==============================================================================

def render_legal_chambers():
    """Restores the full-featured collaborative consultation room."""
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        
        # Shader Controller
        st.subheader("🎨 UI Configuration")
        mode = st.radio("Shader Mode", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_full_spectrum_shaders(mode)
        
        st.divider()
        st.subheader("🏛️ Session Protocol")
        target_lang = st.selectbox("🌐 Interaction Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        use_irac = st.toggle("Enforce IRAC Analysis", value=True)
        
        st.divider()
        st.subheader("📁 Case Navigator")
        u_email = st.session_state.user_email
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        cases = [r[0] for r in c.execute("SELECT case_name FROM cases WHERE email=?", (u_email,)).fetchall()]
        conn.close()
        
        st.session_state.active_case = st.selectbox("Active Chamber", cases if cases else ["General Consultation"])
        
        if st.button("➕ Initialize New Case"):
            st.session_state.show_case_creator = True
            
        if st.session_state.get('show_case_creator'):
            c_name = st.text_input("New Identifier")
            if st.button("Confirm") and c_name:
                conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
                c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                          (u_email, c_name, datetime.datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close()
                st.session_state.show_case_creator = False
                st.rerun()

        st.divider()
        if st.button("📧 Email Current Log"):
            current_hist = db_load_history(u_email, st.session_state.active_case)
            if send_legal_report(u_email, st.session_state.active_case, current_hist):
                st.success("Report Dispatched.")

        if st.button("🚪 Hard Session Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            authenticator.logout(); st.rerun()

    # --- MAIN CONSULTATION WINDOW ---
    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # Restore History View
    history_log = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for msg in history_log:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User Input Interface
    query = st.chat_input("State the facts of the matter for analysis...")
    v_query = speech_to_text(language=lang_code, key='v_input', just_once=True)
    
    final_query = v_query or query
    
    if final_query:
        # Save to SQL
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_query)
        with st.chat_message("user"): st.write(final_query)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Pakistani Statutes & Case Law..."):
                try:
                    irac_prompt = ""
                    if use_irac:
                        irac_prompt = "Structure strictly using IRAC: Issue, Rule (citing PPC/CrPC/CPC/QSO), Analysis, Conclusion."
                    
                    full_p = f"Persona: Senior High Court Advocate. {irac_prompt}\nLang: {target_lang}\nQuery: {final_query}"
                    
                    ai_response = load_analytical_engine().invoke(full_p).content
                    st.markdown(ai_response)
                    
                    # Save AI response
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", ai_response)
                    
                    # Audio synthesis
                    play_voice_synthesis(ai_response, lang_code)
                    st.rerun()
                except Exception as e:
                    st.error(f"AI Consultation Error: {e}")

def render_library():
    """Restores the digital law library metadata dashboard."""
    st.header("📚 Digital Asset Library")
    st.info("The library indexes all PDF references located in the /data project directory.")
    
    if st.button("🔄 Rescan Library Folder"):
        sync_library_assets(); st.rerun()
        
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    docs = c.execute("SELECT name, size, pages, indexed_on FROM documents").fetchall()
    conn.close()
    
    if docs:
        st.table(pd.DataFrame(docs, columns=["Document Name", "File Size", "Total Pages", "Date Indexed"]))
    else:
        st.warning("No legal references currently indexed.")

def render_portal():
    """RESTORED: The multi-auth entry portal with Signup and Google OAuth."""
    st.title("⚖️ Alpha Apex Public Portal")
    st.markdown("### Secure Legal Intelligence Gateway")
    
    # Google OAuth Trigger
    google_user = authenticator.login()
    if google_user:
        st.session_state.connected = True
        st.session_state.user_email = google_user['email']
        st.session_state.username = google_user.get('name', 'Advocate')
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

    st.divider()
    t1, t2 = st.tabs(["🔐 Vault Login", "📝 Register New Vault"])
    
    with t1:
        e = st.text_input("Email Identifier")
        p = st.text_input("Security Password", type="password")
        if st.button("Authorize Vault Access"):
            uname = db_verify_vault(e, p)
            if uname:
                st.session_state.connected = True
                st.session_state.user_email = e; st.session_state.username = uname; st.rerun()
            else: st.error("Access Denied: Invalid Credentials")
            
    with t2:
        st.subheader("RESTORED: Local Registration")
        re = st.text_input("Registration Email")
        ru = st.text_input("Full Professional Name")
        rp = st.text_input("Establish Password", type="password")
        if st.button("Create Vault Account"):
            db_register_user(re, ru, rp)
            st.success("Account Established. Please use Vault Login tab.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE (MAIN LOOP)
# ==============================================================================

if "connected" not in st.session_state: st.session_state.connected = False

# Session Recovery Logic
if not st.session_state.connected:
    try:
        u_rec = authenticator.check_authentification()
        if u_rec:
            st.session_state.connected = True
            st.session_state.user_email = u_rec['email']
            st.session_state.username = u_rec.get('name', 'Advocate')
            st.rerun()
    except: pass

# Router
if not st.session_state.connected:
    render_portal()
else:
    nav = st.sidebar.radio("Navigation", ["Chambers", "Law Library", "About"])
    if nav == "Chambers": render_legal_chambers()
    elif nav == "Law Library": render_library()
    else:
        st.header("ℹ️ Alpha Apex Development")
        st.table([
            ["Lead Architect", "Saim Ahmed"], ["AI Systems", "Huzaifa Khan"], 
            ["DB Engineer", "Mustafa Khan"], ["UX Design", "Ibrahim Sohail"], ["QA Lead", "Daniyal Faraz"]
        ])

# ==============================================================================
# END OF SCRIPT - RESTORED TO 450+ LINES
# ==============================================================================
