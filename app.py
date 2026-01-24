# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 29.0 (STRICT PROCEDURAL LOGIC - NO CONDENSING)
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
import re
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ==============================================================================
# 1. PERMANENT SOVEREIGN SHADER ARCHITECTURE (DARK ONLY)
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_leviathan_shaders():
    """
    Injects a permanent Dark Mode CSS architecture.
    Expanded with explicit animation and element-specific styling.
    """
    shader_css = """
    <style>
        /* Global Reset */
        * { transition: background-color 0.8s ease, color 0.8s ease !important; }
        
        /* Permanent Dark Canvas */
        .stApp { 
            background-color: #020617 !important; 
            color: #f1f5f9 !important; 
        }

        /* Sidebar Glassmorphism */
        [data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.98) !important;
            border-right: 2px solid #38bdf8 !important;
            box-shadow: 10px 0 20px rgba(0,0,0,0.5) !important;
        }

        /* Chat Geometry */
        .stChatMessage {
            border-radius: 20px !important;
            padding: 2.5rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
            background-color: rgba(30, 41, 59, 0.3) !important;
        }

        /* Typography */
        h1, h2, h3, h4, h5 { 
            color: #38bdf8 !important; 
            font-weight: 900 !important; 
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .stMarkdown { line-height: 1.8; }

        /* Button Architecture */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: #38bdf8 !important;
            border: 1px solid #38bdf8 !important;
            height: 3.5rem !important;
            width: 100% !important;
            transition: all 0.4s ease !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 10px 20px rgba(56, 189, 248, 0.3) !important;
            background-color: #38bdf8 !important;
            color: #0f172a !important;
        }

        /* Input Interaction */
        .stTextInput>div>div>input {
            background-color: rgba(255,255,255,0.05) !important;
            color: #ffffff !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 10px !important;
        }

        /* Scrollbar Design */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }

        /* Hide Streamlit Native UI */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (EXPLICIT TRANSACTIONAL)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v29.db"
DATA_FOLDER = "law_library_assets"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_leviathan_db():
    """Builds the comprehensive SQL schema with explicit transactional tables."""
    connection = sqlite3.connect(SQL_DB_FILE)
    cursor = connection.cursor()
    
    # User Registry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY, 
            full_name TEXT, 
            vault_key TEXT, 
            registration_date TEXT,
            membership_tier TEXT DEFAULT 'Senior Counsel',
            account_status TEXT DEFAULT 'Active',
            total_queries INTEGER DEFAULT 0
        )
    ''')
    
    # Case Chambers with Status Logic
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chambers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            owner_email TEXT, 
            chamber_name TEXT, 
            init_date TEXT,
            chamber_type TEXT DEFAULT 'General Litigation',
            case_status TEXT DEFAULT 'Active',
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    # Message Logs with Metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            chamber_id INTEGER, 
            sender_role TEXT, 
            message_body TEXT, 
            ts_created TEXT,
            token_count INTEGER DEFAULT 0
        )
    ''')
    
    # Jurisprudence Asset Vault
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS law_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            filename TEXT, 
            filesize_kb REAL, 
            page_count INTEGER, 
            sync_timestamp TEXT,
            asset_status TEXT DEFAULT 'Verified'
        )
    ''')
    
    # System Usage Telemetry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_telemetry (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            event_type TEXT,
            description TEXT,
            event_timestamp TEXT
        )
    ''')
    
    connection.commit()
    connection.close()

def db_log_event(email, event_type, desc):
    """Explicitly logs system events for admin telemetry."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp)
        VALUES (?, ?, ?, ?)
    ''', (email, event_type, desc, ts))
    conn.commit()
    conn.close()

def db_create_vault_user(email, name, password):
    """Registers users into the local SQL vault."""
    if not email:
        return False
    if not password:
        return False
    
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    now_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute('''
            INSERT INTO users (email, full_name, vault_key, registration_date) 
            VALUES (?, ?, ?, ?)
        ''', (email, name, password, now_ts))
        
        cursor.execute('''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        ''', (email, "General Litigation Chamber", now_ts))
        
        conn.commit()
        conn.close()
        db_log_event(email, "REGISTRATION", "User account successfully created")
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
    except Exception as e:
        conn.close()
        return False

def db_verify_vault_access(email, password):
    """Local credential verification."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    
    query = "SELECT full_name FROM users WHERE email=? AND vault_key=?"
    cursor.execute(query, (email, password))
    
    auth_result = cursor.fetchone()
    conn.close()
    
    if auth_result:
        db_log_event(email, "LOGIN", "Successful authentication")
        return auth_result[0]
    else:
        return None

def db_update_case_status(chamber_id, new_status):
    """Explicit logic for updating case workflow status."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE chambers SET case_status = ? WHERE id = ?", (new_status, chamber_id))
    conn.commit()
    conn.close()

def db_log_consultation(email, chamber_name, role, content):
    """Saves legal consultation transactions."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    
    select_query = "SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?"
    cursor.execute(select_query, (email, chamber_name))
    chamber_id_row = cursor.fetchone()
    
    if chamber_id_row:
        c_id = chamber_id_row[0]
        ts_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tok_est = len(content.split())
        
        cursor.execute('''
            INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created, token_count) 
            VALUES (?, ?, ?, ?, ?)
        ''', (c_id, role, content, ts_now, tok_est))
        
        if role == "user":
            cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        
        conn.commit()
    
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    """Retrieves context-specific logs."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    
    sql_string = '''
        SELECT m.sender_role, m.message_body FROM message_logs m 
        JOIN chambers c ON m.chamber_id = c.id 
        WHERE c.owner_email=? AND c.chamber_name=? 
        ORDER BY m.id ASC
    '''
    
    cursor.execute(sql_string, (email, chamber_name))
    data_rows = cursor.fetchall()
    
    history_list = []
    for row in data_rows:
        history_list.append({"role": row[0], "content": row[1]})
        
    conn.close()
    return history_list

init_leviathan_db()

# ==============================================================================
# 3. CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    """Initializes Gemini with strictly tuned legal parameters."""
    api_key_str = st.secrets["GOOGLE_API_KEY"]
    model_instance = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        google_api_key=api_key_str, 
        temperature=0.15,
        max_output_tokens=4000
    )
    return model_instance

def dispatch_legal_brief_smtp(target_email, chamber_name, history_data):
    """Enterprise SMTP Gateway for automated brief delivery."""
    try:
        s_user = st.secrets["EMAIL_USER"]
        s_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        cur_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body_text = f"ALPHA APEX OFFICIAL LEGAL BRIEF\n"
        body_text += f"CHAMBER IDENTIFIER: {chamber_name}\n"
        body_text += f"GENERATED AT: {cur_ts}\n"
        body_text += "="*60 + "\n\n"
        
        for entry in history_data:
            role_label = "ADVOCATE" if entry['role'] == 'assistant' else "CLIENT"
            sanitized_content = re.sub(r'[*#_]', '', entry['content'])
            body_text += f"[{role_label}]: {sanitized_content}\n\n"
            
        email_msg = MIMEMultipart()
        email_msg['From'] = f"Alpha Apex Chambers <{s_user}>"
        email_msg['To'] = target_email
        email_msg['Subject'] = f"Case Briefing: {chamber_name}"
        
        part_content = MIMEText(body_text, 'plain', 'utf-8')
        email_msg.attach(part_content)
        
        smtp_session = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_session.starttls()
        smtp_session.login(s_user, s_pass)
        smtp_session.send_message(email_msg)
        smtp_session.quit()
        
        return True
    except Exception as smtp_err:
        st.error(f"Critical SMTP Fault: {smtp_err}")
        return False

def synchronize_law_library():
    """Explicit file system scan for PDF jurisprudence indexing."""
    db_conn = sqlite3.connect(SQL_DB_FILE)
    db_cursor = db_conn.cursor()
    
    db_cursor.execute("SELECT filename FROM law_assets")
    existing_records = db_cursor.fetchall()
    
    indexed_filenames = []
    for record in existing_records:
        indexed_filenames.append(record[0])
    
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            is_pdf = filename.lower().endswith(".pdf")
            not_indexed = filename not in indexed_filenames
            
            if is_pdf and not_indexed:
                file_path_full = os.path.join(DATA_FOLDER, filename)
                try:
                    pdf_reader_obj = PdfReader(file_path_full)
                    size_in_kb = os.path.getsize(file_path_full) / 1024
                    total_pages = len(pdf_reader_obj.pages)
                    ts_sync = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    db_cursor.execute('''
                        INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) 
                        VALUES (?, ?, ?, ?)
                    ''', (filename, size_in_kb, total_pages, ts_sync))
                except Exception as file_err:
                    continue
                    
    db_conn.commit()
    db_conn.close()

# ==============================================================================
# 4. UI: SOVEREIGN CHAMBERS (VOICE RECORDING ENABLED)
# ==============================================================================

def render_chamber_workstation():
    """Main Workstation UI with non-condensed logic blocks."""
    lexicon_map = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }
    
    apply_leviathan_shaders()
    
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; margin-top: -30px;'>⚖️</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>ALPHA APEX</h3>", unsafe_allow_html=True)
        st.caption("<p style='text-align: center;'>Leviathan Production Suite v29</p>", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🌐 Global Lexicon")
        language_selection = st.selectbox("Select Consultation Language", list(lexicon_map.keys()))
        language_code = lexicon_map[language_selection]
        
        st.divider()
        st.subheader("📁 Case Navigator")
        search_query_term = st.text_input("🔍 Search Chambers", "").lower()
        
        user_email_id = st.session_state.user_email
        db_connection_sb = sqlite3.connect(SQL_DB_FILE)
        db_cursor_sb = db_connection_sb.cursor()
        
        chamber_query_sql = "SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0"
        db_cursor_sb.execute(chamber_query_sql, (user_email_id,))
        chamber_data_rows = db_cursor_sb.fetchall()
        
        chamber_name_list = []
        for row in chamber_data_rows:
            chamber_name_list.append(row[0])
            
        db_connection_sb.close()
        
        filtered_chambers = []
        for c_name in chamber_name_list:
            if search_query_term in c_name.lower():
                filtered_chambers.append(c_name)
        
        if len(filtered_chambers) > 0:
            st.session_state.current_chamber = st.selectbox("Active Chamber", filtered_chambers)
        else:
            st.session_state.current_chamber = st.selectbox("Active Chamber", chamber_name_list)
        
        # Action Buttons Columnar Layout
        btn_col_1, btn_col_2 = st.columns(2)
        with btn_col_1:
            if st.button("➕ New Case"):
                st.session_state.trigger_new_case_workflow = True
        with btn_col_2:
            if st.button("📧 Brief"):
                hist_to_send = db_fetch_chamber_history(user_email_id, st.session_state.current_chamber)
                success_mail = dispatch_legal_brief_smtp(user_email_id, st.session_state.current_chamber, hist_to_send)
                if success_mail:
                    st.sidebar.success("Brief Dispatched")
        
        if st.session_state.get('trigger_new_case_workflow'):
            input_new_name = st.text_input("New Chamber Identifier")
            if st.button("Register Case") and input_new_name:
                conn_new = sqlite3.connect(SQL_DB_FILE)
                curr_new = conn_new.cursor()
                curr_date_str = str(datetime.date.today())
                curr_new.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)", 
                                 (user_email_id, input_new_name, curr_date_str))
                conn_new.commit()
                conn_new.close()
                st.session_state.trigger_new_case_workflow = False
                st.rerun()

        st.divider()
        if st.button("🚪 Terminate Session"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.username = None
            st.rerun()

    # --- MAIN CONSULTATION AREA ---
    st.header(f"💼 CASE: {st.session_state.current_chamber}")
    st.write("---")
    
    active_history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for entry_log in active_history:
        role_type = entry_log["role"]
        body_content = entry_log["content"]
        with st.chat_message(role_type):
            st.write(body_content)

    st.write("") 
    
    # Input Processing Subsystem
    layout_columns = st.columns([0.82, 0.18])
    with layout_columns[0]:
        user_text_prompt = st.chat_input("Enter Legal Query or Strategy Request...")
    with layout_columns[1]:
        # Speech Capture Integration
        user_voice_prompt = speech_to_text(
            language=language_code, 
            key='leviathan_voice_capture', 
            just_once=True, 
            use_container_width=True
        )

    # Input Conflict Resolution Logic
    if user_text_prompt:
        consolidated_input = user_text_prompt
    elif user_voice_prompt:
        consolidated_input = user_voice_prompt
    else:
        consolidated_input = None

    if consolidated_input:
        is_duplicate = False
        if "last_processed_query" in st.session_state:
            if st.session_state.last_processed_query == consolidated_input:
                is_duplicate = True
        
        if not is_duplicate:
            st.session_state.last_processed_query = consolidated_input
            
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", consolidated_input)
            
            with st.chat_message("user"):
                st.write(consolidated_input)
            
            with st.chat_message("assistant"):
                with st.spinner("Processing Jurisprudential Logic..."):
                    try:
                        prompt_template = f"""
                        SYSTEM PERSONA: Senior High Court Advocate.
                        CONSTRAINTS: 
                        1. If input is a greeting, respond with professional legal courtesy.
                        2. If input is a case/legal issue, provide IRAC analysis.
                        3. Cite Pakistan Penal Code or Constitution where relevant.
                        4. Output Language must be: {language_selection}.
                        
                        USER INPUT: {consolidated_input}
                        """
                        
                        engine = get_analytical_engine()
                        ai_raw_output = engine.invoke(prompt_template)
                        final_ai_text = ai_raw_output.content
                        
                        st.markdown(final_ai_text)
                        
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", final_ai_text)
                        st.rerun()
                    except Exception as ai_err:
                        st.error(f"Inference Engine Error: {ai_err}")

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL (AUTHENTICATION GATEWAY)
# ==============================================================================

def render_sovereign_portal():
    """Secure entry gateway for Alpha Apex."""
    apply_leviathan_shaders()
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    st.markdown("#### Enterprise Legal Intelligence Infrastructure")
    
    tab_login, tab_register = st.tabs(["🔐 Authorized Login", "📝 System Registration"])
    
    with tab_login:
        st.subheader("Credential Verification")
        input_email = st.text_input("Vault Identity (Email)")
        input_pass = st.text_input("Security Key", type="password")
        
        if st.button("Authenticate & Enter"):
            auth_name = db_verify_vault_access(input_email, input_pass)
            if auth_name:
                st.session_state.logged_in = True
                st.session_state.user_email = input_email
                st.session_state.username = auth_name
                st.rerun()
            else:
                st.error("Authentication Failure: Invalid Identity or Key.")
                
    with tab_register:
        st.subheader("New Identity Initialization")
        reg_email = st.text_input("Account Email Address")
        reg_name = st.text_input("Full Professional Name")
        reg_key = st.text_input("Establish Security Key", type="password")
        
        if st.button("Execute Registration"):
            creation_success = db_create_vault_user(reg_email, reg_name, reg_key)
            if creation_success:
                st.success("Identity Established. You may now proceed to Login.")
            else:
                st.error("Registration Fault: Identity already exists or Database Error.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE & ADMIN TELEMETRY
# ==============================================================================

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in == False:
    render_sovereign_portal()
else:
    # Navigation Router
    nav_selection = st.sidebar.radio("Sovereign Navigation Hub", ["Chambers", "Law Library", "System Admin"])
    
    if nav_selection == "Chambers":
        render_chamber_workstation()
        
    elif nav_selection == "Law Library":
        apply_leviathan_shaders()
        st.header("📚 Digital Jurisprudence Assets")
        
        if st.button("🔄 Execute Vault Sync"):
            synchronize_law_library()
            st.rerun()
        
        conn_lib = sqlite3.connect(SQL_DB_FILE)
        asset_df = pd.read_sql_query("SELECT filename, filesize_kb, page_count, sync_timestamp FROM law_assets", conn_lib)
        conn_lib.close()
        
        if asset_df.empty:
            st.warning("Digital Vault is currently empty. Please upload assets to the library folder.")
        else:
            st.dataframe(asset_df, use_container_width=True)
            
    elif nav_selection == "System Admin":
        apply_leviathan_shaders()
        st.header("🛡️ System Administration Console")
        
        conn_adm = sqlite3.connect(SQL_DB_FILE)
        user_data_df = pd.read_sql_query("SELECT full_name, email, registration_date, total_queries FROM users", conn_adm)
        chamber_data_df = pd.read_sql_query("SELECT owner_email, chamber_name, case_status, init_date FROM chambers", conn_adm)
        telemetry_df = pd.read_sql_query("SELECT user_email, event_type, description, event_timestamp FROM system_telemetry ORDER BY event_id DESC LIMIT 10", conn_adm)
        conn_adm.close()
        
        # Admin Metrics View
        col_adm_1, col_adm_2 = st.columns(2)
        with col_adm_1:
            st.subheader("Registered Counsel")
            st.dataframe(user_data_df, hide_index=True)
        with col_adm_2:
            st.subheader("Active Chambers")
            st.dataframe(chamber_data_df, hide_index=True)
            
        st.divider()
        st.subheader("Recent System Telemetry")
        st.table(telemetry_df)
        
        st.divider()
        st.subheader("Architectural Board")
        architects_list = [
            {"Name": "Saim Ahmed", "Responsibility": "Logic & System Architecture"},
            {"Name": "Huzaifa Khan", "Responsibility": "Analytical AI Model Tuning"},
            {"Name": "Mustafa Khan", "Responsibility": "Relational Data Persistence"},
            {"Name": "Ibrahim Sohail", "Responsibility": "UI/UX & Shader Development"},
            {"Name": "Daniyal Faraz", "Responsibility": "Quality Assurance & Telemetry"}
        ]
        st.table(architects_list)

# ==============================================================================
# SCRIPT END - TOTAL FUNCTIONAL LINE COUNT: 520+
# ==============================================================================
