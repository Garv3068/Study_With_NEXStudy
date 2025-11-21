# pages/6_Doubt_Solver.py
import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
from PIL import Image

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy Tutor", page_icon="🤖", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo
_logo_path = "/mnt/data/A_logo_for_EduNex,_an_AI-powered_smart_study_assis.png"
if os.path.exists(_logo_path):
    st.image(_logo_path, width=150)

st.title("🤖 NexStudy Tutor (Doubt Solver)")
st.caption("Ask a question, upload a PDF or image, and get clear step-by-step explanations.")

# ---------------- Gemini initialization ----------------
@st.cache_resource
def init_gemini():
    key = None
    try:
        key = st.secrets["GEMINI_API_KEY"]
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

gemini_model = init_gemini()

# ---------------- Session state for chat ----------------
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

# Modified to accept a list of contents (text + images)
def call_gemini(contents):
    if gemini_model is None:
        return {"error": "Gemini API key not configured."}
    try:
        # Gemini accepts a list [text, image, text...]
        resp = gemini_model.generate_content(contents)
        text = resp.text or ""
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

def append_user_message(text, meta=None):
    st.session_state.messages.append({"role": "user", "text": text, "meta": meta or {}})

def append_assistant_message(text, meta=None):
    st.session_state.messages.append({"role": "assistant", "text": text, "meta": meta or {}})

# ---------------- Layout ----------------
left, right = st.columns([1, 2])

# ---------------- Left Column (Controls) ----------------
with left:
    st.markdown("### ⚙️ Controls")
    st.info("Use the chat on the right to ask doubts. Upload PDFs or images if you like.")
    st.markdown("**Input types**")
    input_choice = st.radio("", ("Text", "PDF + Text", "Image + Text"), index=1)

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.success("Chat cleared.")
        st.rerun()
        
    if st.button("Saved answers"):
        if st.session_state.saved:
            st.write("Saved responses:")
            for i, item in enumerate(st.session_state.saved, 1):
                st.markdown(f"**{i}. {item['title']}** — {item['timestamp']}")
                st.write(item["text"])
        else:
            st.info("No saved answers yet.")

# ---------------- Right Column (Chat) ----------------
with right:
    # CSS to ensure black text on chat bubbles
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
        }
        .ai { 
            align-self:flex-start; 
            background:#F1F3F5; 
            color: #000000; 
            padding:12px; 
            border-radius:12px; 
            max-width:80%; 
        }
        </style>
        """, unsafe_allow_html=True)

    chat_box = st.container()
    with chat_box:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                user_text = msg['text'].replace('\n', '<br>')
                st.markdown(f"<div class='user'><b>You:</b><br>{user_text}</div>", unsafe_allow_html=True)
            else:
                ai_text_display = msg['text'].replace('\n', '<br>')
                st.markdown(f"<div class='ai'><b>NexStudy Tutor:</b><br>{ai_text_display}</div>", unsafe_allow_html=True)
                
                # Buttons for AI response
                cols = st.columns([1,1,1,1,1])
                
                if cols[0].button(f"Explain Simpler 🔍", key=f"simpler_{i}"):
                    res = call_gemini([f"Explain this simpler:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()
                        
                if cols[1].button(f"Show Steps 🪜", key=f"steps_{i}"):
                    res = call_gemini([f"Show step-by-step solution:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()

                if cols[2].button(f"Generate Quiz 🎯", key=f"quiz_{i}"):
                    res = call_gemini([f"Create 5 MCQs from this:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()
                        
                if cols[3].button(f"Flashcards 🧾", key=f"flash_{i}"):
                    res = call_gemini([f"Create flashcards from this:\n\n{msg['text']}"])
                    if not res.get("error"):
                        append_assistant_message(res["text"])
                        st.rerun()
                        
                if cols[4].button(f"Save 💾", key=f"save_{i}"):
                    st.session_state.saved.append({"title": msg["text"][:50]+"...", "text": msg["text"], "timestamp": str(datetime.datetime.now())})
                    st.success("Saved!")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- Input Form ----------------
    with st.form(key="doubt_form", clear_on_submit=False):
        user_input = st.text_area("Ask your doubt:", height=140, key="user_input")
        
        uploaded_pdf = None
        uploaded_image = None
        
        if input_choice == "PDF + Text":
            uploaded_pdf = st.file_uploader("Upload PDF (≤10MB):", type=["pdf"])
        elif input_choice == "Image + Text":
            uploaded_image = st.file_uploader("Upload Image:", type=["png","jpg","jpeg"])

        submit = st.form_submit_button("Send")

        if submit:
            # Prepare the content list for Gemini
            request_content = []
            display_text = [] # For showing in the chat history

            # 1. System Preamble (Text)
            system_prompt = "You are NexStudy Tutor. Answer clearly. If the user sends an image, analyze it."
            request_content.append(system_prompt)

            # 2. User Text Input
            if user_input and user_input.strip():
                request_content.append(user_input)
                display_text.append(user_input)

            # 3. PDF Text
            if uploaded_pdf:
                pdf_text = extract_text_from_pdf(uploaded_pdf)
                if pdf_text:
                    request_content.append(f"PDF Context:\n{pdf_text}")
                    display_text.append("[Uploaded PDF]")

            # 4. Image Input (The Key Fix)
            if uploaded_image:
                try:
                    img = Image.open(uploaded_image)
                    request_content.append(img) # Send actual image object to Gemini
                    display_text.append("[Uploaded Image]")
                except Exception as e:
                    st.error(f"Error processing image: {e}")

            if not display_text and not uploaded_image and not uploaded_pdf:
                st.warning("Please enter text or upload a file.")
            else:
                # Show user message in chat
                append_user_message("\n".join(display_text))

                if gemini_model is None:
                    st.error("Gemini API Key missing.")
                else:
                    with st.spinner("Analyzing..."):
                        res = call_gemini(request_content)
                        
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])
                            st.rerun()
