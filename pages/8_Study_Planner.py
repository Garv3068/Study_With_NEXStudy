import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
from datetime import date

# ---------------- Page config ----------------
st.set_page_config(page_title="AI Study Planner", page_icon="📅", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("logo.png"):
    st.image("logo.png", width=200)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=200)

st.title("📅 AI Study Planner")
st.caption("Upload your syllabus, set your exam date, and get a perfectly optimized study schedule.")

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
    
    has_secret_key = False
    try:
        if st.secrets.get("GEMINI_API_KEY"):
            has_secret_key = True
    except:
        pass

    user_api_key = ""
    if not has_secret_key:
        st.warning("⚠️ No API Key found.")
        user_api_key = st.text_input("Enter Gemini API Key:", type="password")
    else:
        st.success("✅ API Key loaded")

gemini_model = init_gemini(user_api_key)

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

# ---------------- Session State ----------------
if "study_plan" not in st.session_state:
    st.session_state.study_plan = ""

# ---------------- Layout ----------------
col_config, col_plan = st.columns([1, 2])

# ---------------- LEFT COLUMN: Configuration ----------------
with col_config:
    st.markdown("### ⚙️ Plan Details")
    
    with st.form("planner_form"):
        # Syllabus Input
        syllabus_type = st.radio("Syllabus Source:", ["Paste Text", "Upload PDF"])
        
        syllabus_text = ""
        if syllabus_type == "Paste Text":
            syllabus_text = st.text_area("Paste Topics/Chapters:", height=150, placeholder="1. Algebra\n2. Calculus\n3. Thermodynamics...")
        else:
            uploaded_file = st.file_uploader("Upload Syllabus PDF:", type=["pdf"])
        
        # Dates
        today = date.today()
        exam_date = st.date_input("Exam Date:", min_value=today + datetime.timedelta(days=1))
        
        # Preferences
        daily_hours = st.slider("Daily Study Hours:", 1, 12, 4)
        focus_areas = st.text_input("Weak Areas (Focus more on):", placeholder="e.g. Organic Chemistry")
        
        generate_btn = st.form_submit_button("🚀 Generate Plan")

    if generate_btn:
        final_syllabus = syllabus_text
        if syllabus_type == "Upload PDF" and uploaded_file:
            final_syllabus = extract_text_from_pdf(uploaded_file)
        
        if not final_syllabus:
            st.warning("Please provide a syllabus (text or PDF).")
        else:
            if gemini_model:
                with st.spinner("Creating your master plan..."):
                    # Calculate days
                    days_left = (exam_date - today).days
                    
                    prompt = f"""
                    Act as an expert study strategist. Create a detailed day-by-day study schedule.
                    
                    **Constraints:**
                    - Days remaining: {days_left} days
                    - Daily study time: {daily_hours} hours
                    - Focus areas (give more time to these): {focus_areas}
                    
                    **Syllabus:**
                    {final_syllabus[:10000]} (truncated if too long)
                    
                    **Output Format:**
                    Start with a motivational quote.
                    Then provide a structured Markdown table:
                    | Day | Date | Topic to Cover | Activity (Read/Practice/Revise) |
                    |---|---|---|---|
                    | Day 1 | {today} | ... | ... |
                    
                    After the table, provide 3 bullet points on "Strategy for Success".
                    """
                    
                    try:
                        response = gemini_model.generate_content(prompt)
                        st.session_state.study_plan = response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.error("API Key missing.")

# ---------------- RIGHT COLUMN: The Plan ----------------
with col_plan:
    if st.session_state.study_plan:
        st.markdown("### 🗓️ Your Personalized Schedule")
        
        # Display the plan
        st.markdown(st.session_state.study_plan)
        
        st.markdown("---")
        st.download_button(
            label="📥 Download Plan as Markdown",
            data=st.session_state.study_plan,
            file_name="Study_Plan.md",
            mime="text/markdown"
        )
    else:
        st.info("👈 Fill in the details on the left to generate your schedule.")
        
        st.markdown("""
        ### How it works:
        1. **Analyze:** The AI reads your syllabus and identifies key topics.
        2. **Prioritize:** It allocates more time to your weak areas.
        3. **Schedule:** It spreads topics evenly across the days leading up to your exam.
        """)
