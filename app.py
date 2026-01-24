__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
import sqlite3
import glob
import time
import pandas as pd
import datetime
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from PyPDF2 import PdfReader
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate

# ==============================================================================
# 1. SYSTEM CONFIGURATION
# ==============================================================================

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except KeyError:
    st.error("Missing GOOGLE_API_KEY in Streamlit Secrets")
    st.stop()

DATA_FOLDER = "data" 
DB_PATH = "./chroma_db"
SQL_DB_FILE = "advocate_ai_v3.db"
MODEL_NAME = "gemini-2.0-flash"

# ==============================================================================
# 2. UI STYLING & JS
# ==============================================================================

st.set_page_config(page_title="Alpha Apex", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-bottom: 150px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #333; }
    .mic-box {
        display: flex;
        align-items: center;
        justify-content: center;
        padding-top: 38px;
    }
    [data-testid="stMarkdownContainer"] p {
        font-family: 'Segoe UI', 'Tahoma', sans-serif;
        font-size: 1.1rem;
    }
    /* Professional Black Sidebar Styling */
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

def play_voice_js(text, lang_code='en-US'):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    is_urdu = True if (lang_code == 'ur-PK' or bool(re.search(r'[\u0600-\u06FF]', safe_text))) else False

    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            function setVoice() {{
                var voices = window.speechSynthesis.getVoices();
                if ({str(is_urdu).lower()}) {{
                    msg.lang = 'ur-PK';
                    var v = voices.find(v => v.lang.includes('ur') or v.lang.includes('hi'));
                    if (v) msg.voice = v;
                }} else {{
                    msg.lang = 'en-US';
                }}
                window.speechSynthesis.speak(msg);
            }}
            if (window.speechSynthesis.getVoices().length !== 0) {{ setVoice(); }}
            else {{ window.speechSynthesis.onvoiceschanged = setVoice; }}
        </script>
    """
    components.html(js_code, height=0)

def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.01)

# ==============================================================================
# 3. DATABASE (SQLITE) - SCALABLE LOCAL VERSION
# ==============================================================================

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    
    # Check for password column and add if missing
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
    
    # Ensure every user has at least one case to prevent index errors
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

def db_get_cases(email):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT case_name FROM cases WHERE email=? ORDER BY id DESC", (email,))
    cases = [row[0] for row in c.fetchall()]
    conn.close()
    return cases if cases else ["General Consultation"]

def db_rename_case(email, old_name, new_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE cases SET case_name = ? WHERE email = ? AND case_name = ?", (new_name, email, old_name))
    conn.commit()
    conn.close()

def db_create_case(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, case_name, datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", (res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC", (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

def db_clear_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE case_id IN (SELECT id FROM cases WHERE email=? AND case_name=?)", (email, case_name))
    conn.commit()
    conn.close()

init_sql_db()

# ==============================================================================
# 4. EMAIL & AI UTILS
# ==============================================================================

def send_email_report(receiver_email, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        
        report_content = f"Legal Consultation Report: {case_name}\n"
        report_content += "="*30 + "\n\n"
        for m in history:
            role = "Counsel" if m['role'] == 'assistant' else "Client"
            report_content += f"[{role}]: {m['content']}\n\n"

        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Legal AI <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Case Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

@st.cache_resource
def load_models():
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME, 
        temperature=0.3, 
        google_api_key=API_KEY,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )
    embed = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embed

ai_engine, vector_embedder = load_models()

def sync_knowledge_base():
    if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
    pdfs = glob.glob(f"{DATA_FOLDER}/*.pdf") + glob.glob(f"{DATA_FOLDER}/*.PDF")
    if not pdfs: return None, "No PDFs found"
    
    if os.path.exists(DB_PATH):
        return Chroma(persist_directory=DB_PATH, embedding_function=vector_embedder), "Connected to index"
    else:
        chunks = []
        for p in pdfs:
            loader = PyPDFLoader(p)
            chunks.extend(loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)))
        return Chroma.from_documents(chunks, vector_embedder, persist_directory=DB_PATH), "Indexed"

if "law_db" not in st.session_state:
    db_inst, _ = sync_knowledge_base()
    st.session_state.law_db = db_inst

# ==============================================================================
# 5. AUTHENTICATION & LOGIN/SIGNUP UI
# ==============================================================================

try:
    config_dict = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f:
        json.dump({"web": config_dict}, f)
    my_uri = config_dict['redirect_uris'][0]
except KeyError:
    st.error("Missing google_auth in Streamlit Secrets")
    st.stop()

authenticator = Authenticate(
    'client_secret.json', 
    my_uri, 
    'advocate_ai_cookie',
    'legal_app_secret_key', 
    30
)

authenticator.check_authenticity()
if st.session_state.get('connected'):
    user_info = st.session_state.get('user_info', {})
    if 'email' in user_info:
        st.session_state.user_email = user_info.get('email')
        st.session_state.username = user_info.get('name', "Counsel")
        st.session_state.logged_in = True
        db_register_user(st.session_state.user_email, st.session_state.username)

if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

def login_signup_page():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("# Alpha Apex AI")
        with st.container(border=True):
            t1, t2 = st.tabs(["Google Login", "Email Access"])
            with t1: 
                authenticator.login()
            with t2:
                auth_mode = st.radio("Select Mode", ["Login", "Signup"], horizontal=True)
                email_in = st.text_input("Email", key="email_field")
                pass_in = st.text_input("Password", type="password", key="pass_field")
                
                if auth_mode == "Signup":
                    name_in = st.text_input("Full Name", key="name_field")
                    if st.button("Create Account"):
                        if email_in and pass_in and name_in:
                            db_register_user(email_in, name_in, pass_in)
                            st.success("Account created! Now login above.")
                        else:
                            st.warning("All fields are required.")
                else:
                    if st.button("Sign In"):
                        username = db_check_login(email_in, pass_in)
                        if username:
                            st.session_state.logged_in = True
                            st.session_state.user_email = email_in
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")

# ==============================================================================
# 6. CHAMBERS INTERFACE
# ==============================================================================

def render_chambers_page():
    langs = {"English": "en-US", "Urdu (اردو)": "ur-PK"}

    with st.sidebar:
        st.header(f"Counsel {st.session_state.username}")
        target_lang = st.selectbox("Language", list(langs.keys()))
        lang_code = langs[target_lang]
        st.divider()
        
        cases = db_get_cases(st.session_state.user_email)
        
        if "active_case" not in st.session_state or st.session_state.active_case not in cases:
            st.session_state.active_case = cases[0]
            
        sel = st.selectbox("Case Files", cases, index=cases.index(st.session_state.active_case))
        
        if sel != st.session_state.active_case:
            st.session_state.active_case = sel
            st.session_state.messages = db_load_history(st.session_state.user_email, sel)
            st.rerun()
        
        if st.button("New Case"):
            db_create_case(st.session_state.user_email, f"Case {len(cases)+1}")
            st.rerun()

        if st.button("Clear Chat History"):
            db_clear_history(st.session_state.user_email, st.session_state.active_case)
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.connected = False
            st.rerun()

    st.title(f"Case File: {st.session_state.active_case}")

    if "messages" not in st.session_state:
        st.session_state.messages = db_load_history(st.session_state.user_email, st.session_state.active_case)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    c_text, c_mic = st.columns([10, 1])
    with c_text:
        text_in = st.chat_input(f"Consult in {target_lang}...")
    with c_mic:
        voice_in = speech_to_text(language=lang_code, key='mic_chambers', just_once=True)

    final_in = voice_in or text_in

    if final_in:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_in)
        st.session_state.messages.append({"role": "user", "content": final_in})
        
        with st.chat_message("user"):
            st.markdown(final_in)
        
        with st.chat_message("assistant"):
            p, res = st.empty(), ""
            ctx = ""
            if st.session_state.law_db:
                docs = st.session_state.law_db.as_retriever(search_kwargs={"k": 4}).invoke(final_in)
                ctx = "\n\n".join([d.page_content for d in docs])
            
            prompt = f"""
            Role: High Court Advocate. 
            Format: IRAC. 
            Lang: {target_lang}. 
            No emojis.
            Context: {ctx}
            Query: {final_in}
            """
            
            try:
                ai_out = ai_engine.invoke(prompt).content
                for chunk in stream_text(ai_out):
                    res += chunk
                    p.markdown(res + "▌")
                p.markdown(res)
                
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                if voice_in:
                    play_voice_js(res, lang_code)
            except Exception as e:
                st.error(f"Error: {e}")

# ==============================================================================
# 8. PAGES
# ==============================================================================

def render_library_page():
    st.title("Legal Library")
    if st.button("Sync Library"):
        db_inst, msg = sync_knowledge_base()
        st.session_state.law_db = db_inst
        st.success(msg)

def render_team_page():
    st.title("Team")
    st.write("Alpha Apex Contributors.")

# ==============================================================================
# 9. EXECUTION
# ==============================================================================

if not st.session_state.logged_in:
    login_signup_page()
else:
    nav = st.sidebar.radio("Navigate", ["Chambers", "Library", "Team"])
    if nav == "Chambers": render_chambers_page()
    elif nav == "Library": render_library_page()
    else: render_team_page()
