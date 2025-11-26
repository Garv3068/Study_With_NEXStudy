import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
from PIL import Image
import io

# ---------------- Page config ----------------
st.set_page_config(page_title="Past Paper Solver", page_icon="📝", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo
_logo_path = "/mnt/data/A_logo_for_EduNex,_an_AI-powered_smart_study_assis.png"
if os.path.exists(_logo_path):
    st.image(_logo_path, width=150)

st.title("📝 Past Paper Solver")
st.caption("Upload an exam paper (PDF or Images) and get a comprehensive solution key.")

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
    # st.header("⚙️ Settings")
    
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
    # else:
        # st.success("✅ API Key loaded")

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

def call_gemini(contents):
    if gemini_model is None:
        return {"error": "Gemini API key not configured."}
    try:
        resp = gemini_model.generate_content(contents)
        text = resp.text or ""
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

# ---------------- Session State ----------------
if "paper_solution" not in st.session_state:
    st.session_state.paper_solution = ""

# ---------------- Layout ----------------
col_upload, col_result = st.columns([1, 2])

# ---------------- LEFT COLUMN: Upload & Config ----------------
with col_upload:
    st.markdown("### 📤 Upload Paper")
    
    upload_type = st.radio("File Type:", ["PDF Document", "Images (Pages)"])
    
    user_context = st.text_area("Any specific instructions?", placeholder="e.g. Solve only Section B, or 'This is a Biology Class 12 paper'")
    
    uploaded_file = None
    uploaded_images = []
    
    if upload_type == "PDF Document":
        uploaded_file = st.file_uploader("Upload Exam PDF:", type=["pdf"])
    else:
        uploaded_images = st.file_uploader("Upload Exam Pages:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    st.markdown("---")
    
    if st.button("🚀 Solve Paper", type="primary"):
        if not (uploaded_file or uploaded_images):
            st.warning("Please upload a file first.")
        else:
            with st.spinner("Analyzing questions and drafting solutions... (This may take a moment)"):
                content_parts = []
                
                # System Prompt
                system_prompt = """
                You are an expert academic examiner. 
                Task: Solve the provided past question paper.
                
                Format the output strictly as follows:
                ## 📄 Paper Solution
                
                ### Section A (or Question 1)
                **Q1:** [Question text]
                **Answer:** [Model Answer]
                *(If MCQ, explain why the option is correct)*
                
                ### Section B (or Question 2)
                ...
                
                Keep answers accurate, academic, and well-structured.
                """
                content_parts.append(system_prompt)
                
                if user_context:
                    content_parts.append(f"User Instructions: {user_context}")

                # Process PDF
                if uploaded_file:
                    text_data = extract_text_from_pdf(uploaded_file)
                    if text_data:
                        content_parts.append(f"Exam Paper Content:\n{text_data}")
                    else:
                        st.error("Could not read PDF text. Try converting to images.")

                # Process Images
                if uploaded_images:
                    for img_file in uploaded_images:
                        try:
                            img = Image.open(img_file)
                            content_parts.append(img)
                        except:
                            pass
                
                # API Call
                res = call_gemini(content_parts)
                
                if res.get("error"):
                    st.error(res["error"])
                else:
                    st.session_state.paper_solution = res["text"]
                    st.rerun()

# ---------------- RIGHT COLUMN: Solutions Display ----------------
with col_result:
    if st.session_state.paper_solution:
        st.markdown(st.session_state.paper_solution)
        
        st.markdown("---")
        st.download_button(
            label="📥 Download Solution as Text",
            data=st.session_state.paper_solution,
            file_name="Solution_Key.txt",
            mime="text/plain"
        )
    else:
        # Empty State
        st.info("👈 Upload your question paper on the left to see the magic happen.")
        st.markdown(
            """
            ### Features:
            - **Full Paper Solving:** Upload a PDF and get answers for all questions.
            - **MCQ Explanations:** Understand *why* an option is correct.
            - **Step-by-Step Math:** Detailed steps for numerical problems.
            """
        )
