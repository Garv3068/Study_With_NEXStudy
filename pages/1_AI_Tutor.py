import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
from PIL import Image

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy", page_icon="🧠", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo
if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=200)

st.title("🧠 NexStudy")
st.caption("Your personal AI academic companion. Solve doubts, learn topics, and master your syllabus.")

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
        # return genai.GenerativeModel("gemini-2.0-flash")
        return genai.GenerativeModel("gemini-2.5-flash-lite")
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

# ---------------- Session State ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "saved" not in st.session_state:
    st.session_state.saved = []

if "topic_explanation" not in st.session_state:
    st.session_state.topic_explanation = ""

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

def get_chat_history_text():
    """
    Reconstructs the chat history as a text block to give context to the model.
    We limit it to the last 6 turns to save tokens and focus on recent context.
    """
    history_context = ""
    # Get last 6 messages
    recent_messages = st.session_state.messages[-6:]

    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "NexStudy AI"
        # Clean text to avoid confusing the model with heavy formatting
        clean_text = msg['text'].replace("\n", " ") 
        history_context += f"{role}: {clean_text}\n"

    return history_context

# ---------------- Layout ----------------
left, right = st.columns([1, 2])

# ---------------- LEFT COLUMN: Tools & Modes ----------------
with left:
    st.markdown("### 🛠️ Study Mode")
    mode = st.radio(
        "Choose Mode:", 
        ["💬 Doubt Solver & Chat", "📖 Topic Explainer"], 
        index=0
    )
    st.markdown("---")

    # ==========================================
    # MODE 1: CHAT / DOUBT SOLVER CONTROLS
    # ==========================================
    if mode == "💬 Doubt Solver & Chat":
        st.info("Ask questions or upload homework.")

        st.session_state.input_type = st.radio(
            "Attach Material:", 
            ("None", "PDF Document", "Image (Problem)"), 
            index=0
        )

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()
        with col_b:
            if st.button("💾 Saved Items"):
                if st.session_state.saved:
                    st.write("**Saved:**")
                    for i, item in enumerate(st.session_state.saved, 1):
                        with st.expander(f"{i}. {item['timestamp']}"):
                            st.write(item["text"])
                else:
                    st.info("Empty.")

    # ==========================================
    # MODE 2: TOPIC EXPLAINER CONTROLS
    # ==========================================
    elif mode == "📖 Topic Explainer":
        st.markdown("#### 🧠 Learn a Concept")

        topic_input = st.text_input("Topic:", placeholder="e.g. Thermodynamics, SQL Joins")

        explanation_level = st.selectbox(
            "Depth:",
            ["ELI5 (Simple)", "High School", "College/Undergrad", "PhD/Research"]
        )

        include_links = st.checkbox("Include Video Links", value=True)

        if st.button("🚀 Explain", type="primary"):
            if not topic_input.strip():
                st.warning("Enter a topic.")
            else:
                prompt_text = f"Explain '{topic_input}'."
                prompt_details = f"Level: {explanation_level}.\n"
                if include_links:
                    prompt_details += "Include 3 best YouTube/Web resource links."

                full_prompt = f"{prompt_text}\n{prompt_details}"

                if gemini_model:
                    with st.spinner(f"Explaining '{topic_input}'..."):
                        res = call_gemini([f"You are an expert tutor. {full_prompt}"])
                        if not res.get("error"):
                            st.session_state.topic_explanation = res["text"]
                            st.rerun()
                        else:
                            st.error(res["error"])
                else:
                    st.error("API Key missing.")

# ---------------- RIGHT COLUMN: Interaction Area ----------------
with right:

    # ==========================================
    # VIEW 1: CHAT INTERFACE
    # ==========================================
    if mode == "💬 Doubt Solver & Chat":

        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.messages):
                # -----------------------------------------------
                # USER MESSAGE -> GREY BOX
                # -----------------------------------------------
                if msg["role"] == "user":
                    user_text = msg['text'].replace('\n', '<br>')
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #f0f2f6; 
                            padding: 15px; 
                            border-radius: 10px; 
                            margin-bottom: 20px; 
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                            color: #000000;">
                            <h5 style="margin: 0 0 8px 0; color: #444;">👤 You</h5>
                            <div style="font-size: 1rem;">{user_text}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                # -----------------------------------------------
                # AI MESSAGE -> CLEAN TEXT (No Box)
                # -----------------------------------------------
                else:
                    st.markdown(f"### 🧠 NexStudy")
                    st.markdown(msg['text'])

                    # Tool Buttons below AI text
                    b1, b2, b3, b4, b5 = st.columns([1,1,1,1,1])
                    if b1.button("Simplify", key=f"s_{i}"):
                        res = call_gemini([f"Simplify this:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()

                    if b2.button("Steps", key=f"st_{i}"):
                        res = call_gemini([f"Show steps:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()

                    if b3.button("Quiz", key=f"q_{i}"):
                        res = call_gemini([f"Make 3 MCQs on this:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()

                    if b4.button("Cards", key=f"c_{i}"):
                        res = call_gemini([f"Make flashcards on this:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()

                    if b5.button("Save", key=f"sv_{i}"):
                        st.session_state.saved.append({"text": msg["text"], "timestamp": str(datetime.datetime.now())})
                        st.success("Saved!")

                    st.divider()

        # ---------------- CHAT INPUT ----------------
        st.write("")
        # FIX: Changed clear_on_submit to True. 
        # This clears the text area and file uploaders automatically after sending.
        with st.form(key="chat_form", clear_on_submit=True):
            col_in, col_btn = st.columns([6, 1])
            with col_in:
                user_input = st.text_area("Type your question...", height=80, key="u_in")

            # Show uploaders based on Left Sidebar selection
            uploaded_pdf = None
            uploaded_image = None
            if st.session_state.get("input_type") == "PDF Document":
                uploaded_pdf = st.file_uploader("PDF:", type=["pdf"])
            elif st.session_state.get("input_type") == "Image (Problem)":
                uploaded_image = st.file_uploader("Image:", type=["png","jpg","jpeg"])

            with col_btn:
                st.write("")
                st.write("")
                if st.form_submit_button("🚀 Send"):

                    # --- CONTINUOUS CHAT LOGIC ---
                    # 1. Get history text
                    history_text = get_chat_history_text()

                    # 2. Construct System Prompt with Memory
                    system_prompt = f"""
                    You are NexStudy, an expert academic tutor.
                    
                    **Context from previous conversation:**
                    {history_text}
                    
                    **Instructions:**
                    - Answer the NEW user question below.
                    - Use the context above if the user refers to "it", "that", or previous topics.
                    - If the user uploads a file, prioritize analyzing that file.
                    - Be concise and helpful.
                    """

                    content_parts = [system_prompt]
                    display_text = []

                    if user_input.strip():
                        content_parts.append(f"NEW USER QUESTION: {user_input}")
                        display_text.append(user_input)

                    if uploaded_pdf:
                        pdf_text = extract_text_from_pdf(uploaded_pdf)
                        if pdf_text:
                            content_parts.append(f"PDF Context:\n{pdf_text}")
                            display_text.append(f"📄 [PDF: {uploaded_pdf.name}]")

                    if uploaded_image:
                        try:
                            img = Image.open(uploaded_image)
                            content_parts.append(img)
                            display_text.append(f"🖼️ [Image: {uploaded_image.name}]")
                        except: pass

                    if display_text or uploaded_image or uploaded_pdf:
                        append_user_message("\n".join(display_text))
                        if gemini_model:
                            with st.spinner("Thinking..."):
                                res = call_gemini(content_parts)
                                if not res.get("error"):
                                    append_assistant_message(res["text"])
                                    st.rerun()
                        else:
                            st.error("Check API Key.")
                    else:
                        st.warning("Empty message.")

    # ==========================================
    # VIEW 2: TOPIC EXPLAINER OUTPUT
    # ==========================================
    elif mode == "📖 Topic Explainer":
        if st.session_state.topic_explanation:
            st.markdown("### 📝 Topic Guide")
            st.markdown("---")
            st.markdown(st.session_state.topic_explanation)
            st.markdown("---")
            if st.button("📋 Copy Text"):
                 st.code(st.session_state.topic_explanation)
        else:
            st.info("👈 Use the sidebar to generate a topic guide.")
            st.markdown("""
            **NexStudy Explainer** can help you with:
            - ⚛️ **Complex Concepts**
            - 📚 **Exam Prep**
            - 🔬 **Research Topics**
            """)
