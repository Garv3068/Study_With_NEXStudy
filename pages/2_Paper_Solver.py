import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
from PIL import Image
from supabase import create_client, Client

# ---------------- Page config ----------------
st.set_page_config(page_title="Past Paper Solver", page_icon="📝", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("assets/image.png"):
    st.image("assets/image.png", width=150)
elif os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("📝 Past Paper Solver")
st.caption("Upload an exam paper (PDF or Images) and get a comprehensive solution key.")

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
if "paper_solution" not in st.session_state:
    st.session_state.paper_solution = ""

# ---------------- Database Functions ----------------
def fetch_saved_papers():
    """Fetch saved_papers array from Supabase profiles"""
    if not user or not supabase: return []
    try:
        res = supabase.table("profiles").select("saved_papers").eq("id", user["id"]).single().execute()
        if res.data and res.data.get("saved_papers"):
            return res.data["saved_papers"]
    except: pass
    return []

def save_paper_to_db(solution_text, source_name):
    """Append new solution to saved_papers in Supabase"""
    if not user or not supabase: return False
    try:
        current_data = fetch_saved_papers()
        entry = {
            "title": f"Solution: {source_name}",
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "content": solution_text
        }
        current_data.append(entry)
        
        # Update DB
        supabase.table("profiles").update({"saved_papers": current_data}).eq("id", user["id"]).execute()
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
        return genai.GenerativeModel("gemini-2.5-flash-lite")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    if user:
        st.success(f"Logged in: {user.get('email')}")
    else:
        st.warning("Guest Mode. Sign in to save solutions.")

    api_key_input = None
    if "GEMINI_API_KEY" in st.secrets:
        api_key_input = st.secrets["GEMINI_API_KEY"]
    else:
        api_key_input = st.text_input("Enter Gemini API Key:", type="password")

gemini_model = init_gemini(api_key_input)

# ---------------- Helpers ----------------
def extract_text_from_pdf(uploaded_file):
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
        return ""

def call_gemini(contents):
    if gemini_model is None:
        return {"error": "Gemini API key not configured."}
    try:
        resp = gemini_model.generate_content(contents)
        text = resp.text or ""
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

# ---------------- TABS ----------------
tab_solve, tab_saved = st.tabs(["🚀 Solve New Paper", "📚 Saved Solutions"])

# =======================================================
# TAB 1: SOLVE NEW
# =======================================================
with tab_solve:
    col_upload, col_result = st.columns([1, 2])

    with col_upload:
        st.markdown("### 📤 Upload Paper")
        upload_type = st.radio("File Type:", ["PDF Document", "Images (Pages)"])
        user_context = st.text_area("Instructions:", placeholder="e.g. Solve only Section B")
        
        uploaded_file = None
        uploaded_images = []
        source_name = "Unknown Paper"
        
        if upload_type == "PDF Document":
            uploaded_file = st.file_uploader("Upload Exam PDF:", type=["pdf"])
            if uploaded_file: source_name = uploaded_file.name
        else:
            uploaded_images = st.file_uploader("Upload Exam Pages:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            if uploaded_images: source_name = f"{len(uploaded_images)} Images"

        if st.button("🚀 Solve Paper", type="primary"):
            if not (uploaded_file or uploaded_images):
                st.warning("Please upload a file.")
            elif not gemini_model:
                st.error("API Key missing.")
            else:
                with st.spinner("Analyzing questions..."):
                    content_parts = [
                        """
                        You are an expert academic examiner. Solve this paper.
                        Format: 
                        ## 📄 Solution Key
                        ### Section A
                        **Q1:** ... **Answer:** ...
                        """
                    ]
                    if user_context: content_parts.append(f"Instructions: {user_context}")

                    if uploaded_file:
                        text_data = extract_text_from_pdf(uploaded_file)
                        if text_data: content_parts.append(f"Content:\n{text_data}")
                    
                    if uploaded_images:
                        for img_file in uploaded_images:
                            try:
                                img = Image.open(img_file)
                                content_parts.append(img)
                            except: pass
                    
                    res = call_gemini(content_parts)
                    if res.get("error"):
                        st.error(res["error"])
                    else:
                        st.session_state.paper_solution = res["text"]
                        st.session_state.current_source_name = source_name
                        st.rerun()

    with col_result:
        if st.session_state.paper_solution:
            st.markdown(st.session_state.paper_solution)
            
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 Download Text", st.session_state.paper_solution, "Solution.md")
            
            with c2:
                if user:
                    if st.button("💾 Save to Library"):
                        name = st.session_state.get("current_source_name", "Paper")
                        if save_paper_to_db(st.session_state.paper_solution, name):
                            st.success("Saved!")
        else:
            st.info("👈 Upload a paper to start.")

# =======================================================
# TAB 2: SAVED SOLUTIONS
# =======================================================
with tab_saved:
    st.markdown("### 📚 Library")
    if user and supabase:
        saved_papers = fetch_saved_papers()
        if saved_papers:
            for i, paper in enumerate(reversed(saved_papers)):
                with st.expander(f"{paper.get('title')} ({paper.get('date')})"):
                    st.markdown(paper.get('content'))
                    st.download_button("Download", paper.get('content'), f"Solution_{i}.md", key=f"dl_{i}")
        else:
            st.info("No saved solutions found.")
    else:
        st.warning("Log in to view saved solutions.")
