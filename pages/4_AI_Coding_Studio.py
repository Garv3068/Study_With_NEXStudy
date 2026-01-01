import streamlit as st
import google.generativeai as genai
import os
import datetime
import json
from supabase import create_client, Client

# ---------------- Page config ----------------
st.set_page_config(page_title="AI Coding Studio", page_icon="💻", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("assets/image.png"):
    st.image("assets/image.png", width=150)
elif os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("💻 AI Coding Studio")
st.caption("Generate code, debug errors, and build projects with AI assistance.")

# ---------------- Supabase Client ----------------
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None

supabase = get_supabase()

# ---------------- Session State ----------------
user = st.session_state.get("user")
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "debug_analysis" not in st.session_state:
    st.session_state.debug_analysis = ""

# ---------------- Database Functions ----------------
def fetch_saved_code():
    """Fetch saved_code array from Supabase profiles"""
    if not user or not supabase: return []
    try:
        res = supabase.table("profiles").select("saved_code").eq("id", user["id"]).single().execute()
        if res.data and res.data.get("saved_code"):
            return res.data["saved_code"]
    except: pass
    return []

def save_code_to_db(title, language, code, type="snippet"):
    """Append new code to saved_code in Supabase"""
    if not user or not supabase: return False
    try:
        current_data = fetch_saved_code()
        entry = {
            "title": title if title else f"Untitled {language} Snippet",
            "language": language,
            "code": code,
            "type": type,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        current_data.append(entry)
        
        # Update DB
        supabase.table("profiles").update({"saved_code": current_data}).eq("id", user["id"]).execute()
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

# ---------------- Gemini Initialization ----------------
@st.cache_resource
def init_gemini(api_key_input):
    key = api_key_input
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
    
    if not key:
        return None

    try:
        genai.configure(api_key=key)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    if user:
        st.success(f"Logged in: {user.get('email')}")
    else:
        st.warning("Guest Mode. Sign in to save code.")

    api_key_input = None
    if "GEMINI_API_KEY" in st.secrets:
        api_key_input = st.secrets["GEMINI_API_KEY"]
    else:
        api_key_input = st.text_input("Enter Gemini API Key:", type="password")

gemini_model = init_gemini(api_key_input)

# ---------------- TABS ----------------
tab_gen, tab_debug, tab_lib = st.tabs(["⚙️ Generator", "🐞 Debugger", "📚 Code Library"])

# =======================================================
# TAB 1: CODE GENERATOR
# =======================================================
with tab_gen:
    st.markdown("### 🛠️ Generate Code")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        lang = st.selectbox("Language:", ["Python", "JavaScript", "HTML/CSS", "C++", "Java", "SQL"])
        details = st.text_area("Describe what you need:", placeholder="e.g. A snake game using pygame...")
        
        if st.button("🚀 Generate Code", type="primary"):
            if not details:
                st.warning("Describe the code first.")
            elif not gemini_model:
                st.error("API Key missing.")
            else:
                with st.spinner("Coding..."):
                    prompt = f"Write {lang} code for: {details}. Provide ONLY code inside markdown block."
                    try:
                        res = gemini_model.generate_content(prompt)
                        st.session_state.generated_code = res.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        if st.session_state.generated_code:
            st.markdown("### Result")
            st.markdown(st.session_state.generated_code)
            
            # Extract code content for saving (simple cleaning)
            code_content = st.session_state.generated_code
            
            if user:
                save_title = st.text_input("Snippet Name (for saving):", placeholder="My Script")
                if st.button("💾 Save to Library", key="save_gen"):
                    if save_code_to_db(save_title, lang, code_content, "generated"):
                        st.success("Saved!")

# =======================================================
# TAB 2: DEBUGGER
# =======================================================
with tab_debug:
    st.markdown("### 🐞 Intelligent Debugger")
    
    col_d1, col_d2 = st.columns([1, 1])
    
    with col_d1:
        buggy_code = st.text_area("Paste Buggy Code:", height=300)
        error_msg = st.text_area("Error Message (Optional):")
        
        if st.button("🔍 Fix Bug", type="primary"):
            if not buggy_code:
                st.warning("Paste code.")
            elif not gemini_model:
                st.error("API Key missing.")
            else:
                with st.spinner("Analyzing..."):
                    prompt = f"""
                    Debug this code.
                    Code:
                    {buggy_code}
                    
                    Error: {error_msg}
                    
                    Output: 
                    1. What is wrong.
                    2. Corrected Code.
                    """
                    try:
                        res = gemini_model.generate_content(prompt)
                        st.session_state.debug_analysis = res.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col_d2:
        if st.session_state.debug_analysis:
            st.markdown("### Analysis")
            st.markdown(st.session_state.debug_analysis)
            
            if user:
                if st.button("💾 Save Solution to Library", key="save_debug"):
                    if save_code_to_db(f"Debug Fix: {datetime.datetime.now().strftime('%H:%M')}", "Mixed", st.session_state.debug_analysis, "debug"):
                        st.success("Saved!")

# =======================================================
# TAB 3: LIBRARY
# =======================================================
with tab_lib:
    st.markdown("### 📚 My Code Snippets")
    if user and supabase:
        saved_snippets = fetch_saved_code()
        if saved_snippets:
            for i, snippet in enumerate(reversed(saved_snippets)):
                with st.expander(f"{snippet.get('language')} | {snippet.get('title')} ({snippet.get('date')})"):
                    st.markdown(snippet.get('code'))
                    st.download_button("Download", snippet.get('code'), f"Snippet_{i}.txt", key=f"dl_c_{i}")
        else:
            st.info("No saved code yet.")
    else:
        st.warning("Log in to view your code library.")
