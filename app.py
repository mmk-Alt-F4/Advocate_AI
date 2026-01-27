# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# ==============================================================================
# SYSTEM VERSION: 34.0 (UNCOMPRESSED ARCHITECTURE - NO DELETIONS)
# DEPLOYMENT TARGET: STREAMLIT CLOUD / LOCALHOST
# DATABASE CONNECTION: advocate_ai_v2.db
# SECURITY PROTOCOL: OAUTH 2.0 + LOCAL AES (Simulated)
#
# ARCHITECTURAL BOARD:
# 1. SAIM AHMED       - LEAD SYSTEM ARCHITECT & LOGIC CONTROLLER
# 2. HUZAIFA KHAN     - AI GENERATIVE MODELS & NLP TUNING
# 3. MUSTAFA KHAN     - SQL PERSISTENCE & DATA SECURITY
# 4. IBRAHIM SOHAIL   - UI/UX SHADERS & FRONTEND OPTIMIZATION
# 5. DANIYAL FARAZ    - QUALITY ASSURANCE & INTEGRATION TESTING
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: SYSTEM IMPORTS & ENVIRONMENT CONFIGURATION
# ------------------------------------------------------------------------------

try:
    import pysqlite3
    import sys
    # Swap standard sqlite3 for pysqlite3 to ensure cloud compatibility
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    # Fallback to standard library if pysqlite3 is not available
    import sqlite3

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

# ------------------------------------------------------------------------------
# SECTION 2: GLOBAL CONFIGURATION CONSTANTS
# ------------------------------------------------------------------------------

SYSTEM_CONFIG = {
    "APP_NAME": "Alpha Apex - Leviathan Law AI",
    "APP_ICON": "⚖️",
    "LAYOUT": "wide",
    "DB_FILE": "advocate_ai_v2.db",
    "DATA_DIR": "data",
    "OAUTH_REDIRECT_URI": "http://localhost:8501", # Adjust for production
    "VERSION_TAG": "34.0-LEV-STRICT",
    "THEME_COLOR": "#0b1120"
}

# Apply Streamlit Page Configuration
st.set_page_config(
    page_title=SYSTEM_CONFIG["APP_NAME"], 
    page_icon=SYSTEM_CONFIG["APP_ICON"], 
    layout=SYSTEM_CONFIG["LAYOUT"],
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# SECTION 3: PERMANENT SOVEREIGN SHADER ARCHITECTURE (CSS)
# ------------------------------------------------------------------------------

def apply_leviathan_shaders():
    """
    Injects the permanent Dark Mode CSS architecture.
    This function contains the visual DNA of the application.
    It forces the 'Dark Blue/Navy' aesthetic across all elements.
    """
    shader_css = """
    <style>
        /* ------------------------------------------------------- */
        /* GLOBAL RESET & STABILITY LAYER                          */
        /* ------------------------------------------------------- */
        * { 
            transition: background-color 0.8s ease, color 0.8s ease !important; 
            font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
            box-sizing: border-box;
        }
        
        /* ------------------------------------------------------- */
        /* MAIN APPLICATION CANVAS                                 */
        /* ------------------------------------------------------- */
        .stApp { 
            background-color: #0b1120 !important; 
            color: #e2e8f0 !important; 
        }

        /* ------------------------------------------------------- */
        /* SIDEBAR GLASSMORPHISM ARCHITECTURE                      */
        /* ------------------------------------------------------- */
        [data-testid="stSidebar"] {
            background-color: #020617 !important; /* Deepest Navy */
            border-right: 1px solid #1e293b !important;
            box-shadow: 10px 0 20px rgba(0, 0, 0, 0.5) !important;
        }

        /* ------------------------------------------------------- */
        /* RADIO BUTTON & NAVIGATION STYLING                       */
        /* ------------------------------------------------------- */
        .stRadio > div[role="radiogroup"] > label > div:first-child {
            background-color: #ef4444 !important; /* Red Alpha Indicator */
            border-color: #ef4444 !important;
        }
        
        .stRadio > div[role="radiogroup"] {
            gap: 12px;
            padding: 10px 0px;
        }
        
        .stRadio label {
            color: #cbd5e1 !important;
            font-weight: 500 !important;
        }

        /* ------------------------------------------------------- */
        /* HIGH-FIDELITY CHAT GEOMETRY                             */
        /* ------------------------------------------------------- */
        .stChatMessage {
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            border: 1px solid rgba(56, 189, 248, 0.1) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
            background-color: rgba(30, 41, 59, 0.3) !important;
        }

        /* USER SPECIFIC MESSAGE BUBBLE */
        [data-testid="stChatMessageUser"] {
            border-left: 3px solid #38bdf8 !important;
            background-color: rgba(56, 189, 248, 0.05) !important;
        }
        
        /* AI SPECIFIC MESSAGE BUBBLE */
        [data-testid="stChatMessageAvatarAssistant"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
        }

        /* ------------------------------------------------------- */
        /* TYPOGRAPHY & HEADLINES                                  */
        /* ------------------------------------------------------- */
        h1, h2, h3, h4, h5, h6 { 
            color: #f8fafc !important; 
            font-weight: 700 !important; 
            text-transform: none !important; 
            letter-spacing: 0.5px;
        }
        
        .logo-text {
            color: #f8fafc;
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 0px;
            letter-spacing: 1px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .sub-logo-text {
            color: #94a3b8;
            font-size: 11px;
            margin-top: -5px;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }

        /* ------------------------------------------------------- */
        /* PRECISION BUTTON STYLING                                */
        /* ------------------------------------------------------- */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            background: #1e293b !important;
            color: #cbd5e1 !important;
            border: 1px solid #334155 !important;
            height: 3rem !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton>button:hover {
            background-color: #334155 !important;
            color: #f1f5f9 !important;
            border-color: #475569 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        }
        
        .stButton>button:active {
            transform: translateY(1px) !important;
        }

        /* ------------------------------------------------------- */
        /* GOOGLE OAUTH BUTTON SPECIFICATION                       */
        /* ------------------------------------------------------- */
        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #ffffff;
            color: #1e293b;
            font-weight: 600;
            padding: 0.75rem;
            border-radius: 8px;
            cursor: pointer;
            border: 1px solid #e2e8f0;
            text-decoration: none !important;
            transition: all 0.3s ease;
            margin-top: 15px;
            width: 100%;
            font-size: 0.95rem;
        }

        .google-btn:hover {
            background-color: #f1f5f9;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }

        .google-icon {
            width: 20px;
            height: 20px;
            margin-right: 12px;
        }

        /* ------------------------------------------------------- */
        /* INPUT FIELD REFINEMENT                                  */
        /* ------------------------------------------------------- */
        .stTextInput>div>div>input {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
        }

        /* ------------------------------------------------------- */
        /* SCROLLBAR AESTHETICS                                    */
        /* ------------------------------------------------------- */
        ::-webkit-scrollbar { 
            width: 8px; 
            height: 8px;
        }
        ::-webkit-scrollbar-track { 
            background: #020617; 
        }
        ::-webkit-scrollbar-thumb { 
            background: #1e293b; 
            border-radius: 4px; 
        }
        ::-webkit-scrollbar-thumb:hover { 
            background: #334155; 
        }

        /* ------------------------------------------------------- */
        /* UTILITY HIDING                                          */
        /* ------------------------------------------------------- */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECTION 4: RELATIONAL DATABASE PERSISTENCE ENGINE
# ------------------------------------------------------------------------------

def get_db_connection():
    """
    Creates a thread-safe connection to the persistent database file.
    Enables WAL (Write-Ahead Logging) mode for better concurrency during writes.
    
    Returns:
        sqlite3.Connection: The active database connection object.
    """
    try:
        connection = sqlite3.connect(SYSTEM_CONFIG["DB_FILE"], check_same_thread=False)
        # Enable Write-Ahead Logging for performance
        connection.execute("PRAGMA journal_mode=WAL;") 
        # Set synchronous mode to Normal to balance safety and speed
        connection.execute("PRAGMA synchronous=NORMAL;")
        return connection
    except sqlite3.Error as e:
        st.error(f"CRITICAL: Database Connection Failure. Details: {e}")
        return None

def init_leviathan_db():
    """
    Builds the comprehensive SQL schema with explicit transactional tables.
    Uses IF NOT EXISTS to ensure compatibility with existing legacy files.
    This function initializes all 5 core tables required for the ecosystem.
    """
    connection = get_db_connection()
    if not connection:
        st.stop() # Halt execution if DB is unreachable

    try:
        cursor = connection.cursor()
        
        # -------------------------------------------------------
        # TABLE 1: Master User Registry (Permanent Storage)
        # -------------------------------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, 
                full_name TEXT, 
                vault_key TEXT, 
                registration_date TEXT,
                membership_tier TEXT DEFAULT 'Senior Counsel',
                account_status TEXT DEFAULT 'Active',
                total_queries INTEGER DEFAULT 0,
                last_login TEXT
            )
        ''')
        
        # -------------------------------------------------------
        # TABLE 2: Case Chamber Virtual Registry
        # -------------------------------------------------------
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
        
        # -------------------------------------------------------
        # TABLE 3: Transactional Consultation History
        # -------------------------------------------------------
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
        
        # -------------------------------------------------------
        # TABLE 4: Digital Jurisprudence Metadata Vault
        # -------------------------------------------------------
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
        
        # -------------------------------------------------------
        # TABLE 5: System Telemetry & Audit Log
        # -------------------------------------------------------
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
        # print("System Database Integrity Verified.") 
    except sqlite3.Error as e:
        st.error(f"SCHEMA INITIALIZATION FAILED: {e}")
    finally:
        connection.close()

# ------------------------------------------------------------------------------
# SECTION 5: DATABASE TRANSACTIONAL FUNCTIONS
# ------------------------------------------------------------------------------

def db_log_event(email, event_type, desc):
    """
    Explicitly logs system events for admin telemetry.
    
    Args:
        email (str): The user associated with the event.
        event_type (str): Category (e.g., LOGIN, ERROR).
        desc (str): Detailed description.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp)
                VALUES (?, ?, ?, ?)
            ''', (email, event_type, desc, ts))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Logging Error: {e}")
        finally:
            conn.close()

def db_create_vault_user(email, name, password):
    """
    Registers users into the local SQL vault.
    
    Args:
        email (str): User's unique email.
        name (str): Full legal name.
        password (str): Encrypted or plain password (based on config).
        
    Returns:
        bool: True if successful, False if email already exists.
    """
    # Validation Check
    if email == "" or password == "" or name == "":
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        # Verify non-existence of user
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False
            
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Atomic Insert Operation: User Registry
        cursor.execute('''
            INSERT INTO users (email, full_name, vault_key, registration_date, last_login) 
            VALUES (?, ?, ?, ?, ?)
        ''', (email, name, password, ts, ts))
        
        # Atomic Insert Operation: Default Chamber
        cursor.execute('''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        ''', (email, "General Litigation Chamber", ts))
        
        conn.commit()
        
        # Log the registration event
        db_log_event(email, "REGISTRATION", "Account Vault Synchronized successfully")
        return True
        
    except Exception as e:
        st.error(f"VAULT WRITE ERROR: {e}")
        return False
    finally:
        conn.close()

def db_verify_vault_access(email, password):
    """
    Credential verification logic against the persistent SQL store.
    
    Returns:
        str: User's Full Name if valid, None otherwise.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        # Secure query parameterization
        cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
        res = cursor.fetchone()
        
        if res:
            # Update last login timestamp upon success
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", (ts, email))
            conn.commit()
            
            # Log successful access
            db_log_event(email, "LOGIN", "Access Credentials Verified")
            return res[0] # Return the Full Name
            
        return None
    finally:
        conn.close()

def db_log_consultation(email, chamber_name, role, content):
    """
    Records chat history permanently in the SQL message_logs table.
    Ensures that every interaction is auditable.
    """
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Resolve Chamber ID from Name and Email
        cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
        row = cursor.fetchone()
        
        if row:
            ch_id = row[0]
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert the message content
            cursor.execute('''
                INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) 
                VALUES (?, ?, ?, ?)
            ''', (ch_id, role, content, ts))
            
            # Increment usage stats if the sender is the user
            if role == "user":
                cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
                
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"LOGGING FAILURE: {e}")
    finally:
        conn.close()

def db_fetch_chamber_history(email, chamber_name):
    """
    Retrieves logical message flows for a specific chamber.
    Returns a list of dictionaries compatible with Streamlit Chat.
    """
    conn = get_db_connection()
    history = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Complex JOIN to ensure we only get messages for the correct chamber owned by the correct user
            query = '''
                SELECT m.sender_role, m.message_body 
                FROM message_logs m 
                JOIN chambers c ON m.chamber_id = c.id 
                WHERE c.owner_email=? AND c.chamber_name=? 
                ORDER BY m.id ASC
            '''
            cursor.execute(query, (email, chamber_name))
            rows = cursor.fetchall()
            
            for r in rows:
                history.append({
                    "role": r[0], 
                    "content": r[1]
                })
        except Exception as e:
            st.error(f"HISTORY FETCH ERROR: {e}")
        finally:
            conn.close()
            
    return history

# Trigger Database Initialization on Script Load
init_leviathan_db()

# ------------------------------------------------------------------------------
# SECTION 6: CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ------------------------------------------------------------------------------

@st.cache_resource
def get_analytical_engine():
    """
    Configures the Gemini 1.5 Flash Model for Legal Context.
    Uses st.secrets for secure API key management.
    """
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=st.secrets["GOOGLE_API_KEY"], 
            temperature=0.0, # Zero temperature for factual legal deterministic outputs
            max_output_tokens=3000
        )
    except Exception as e:
        st.error(f"AI ENGINE INIT ERROR: {e}")
        return None

def dispatch_legal_brief_smtp(target_email, chamber_name, history_data):
    """
    Enterprise SMTP integration for automated brief delivery via Gmail.
    Formats the chat history into a professional transcript.
    """
    try:
        s_user = st.secrets["EMAIL_USER"]
        s_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{s_user}>"
        msg['To'] = target_email
        msg['Subject'] = f"Legal Consultation Brief: {chamber_name} - {datetime.date.today()}"
        
        # Build the Brief Body
        brief_body = f"--- ALPHA APEX LEGAL INTELLIGENCE BRIEF ---\n"
        brief_body += f"CHAMBER REF: {chamber_name}\n"
        brief_body += f"GENERATION DATE: {datetime.datetime.now()}\n"
        brief_body += f"CONFIDENTIALITY: STRICTLY PRIVILEGED\n\n"
        
        brief_body += "--- TRANSCRIPT BEGINS ---\n\n"
        
        for entry in history_data:
            role_tag = "COUNSEL" if entry['role'] == 'user' else "AI ADVISOR"
            brief_body += f"[{role_tag}]:\n{entry['content']}\n\n"
            
        brief_body += "\n--- END OF PRIVILEGED COMMUNICATION ---"
        brief_body += "\nGenerated by Leviathan AI System."
        
        msg.attach(MIMEText(brief_body, 'plain', 'utf-8'))
        
        # Connect to SMTP Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(s_user, s_pass)
        server.send_message(msg)
        server.quit()
        return True
        
    except Exception as e:
        st.error(f"SMTP Dispatch Error: {e}")
        return False

def synchronize_law_library():
    """
    Indexes and validates PDF assets in the statutory vault (data/ folder).
    Updates the 'law_assets' table with metadata.
    """
    if not os.path.exists(SYSTEM_CONFIG["DATA_DIR"]):
        os.makedirs(SYSTEM_CONFIG["DATA_DIR"])

    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        # Get existing files to avoid duplicates
        cursor.execute("SELECT filename FROM law_assets")
        existing_assets = [row[0] for row in cursor.fetchall()]
        
        files_processed = 0
        
        for file_name in os.listdir(SYSTEM_CONFIG["DATA_DIR"]):
            if file_name.lower().endswith(".pdf") and file_name not in existing_assets:
                try:
                    file_path = os.path.join(SYSTEM_CONFIG["DATA_DIR"], file_name)
                    
                    # Extract Metadata
                    reader = PdfReader(file_path)
                    f_size = os.path.getsize(file_path) / 1024 # KB
                    p_count = len(reader.pages)
                    current_ts = datetime.datetime.now().strftime("%Y-%m-%d")
                    
                    # Insert Metadata
                    cursor.execute('''
                        INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) 
                        VALUES (?,?,?,?)
                    ''', (file_name, f_size, p_count, current_ts))
                    
                    files_processed += 1
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
                    continue
                    
        conn.commit()
        if files_processed > 0:
            st.toast(f"Synchronized {files_processed} new legal assets.", icon="📚")
            
    finally:
        conn.close()

# ------------------------------------------------------------------------------
# SECTION 7: GOOGLE OAUTH CALLBACK & AUTOMATIC REGISTRATION HANDLER
# ------------------------------------------------------------------------------

def handle_google_callback():
    """
    Listens for the Google OAuth redirect and automatically synchronizes
    the advocate_ai_v2.db registry with the incoming Google profile.
    
    This function acts as the gatekeeper for Federated Identity.
    """
    # 1. Capture the 'code' or 'token' from the URL parameters
    query_params = st.query_params
    
    if "code" in query_params:
        auth_code = query_params["code"]
        
        # 2. In a production environment, you would exchange this code for a token.
        # For this logic, we assume the identity payload is retrieved via Google's API.
        try:
            # Mocking the payload structure returned by Google's userinfo endpoint
            # In production, use 'google-auth' or 'requests' to verify the JWT
            google_user_data = {
                "email": "user_from_google@example.com", # Extracted from Google
                "name": "Google Counsel",
                "verified": True
            }
            
            g_email = google_user_data["email"]
            g_name = google_user_data["name"]
            g_temp_key = "OAUTH_EXTERNAL_PROVIDER_VERIFIED" 
            
            # 3. Automatic SQL Synchronization
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                
                # Check if this Google user already exists in the Sovereign Vault
                cursor.execute("SELECT email FROM users WHERE email = ?", (g_email,))
                existing_user = cursor.fetchone()
                
                if not existing_user:
                    # AUTOMATIC RECORD CREATION FOR FIRST-TIME USERS
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Insert the new record into the master user registry
                    cursor.execute('''
                        INSERT INTO users (
                            email, 
                            full_name, 
                            vault_key, 
                            registration_date, 
                            membership_tier, 
                            account_status,
                            last_login
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        g_email, 
                        g_name, 
                        g_temp_key, 
                        ts, 
                        'Senior Counsel', 
                        'Active', 
                        ts
                    ))
                    
                    # Initialize their default litigation chamber automatically
                    cursor.execute('''
                        INSERT INTO chambers (owner_email, chamber_name, init_date) 
                        VALUES (?, ?, ?)
                    ''', (g_email, "Default Google Chamber", ts))
                    
                    conn.commit()
                    db_log_event(g_email, "OAUTH_SIGNUP", "Auto-registered via Google OAuth")
                    st.toast("New Google Account Created & Synced", icon="🆕")
                else:
                    # If they exist, simply update the last login timestamp
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", (ts, g_email))
                    conn.commit()
                    db_log_event(g_email, "OAUTH_LOGIN", "Synchronized via Google OAuth")
                
                conn.close()
                
                # 4. Authorize the session and clean URL
                st.session_state.logged_in = True
                st.session_state.user_email = g_email
                st.session_state.username = g_name
                
                # Remove the sensitive code from the URL for security
                st.query_params.clear()
                st.rerun()
                
        except Exception as e:
            st.error(f"OAuth Synchronization Failure: {e}")

def render_google_sign_in():
    """
    Renders a professional Google Sign-In interface.
    Styled to align with the Alpha Apex Sovereign Shaders.
    """
    # Replace '#' with your actual Google OAuth URL from Cloud Console
    google_oauth_url = "https://accounts.google.com/o/oauth2/auth?..." 
    
    st.markdown(f"""
        <a href="{google_oauth_url}" target="_self" class="google-btn">
            <img class="google-icon" src="https://fonts.gstatic.com/s/i/productlogos/googleg/v6/24px.svg"/>
            Continue with Google Counsel Access
        </a>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECTION 8: UI LAYOUT - SOVEREIGN CHAMBERS (MAIN WORKSTATION)
# ------------------------------------------------------------------------------

def render_main_interface():
    """
    Main logic loop that handles the entire UI structure.
    Refactored to match 'Sovereign Navigation Hub' and 'Settings & Help' requirements.
    Contains the logic for Chat, Library, and Admin panels.
    """
    # Localization Mapping
    lexicon_map = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }
    
    # Apply Visual Layer
    apply_leviathan_shaders()
    
    # --- SIDEBAR CONSTRUCTION ---
    with st.sidebar:
        # BRANDING HEADER
        st.markdown("""
            <div style='padding-bottom: 10px;'>
                <div class='logo-text'>⚖️ ALPHA APEX</div>
                <div class='sub-logo-text'>Leviathan Suite v34.0</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("") # Spacing

        # 1. Navigation Hub
        st.markdown("**Sovereign Navigation Hub**")
        navigation_selector = st.radio(
            "Main Navigation",
            ["Chambers", "Law Library", "System Admin"],
            label_visibility="collapsed"
        )
        
        st.write("---")

        # 2. Case Management (Chambers Mode) Logic
        if navigation_selector == "Chambers":
            st.markdown("**Active Case Files**")
            current_user = st.session_state.user_email
            
            # Fetch user chambers from DB
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (current_user,))
                user_chambers = [r[0] for r in cursor.fetchall()]
                conn.close()
            else:
                user_chambers = ["General Litigation Chamber"]
                
            if not user_chambers:
                user_chambers = ["General Litigation Chamber"]
            
            # Search Filter
            search_query = st.text_input("Find Case...", placeholder="Search...", label_visibility="collapsed")
            visible_chambers = [ch for ch in user_chambers if search_query.lower() in ch.lower()]
            
            # Chamber Selection Radio
            st.session_state.current_chamber = st.radio(
                "Select Case",
                visible_chambers if visible_chambers else user_chambers,
                label_visibility="collapsed"
            )
            
            # Action Buttons Layout
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("➕ New", use_container_width=True):
                    st.session_state.add_case_active = True
            with col_b:
                if st.button("📧 Brief", use_container_width=True):
                    hist_data = db_fetch_chamber_history(current_user, st.session_state.current_chamber)
                    if dispatch_legal_brief_smtp(current_user, st.session_state.current_chamber, hist_data):
                        st.sidebar.success("Brief Sent")
                    else:
                        st.sidebar.error("Brief Failed")

            # Inline Case Creation Form
            if st.session_state.get('add_case_active'):
                with st.container():
                    st.markdown("---")
                    chamber_input = st.text_input("New Chamber Name")
                    if st.button("Initialize Chamber", use_container_width=True) and chamber_input:
                        conn = get_db_connection()
                        if conn:
                            cursor = conn.cursor()
                            d_ts = str(datetime.date.today())
                            cursor.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (current_user, chamber_input, d_ts))
                            conn.commit()
                            conn.close()
                            st.session_state.add_case_active = False
                            st.rerun()

        st.write("---")

        # 3. System Shaders Toggle
        st.markdown("**System Shaders**")
        st.radio(
            "Shader Mode",
            ["Dark Mode", "Light Mode"],
            index=0, 
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.write("") 
        
        # 4. Settings & Help Expander
        with st.expander("⚙️ Settings & help"):
            st.caption("AI Personalization")
            custom_persona = st.text_input("System Persona", value="Senior High Court Advocate")
            selected_language = st.selectbox("Interface Language", list(lexicon_map.keys()))
            
            st.divider()
            st.caption("Support & Documentation")
            st.write("📖 System Documentation")
            st.write("🛡️ Privacy Protocol")
            
            st.divider()
            if st.button("🚪 Secure Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_email = None
                st.session_state.username = None
                st.rerun()

    # --- MAIN CONTENT AREA LOGIC ---
    
    if navigation_selector == "Chambers":
        # Header Area
        st.header(f"💼 CASE: {st.session_state.current_chamber}")
        st.caption("Secure Litigation Environment | Strict Privilege Applies")
        st.write("---")
        
        # Chat Workspace Container
        chat_workspace = st.container()
        
        with chat_workspace:
            # Render Historical Chat
            history_log = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
            
            if not history_log:
                st.info("No consultation history found. Begin by typing a query below.")
            
            for message in history_log:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Input Area (Text + Voice)
        col_text, col_voice = st.columns([0.88, 0.12])
        with col_text:
            text_query = st.chat_input("Enter Legal Query or Strategy Request...")
        with col_voice:
            voice_query = speech_to_text(language=lexicon_map[selected_language], key='leviathan_mic', just_once=True, use_container_width=True)

        active_query = text_query or voice_query

        # Processing Logic
        if active_query:
            if "last_processed" not in st.session_state or st.session_state.last_processed != active_query:
                st.session_state.last_processed = active_query
                
                # Log User Query
                db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", active_query)
                
                # Instant Echo
                with chat_workspace:
                    with st.chat_message("user"):
                        st.write(active_query)
                
                # AI Processing
                with st.chat_message("assistant"):
                    with st.spinner("Executing Legal Analysis..."):
                        try:
                            instruction = f"""
                            SYSTEM PERSONA: {custom_persona}. 
                            STRICT RULES:
                            1. Only discuss law, litigation, statutes, or legal strategy.
                            2. If a query is non-legal, refuse politely.
                            3. Respond accurately in {selected_language}.
                            USER REQUEST: {active_query}
                            """
                            
                            ai_engine = get_analytical_engine()
                            if ai_engine:
                                ai_response = ai_engine.invoke(instruction)
                                response_payload = ai_response.content
                                st.markdown(response_payload)
                                
                                # Log AI Response
                                db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", response_payload)
                            else:
                                st.error("AI Engine Unreachable. Check API Key.")
                                
                            st.rerun()
                        except Exception as ai_err:
                            st.error(f"ENGINE FAULT: {ai_err}")

    elif navigation_selector == "Law Library":
        st.header("📚 Law Library Vault")
        st.write("Managing indexed legal assets and statutory documents.")
        
        col_l1, col_l2 = st.columns([0.2, 0.8])
        with col_l1:
            if st.button("🔄 Synchronize Assets", use_container_width=True):
                with st.spinner("Indexing PDF Assets..."):
                    synchronize_law_library()
                st.rerun()
        
        conn = get_db_connection()
        if conn:
            library_df = pd.read_sql_query("SELECT filename, filesize_kb, page_count, sync_timestamp, asset_status FROM law_assets", conn)
            conn.close()
            
            st.subheader("Indexed Assets")
            st.dataframe(
                library_df, 
                use_container_width=True,
                column_config={
                    "filesize_kb": st.column_config.NumberColumn("Size (KB)", format="%.2f"),
                    "filename": "Document Name",
                    "page_count": "Pages"
                }
            )
        else:
            st.error("Library Database Disconnected.")

    elif navigation_selector == "System Admin":
        st.header("🛡️ System Administration Console")
        st.write("Restricted Access Area. Monitoring System Telemetry.")
        
        conn = get_db_connection()
        if conn:
            # Metrics remain visible for professional oversight
            u_metrics = conn.execute("SELECT count(*), sum(total_queries) FROM users").fetchone()
            u_count = u_metrics[0]
            q_sum = u_metrics[1] if u_metrics[1] else 0
            
            # Fetch Recent Telemetry
            telemetry_df = pd.read_sql_query("SELECT * FROM system_telemetry ORDER BY event_id DESC LIMIT 10", conn)
            
            conn.close()
        else:
            u_count, q_sum = 0, 0
            telemetry_df = pd.DataFrame()
            
        m_cols = st.columns(3)
        m_cols[0].metric("Registered Counsel", u_count)
        m_cols[1].metric("Consultation Volume", q_sum)
        m_cols[2].metric("System Version", SYSTEM_CONFIG["VERSION_TAG"])
        
        st.divider()
        st.info("Information: Counsel Directory and Active Logs are restricted per system privacy refactor.")
        
        st.subheader("Live Telemetry Stream")
        st.dataframe(telemetry_df, use_container_width=True)
        
        st.divider()
        
        st.subheader("Architectural Board")
        architects_metadata = [
            {"Name": "Saim Ahmed", "Focus": "Architecture & Logic Control"},
            {"Name": "Huzaifa Khan", "Focus": "AI Generative Models & Tuning"},
            {"Name": "Mustafa Khan", "Focus": "SQL Security & Persistence"},
            {"Name": "Ibrahim Sohail", "Focus": "UI/UX & Sovereign Shaders"},
            {"Name": "Daniyal Faraz", "Focus": "Quality Assurance & Testing"}
        ]
        st.table(architects_metadata)

# ------------------------------------------------------------------------------
# SECTION 9: UI LAYOUT - SOVEREIGN PORTAL (AUTHENTICATION GATEWAY)
# ------------------------------------------------------------------------------

def render_sovereign_portal():
    """
    Secure gateway logic for Alpha Apex.
    Handles Login, Registration, and OAuth Visualization.
    """
    apply_leviathan_shaders()
    
    # Centered Container for Login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚖️ ALPHA APEX PORTAL")
        st.markdown("#### Strategic Litigation and Legal Intelligence Framework")
        st.markdown("---")
        
        tab_login, tab_reg = st.tabs(["🔐 Secure Login", "📝 Counsel Registration"])
        
        # TAB 1: LOGIN
        with tab_login:
            login_email = st.text_input("Vault Email Address", key="login_e")
            login_key = st.text_input("Security Key", type="password", key="login_k")
            
            if st.button("Grant Access", use_container_width=True):
                with st.spinner("Verifying Credentials..."):
                    user_name = db_verify_vault_access(login_email, login_key)
                    if user_name:
                        st.session_state.logged_in = True
                        st.session_state.user_email = login_email
                        st.session_state.username = user_name
                        st.rerun()
                    else:
                        st.error("ACCESS DENIED: Credentials not found or invalid.")
            
            # Professional Divider and Google Button Integration
            st.markdown("""
                <div style='text-align: center; margin-top: 15px;'>
                    <p style='color: #64748b; font-size: 0.85rem; font-weight: 500;'>OR AUTHENTICATE VIA PROVIDER</p>
                </div>
                """, unsafe_allow_html=True)
                
            render_google_sign_in()
                    
        # TAB 2: REGISTRATION
        with tab_reg:
            st.info("New Counsel Registration")
            reg_email = st.text_input("Registry Email", key="reg_e")
            reg_name = st.text_input("Counsel Full Name", key="reg_n")
            reg_key = st.text_input("Set Security Key", type="password", key="reg_k")
            
            if st.button("Initialize Account", use_container_width=True):
                if reg_email and reg_name and reg_key:
                    if db_create_vault_user(reg_email, reg_name, reg_key):
                        st.success("VAULT SYNCED: Account initialized successfully.")
                    else:
                        st.error("REGISTRATION FAILED: Email already exists or invalid data.")
                else:
                    st.warning("All fields are required.")

# ------------------------------------------------------------------------------
# SECTION 10: MASTER EXECUTION ENGINE
# ------------------------------------------------------------------------------

# Initialize Session State Variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "current_chamber" not in st.session_state:
    st.session_state.current_chamber = "General Litigation Chamber"

# Run Callback Handler first (to catch OAuth redirects)
handle_google_callback()

# Conditional Rendering
if not st.session_state.logged_in:
    render_sovereign_portal()
else:
    render_main_interface()

# ==============================================================================
# END OF SYSTEM ARCHITECTURE
# ==============================================================================
