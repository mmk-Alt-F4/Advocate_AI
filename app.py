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
# 1. SYSTEM CONFIGURATION & COMPATIBILITY FIX
# ==============================================================================

# Secure way to fetch keys on deployment
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except KeyError:
    st.error("Missing 'GOOGLE_API_KEY' in Streamlit Secrets!")
    st.stop()

DATA_FOLDER = "data" 
DB_PATH = "./chroma_db"
SQL_DB_FILE = "advocate_ai_v3.db"
MODEL_NAME = "gemini-2.5-flash"

# ==============================================================================
# 2. UI STYLING & JS
# ==============================================================================

st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

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
    /* Sidebar Styling - UPDATED TO BLACK */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #333;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

def play_voice_js(text, lang_code='en-US'):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    # Auto-detect Urdu if not strictly provided, but prefer the lang_code arg
    if lang_code == 'ur-PK' or bool(re.search(r'[\u0600-\u06FF]', safe_text)):
        is_urdu = True
        lang = 'ur-PK'
    else:
        is_urdu = False
        lang = 'en-US'

    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            function setVoice() {{
                var voices = window.speechSynthesis.getVoices();
                if ({str(is_urdu).lower()}) {{
                    msg.lang = 'ur-PK';
                    var v = voices.find(v => v.lang.includes('ur') || v.lang.includes('hi'));
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
# 3. DATABASE (SQLITE)
# ==============================================================================

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_register_user(email, username):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (email, username, datetime.datetime.now().strftime("%Y-%m-%d")))
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

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

init_sql_db()

# ==============================================================================
# 4. EMAIL & UTILITY FUNCTIONS
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
        # Fallback to console if sidebar context issue arises
        print(f"Email Error: {e}")
        return False

# ==============================================================================
# 5. AI & KNOWLEDGE BASE
# ==============================================================================

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
    if not pdfs: return None, "No PDFs found."
    
    if os.path.exists(DB_PATH):
        return Chroma(persist_directory=DB_PATH, embedding_function=vector_embedder), "Connected to existing index."
    else:
        chunks = []
        for p in pdfs:
            loader = PyPDFLoader(p)
            chunks.extend(loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)))
        return Chroma.from_documents(chunks, vector_embedder, persist_directory=DB_PATH), "Successfully Indexed."

if "law_db" not in st.session_state:
    db_inst, _ = sync_knowledge_base()
    st.session_state.law_db = db_inst

# ==============================================================================
# 6. AUTHENTICATION (DUAL MODE)
# ==============================================================================

try:
    config_dict = dict(st.secrets["google_auth"])
    secret_data = {"web": config_dict}
    with open('client_secret.json', 'w') as f:
        json.dump(secret_data, f)
    my_uri = config_dict['redirect_uris'][0]
except KeyError:
    st.error("Missing 'google_auth' in Streamlit Secrets!")
    st.stop()

authenticator = Authenticate(
    'client_secret.json', 
    my_uri, 
    'advocate_ai_cookie',
    'legal_app_secret_key', 
    30
)

if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

def login_page():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("# ⚖️ Alpha Apex AI")
        with st.container(border=True):
            t1, t2 = st.tabs(["Google Login", "Email Login"])
            with t1: 
                authenticator.login()
            with t2:
                e = st.text_input("Email")
                if st.button("Enter"):
                    if "@" in e:
                        st.session_state.logged_in = True
                        st.session_state.user_email = e
                        st.session_state.username = e.split("@")[0].title()
                        db_register_user(e, st.session_state.username)
                        st.rerun()

# ==============================================================================
# 7. CHAMBERS INTERFACE
# ==============================================================================

def render_chambers_page():
    # Focused Pakistani Languages
    langs = {
        "English": "en-US",
        "Urdu (اردو)": "ur-PK",
        "Sindhi (سنڌي)": "sd-PK",
        "Punjabi (پنجابی)": "pa-PK",
        "Pashto (پښتو)": "ps-PK",
        "Balochi (بلوچی)": "bal-PK"
    }

    with st.sidebar:
        st.header(f"👨‍⚖️ {st.session_state.username}")
        
        # Language Selector
        st.subheader("🌐 Language")
        target_lang = st.selectbox("Choose Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        
        # Case Management
        cases = db_get_cases(st.session_state.user_email)
        if "active_case" not in st.session_state: st.session_state.active_case = cases[0]
        sel = st.selectbox("Case Files", cases, index=cases.index(st.session_state.active_case))
        if sel != st.session_state.active_case:
            st.session_state.active_case = sel
            st.rerun()
        
        with st.expander("Rename Case"):
            nt = st.text_input("New Name", value=st.session_state.active_case)
            if st.button("Confirm Rename"):
                db_rename_case(st.session_state.user_email, st.session_state.active_case, nt)
                st.session_state.active_case = nt
                st.rerun()
        
        if st.button("New Case"):
            db_create_case(st.session_state.user_email, f"Case {len(cases)+1}")
            st.rerun()
        
        st.divider()
        
        # Email Report
        if st.button("📧 Email Conversation"):
            history = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if history:
                with st.spinner("Sending report..."):
                    if send_email_report(st.session_state.user_email, st.session_state.active_case, history):
                        st.success("Sent!")
                    else:
                        st.error("Failed to send.")
            else:
                st.warning("No history found.")
        
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    # --- MAIN CHAT AREA ---
    st.title(f"💼 {st.session_state.active_case}")

    # Quick Actions
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_q = None
    if q_col1.button("⚖️ Infer Legal Path"): quick_q = "What is the recommended legal path forward?"
    if q_col2.button("📜 Give Ruling"): quick_q = "Give a preliminary observation on these facts."
    if q_col3.button("📝 Summarize"): quick_q = "Summarize the legal history of this case."

    # Chat History
    history_container = st.container()
    with history_container:
        history = db_load_history(st.session_state.user_email, st.session_state.active_case)
        for msg in history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Input Area
    input_placeholder = st.container()
    with input_placeholder:
        c_text, c_mic = st.columns([10, 1])
        with c_text:
            text_in = st.chat_input(f"Consult in {target_lang}...")
        with c_mic:
            st.markdown('<div class="mic-box">', unsafe_allow_html=True)
            voice_in = speech_to_text(language=lang_code, start_prompt="🎤", stop_prompt="⏹️", key='mic_chambers', just_once=True)
            st.markdown('</div>', unsafe_allow_html=True)

    final_in = quick_q if quick_q else (voice_in if voice_in else text_in)
    is_v = True if voice_in else False

    if final_in:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_in)
        with history_container:
            with st.chat_message("user"): st.markdown(final_in)
            with st.chat_message("assistant"):
                p, res = st.empty(), ""
                
                # RAG Context Retrieval
                ctx = ""
                if st.session_state.law_db:
                    docs = st.session_state.law_db.as_retriever(search_kwargs={"k": 4}).invoke(final_in)
                    ctx = "\n\n".join([d.page_content for d in docs])
                
                prompt = f"Senior Legal Expert (Pakistan Law). Context: {ctx}\n\nUser Query: {final_in}\n\nRespond ONLY in {target_lang} language/script."
                
                try:
                    ai_out = ai_engine.invoke(prompt).content
                    for chunk in stream_text(ai_out):
                        res += chunk
                        p.markdown(res + "▌")
                    p.markdown(res)
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", res)
                    if is_v: play_voice_js(res, lang_code)
                except Exception as e: st.error(f"Error: {e}")

# ==============================================================================
# 8. LIBRARY PAGE
# ==============================================================================

def render_library_page():
    st.title("📚 Legal Library")
    pdfs = glob.glob(f"{DATA_FOLDER}/*.pdf") + glob.glob(f"{DATA_FOLDER}/*.PDF")
    
    if pdfs:
        library_data = []
        db_exists = os.path.exists(DB_PATH)
        for p in pdfs:
            file_name = os.path.basename(p)
            file_size = round(os.path.getsize(p) / 1024, 2)
            try:
                reader = PdfReader(p)
                pages = len(reader.pages)
            except:
                pages = "N/A"
                
            library_data.append({
                "Document Name": file_name,
                "Pages": pages,
                "Size (KB)": file_size,
                "Status": "✅ Indexed" if db_exists else "⏳ Pending"
            })
        st.table(library_data)
    else:
        st.warning(f"No legal documents found in '{DATA_FOLDER}' folder.")
        
    if st.button("🔄 Sync Library"):
        with st.spinner("Processing documents..."):
            db_inst, msg = sync_knowledge_base()
            st.session_state.law_db = db_inst
            st.success(msg)
            st.rerun()

# ==============================================================================
# 9. TEAM PAGE
# ==============================================================================

def render_team_page():
    st.title("ℹ️ Development Team")
    st.info("Alpha Apex - Advanced Legal Intelligence for Pakistan")
    st.markdown("""
    **Project Contributors:**
    * Saim Ahmed
    * Mustafa Khan
    * Ibrahim Sohail
    * Huzaifa Khan
    * Daniyal Faraz
    """)

# ==============================================================================
# 10. MAIN EXECUTION FLOW
# ==============================================================================

if st.session_state.get('connected'):
    if not st.session_state.get('logged_in'):
        user_info = st.session_state.get('user_info', {})
        st.session_state.user_email = user_info.get('email')
        st.session_state.username = user_info.get('name', "Lawyer")
        st.session_state.logged_in = True
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

if not st.session_state.get('logged_in'):
    login_page()
else:
    with st.sidebar:
        st.markdown("---")
        nav = st.radio("Navigate", ["🏢 Chambers", "📚 Library", "ℹ️ Team"], label_visibility="collapsed")
    
    if nav == "🏢 Chambers":
        render_chambers_page()
    elif nav == "📚 Library":
        render_library_page()
    else:
        render_team_page()
