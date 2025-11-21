import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
from PIL import Image

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy Companion", page_icon="🤖", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo
_logo_path = "/mnt/data/A_logo_for_EduNex,_an_AI-powered_smart_study_assis.png"
if os.path.exists(_logo_path):
    st.image(_logo_path, width=150)

st.title("🤖 NexStudy: AI Tutor & Doubt Solver")
st.caption("""
**Your all-in-one study companion:** Ask questions, upload homework for solutions, get concept explanations, or generate quizzes from your notes.
""")

# ---------------- Gemini Initialization (Robust) ----------------
@st.cache_resource
def init_gemini(api_key_input):
    # 1. Try getting key from user input first
    key = api_key_input
    # 2. If no user input, try secrets
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

# ---------------- Sidebar for API Key ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Check if secret key exists
    has_secret_key = False
    try:
        if st.secrets.get("GEMINI_API_KEY"):
            has_secret_key = True
    except:
        pass

    user_api_key = ""
    if not has_secret_key:
        st.warning("⚠️ No API Key found in secrets.")
        user_api_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="Paste key here...")
        st.markdown("[Get a free key here](https://aistudio.google.com/app/apikey)")
    else:
        st.success("✅ API Key loaded from secrets")

gemini_model = init_gemini(user_api_key)

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "saved" not in st.session_state:
    st.session_state.saved = []

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

def append_user_message(text):
    st.session_state.messages.append({"role": "user", "text": text})

def append_assistant_message(text):
    st.session_state.messages.append({"role": "assistant", "text": text})

# ---------------- Layout ----------------
left, right = st.columns([1, 2])

# ---------------- LEFT COLUMN: Controls ----------------
with left:
    st.markdown("### 📤 Input")
    st.info("Chat below or upload materials to get started.")
    
    input_choice = st.radio("I want to upload:", ("None (Just Chat)", "PDF Document", "Image (Problem/Diagram)"), index=0)

    st.divider()
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col_b:
        if st.button("💾 Saved Notes"):
            if st.session_state.saved:
                st.write("**Your Saved Items:**")
                for i, item in enumerate(st.session_state.saved, 1):
                    with st.expander(f"{i}. {item['timestamp']}"):
                        st.write(item["text"])
            else:
                st.info("No saved notes yet.")

# ---------------- RIGHT COLUMN: Chat Interface ----------------
with right:
    # CSS: Force black text in chat bubbles for Dark Mode visibility
    st.markdown(
        """
        <style>
        .chat-box { max-height: 64vh; overflow:auto; padding:8px; display:flex; flex-direction:column; gap:12px; }
        .user { 
            align-self:flex-end; 
            background:#DCF8C6; 
            color: #000000; 
            padding:12px; 
            border-radius:12px; 
            max-width:80%; 
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .ai { 
            align-self:flex-start; 
            background:#F1F3F5; 
            color: #000000; 
            padding:12px; 
            border-radius:12px; 
            max-width:80%; 
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    chat_box = st.container()
    with chat_box:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for i, msg in enumerate(st.session_state.messages):
            # Render User Message
            if msg["role"] == "user":
                user_text = msg['text'].replace('\n', '<br>')
                st.markdown(f"<div class='user'><b>You:</b><br>{user_text}</div>", unsafe_allow_html=True)
            
            # Render AI Message + Tool Buttons
            else:
                ai_text_display = msg['text'].replace('\n', '<br>')
                st.markdown(f"<div class='ai'><b>NexStudy AI:</b><br>{ai_text_display}</div>", unsafe_allow_html=True)
                
                # --- Action Buttons (Study Tools) ---
                # We use a unique key based on index 'i'
                b1, b2, b3, b4, b5 = st.columns([1,1,1,1,1])
                
                if b1.button(f"Simplify 👶", key=f"simp_{i}", help="Explain like I'm 5"):
                    res = call_gemini([f"Explain this response in much simpler terms with an analogy:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()
                        
                if b2.button(f"Steps 🪜", key=f"step_{i}", help="Show step-by-step solution"):
                    res = call_gemini([f"Break this down into clear, numbered steps:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()

                if b3.button(f"Quiz 🎯", key=f"quiz_{i}", help="Generate a quiz based on this"):
                    res = call_gemini([f"Create 3 Multiple Choice Questions (with answers at the end) to test my understanding of this:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()
                        
                if b4.button(f"Cards 🃏", key=f"card_{i}", help="Make flashcards"):
                    res = call_gemini([f"Create 5 Flashcards (Front/Back format) from this content:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()
                        
                if b5.button(f"Save 💾", key=f"sav_{i}"):
                    st.session_state.saved.append({"text": msg["text"], "timestamp": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))})
                    st.success("Saved!")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- INPUT FORM ----------------
    with st.form(key="chat_form", clear_on_submit=False):
        col_input, col_btn = st.columns([6, 1])
        
        with col_input:
            user_input = st.text_area("Ask a question or explain what you need help with:", height=100, key="u_in")
        
        # File Uploaders (Conditional)
        uploaded_pdf = None
        uploaded_image = None
        
        if input_choice == "PDF Document":
            uploaded_pdf = st.file_uploader("Upload PDF (Notes/Book):", type=["pdf"])
        elif input_choice == "Image (Problem/Diagram)":
            uploaded_image = st.file_uploader("Upload Image:", type=["png","jpg","jpeg"])

        with col_btn:
            st.write("") # spacer
            st.write("") 
            submit_clicked = st.form_submit_button("🚀 Send")

        if submit_clicked:
            content_parts = []
            display_text = []

            # 1. System Persona
            system_prompt = """
            You are NexStudy AI, a smart and patient tutor. 
            - If the user asks for a solution, explain the steps clearly.
            - If the user uploads an image, analyze it (multimodal).
            - If the user sends notes, summarize or explain them.
            Keep answers concise but helpful.
            """
            content_parts.append(system_prompt)

            # 2. Text Input
            if user_input and user_input.strip():
                content_parts.append(user_input)
                display_text.append(user_input)

            # 3. PDF Handling
            if uploaded_pdf:
                pdf_text = extract_text_from_pdf(uploaded_pdf)
                if pdf_text:
                    content_parts.append(f"Context from uploaded PDF:\n{pdf_text}")
                    display_text.append(f"📄 [Attached PDF: {uploaded_pdf.name}]")
                else:
                    st.warning("Could not extract text from PDF.")

            # 4. Image Handling (Direct to Gemini)
            if uploaded_image:
                try:
                    img = Image.open(uploaded_image)
                    content_parts.append(img)
                    display_text.append(f"🖼️ [Attached Image: {uploaded_image.name}]")
                except Exception as e:
                    st.error(f"Error processing image: {e}")

            # Validation & Execution
            if not display_text and not uploaded_image and not uploaded_pdf:
                st.warning("Please type a message or upload a file.")
            else:
                # Show User Message
                append_user_message("\n".join(display_text))

                if gemini_model is None:
                    st.error("Gemini API Key missing. Check sidebar.")
                else:
                    with st.spinner("NexStudy is thinking..."):
                        res = call_gemini(content_parts)
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])
                            st.rerun()
