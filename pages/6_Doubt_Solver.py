# pages/6_Doubt_Solver.py
import streamlit as st
import google.generativeai as genai
import pdfplumber
import io
import os
import datetime

from PIL import Image
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy Tutor", page_icon="🤖", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo (developer-provided file path). If missing, skip.
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
        # no key found
        pass

    if not key:
        return None

    try:
        genai.configure(api_key=key)
        # Use the chosen model: gemini-2.0-flash (fast + cheap)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

gemini_model = init_gemini()

# ---------------- Session state for chat ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: {"role":"user"/"assistant","text":..., "meta":{...}}

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

def ocr_image(uploaded_image_bytes):
    if not TESSERACT_AVAILABLE:
        return None
    try:
        img = Image.open(io.BytesIO(uploaded_image_bytes)).convert("RGB")
        return pytesseract.image_to_string(img)
    except Exception as e:
        st.warning(f"OCR failed: {e}")
        return None

def call_gemini(prompt: str, max_output_tokens: int = 1024):
    if gemini_model is None:
        return {"error": "Gemini API key not configured or model not initialized."}
    try:
        resp = gemini_model.generate_content(prompt)
        text = resp.text or ""
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

def append_user_message(text, meta=None):
    st.session_state.messages.append({"role": "user", "text": text, "meta": meta or {}})

def append_assistant_message(text, meta=None):
    st.session_state.messages.append({"role": "assistant", "text": text, "meta": meta or {}})

# ---------------- Left control column ----------------
left, right = st.columns([1, 2])

with left:
    st.markdown("### ⚙️ Controls")
    st.info("Use the chat on the right to ask doubts. Upload PDFs or images if you like.")
    st.markdown("**Input types**")
    input_choice = st.radio("", ("Text", "PDF + Text", "Image + Text"), index=1)

    # st.markdown("---")
    # st.markdown("**Model**")
    # st.markdown("Using: **gemini-2.0-flash** (fast & student-friendly)")

    # st.markdown("---")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.success("Chat cleared.")
    if st.button("Saved answers"):
        if st.session_state.saved:
            st.write("Saved responses:")
            for i, item in enumerate(st.session_state.saved, 1):
                st.markdown(f"**{i}. {item['title']}** — {item['timestamp']}")
                st.write(item["text"])
        else:
            st.info("No saved answers yet.")

# ---------------- Right chat column ----------------
with right:
    # chat container
    st.markdown(
        """
        <style>
        .chat-box { max-height: 64vh; overflow:auto; padding:8px; display:flex; flex-direction:column; gap:12px; }
        .user { align-self:flex-end; background:#DCF8C6; padding:12px; border-radius:12px; max-width:80%; }
        .ai { align-self:flex-start; background:#F1F3F5; padding:12px; border-radius:12px; max-width:80%; }
        .meta { font-size:12px; color:#666; margin-top:6px; }
        </style>
        """, unsafe_allow_html=True)

    chat_box = st.container()
    with chat_box:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"<div class='user'><b>You:</b><br>{st.markdown(msg['text'], unsafe_allow_html=False) or ''}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='ai'><b>NexStudy Tutor:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
                # action buttons for assistant messages
                cols = st.columns([1,1,1,1,1])
                with cols[0]:
                    if st.button(f"Explain Simpler 🔍 #{i}", key=f"simpler_{i}"):
                        followup_prompt = f"Explain the following content in simpler terms, with short examples:\n\n{msg['text']}"
                        res = call_gemini(followup_prompt)
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])
                with cols[1]:
                    if st.button(f"Show Steps 🪜 #{i}", key=f"steps_{i}"):
                        followup_prompt = f"Provide a step-by-step solution or breakdown for the following text:\n\n{msg['text']}"
                        res = call_gemini(followup_prompt)
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])
                with cols[2]:
                    if st.button(f"Generate Quiz 🎯 #{i}", key=f"quiz_{i}"):
                        followup_prompt = f"Create 5 short MCQs (question + 4 options + correct answer) from the following explanation:\n\n{msg['text']}\n\nReturn concise results."
                        res = call_gemini(followup_prompt)
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])
                with cols[3]:
                    if st.button(f"Flashcards 🧾 #{i}", key=f"flash_{i}"):
                        followup_prompt = f"Convert the following content into 8 short flashcards in 'Q: ... A: ...' format:\n\n{msg['text']}"
                        res = call_gemini(followup_prompt)
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])
                with cols[4]:
                    if st.button(f"Save 💾 #{i}", key=f"save_{i}"):
                        st.session_state.saved.append({"title": msg["text"][:60]+"...", "text": msg["text"], "timestamp": str(datetime.datetime.now())})
                        st.success("Saved to your local library.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- Input area (form) ----------------
    with st.form(key="doubt_form", clear_on_submit=False):
        user_input = st.text_area("Ask your doubt (short question or paste full problem):", height=140, key="user_input")
        uploaded_pdf = None
        uploaded_image = None
        if input_choice in ("PDF + Text", "Image + Text"):
            if input_choice == "PDF + Text":
                uploaded_pdf = st.file_uploader("Upload PDF (≤10MB) (optional):", type=["pdf"])
            else:
                uploaded_image = st.file_uploader("Upload Image (png/jpg) (optional):", type=["png","jpg","jpeg"])

        submit = st.form_submit_button("Send")

        if submit:
            # build content: prefer uploaded asset content if provided + user text
            content_parts = []
            if uploaded_pdf:
                pdf_bytes = uploaded_pdf.read()
                pdf_text = extract_text_from_pdf(io.BytesIO(pdf_bytes))
                if pdf_text:
                    content_parts.append("PDF content:\n" + pdf_text)
                else:
                    st.warning("Couldn't extract text from PDF. Please add a short description below.")
            if uploaded_image:
                img_bytes = uploaded_image.read()
                if TESSERACT_AVAILABLE:
                    ocr_text = ocr_image(img_bytes)
                    if ocr_text:
                        content_parts.append("Image OCR text:\n" + ocr_text)
                    else:
                        st.warning("Could not extract text from image. Please describe the image/question below.")
                else:
                    st.info("OCR not available in this environment. Please add a short description below.")
            if user_input and user_input.strip():
                content_parts.append("User question:\n" + user_input.strip())

            if not content_parts:
                st.warning("Please provide a question or upload a readable PDF/image or give a short description.")
            else:
                full_prompt_text = "\n\n".join(content_parts)
                append_user_message(full_prompt_text, meta={"pdf": bool(uploaded_pdf), "image": bool(uploaded_image)})

                # Call Gemini for the main response
                if gemini_model is None:
                    st.error("Gemini model not initialized. Please set GEMINI_API_KEY in Streamlit secrets.")
                else:
                    with st.spinner("NexStudy is thinking..."):
                        system_preamble = (
                            "You are NexStudy Tutor — an expert, patient teacher for college students. "
                            "Answer concisely and clearly. Provide short examples when relevant. "
                            "If a step-by-step solution is required, include steps. "
                            "When the user uploads a PDF or image, base answers only on the provided content; do not hallucinate facts."
                        )
                        prompt = system_preamble + "\n\nUser content:\n\n" + full_prompt_text + "\n\nAnswer:"
                        res = call_gemini(prompt)
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            append_assistant_message(res["text"])

    # after form submitted, rerun updates show above automatically

# End of page
