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

st.title("🤖 NexStudy: Smart AI Tutor ")
st.caption("""
**Your all-in-one study companion:** Ask questions, upload homework for solutions, get concept explanations, or generate quizzes from your notes.
""")

# ---------------- Gemini Initialization (Robust) ----------------
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

# ---------------- Sidebar for API Key ----------------
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

# ---------------- Layout ----------------
left, right = st.columns([1, 2])

# ---------------- LEFT COLUMN: Controls ----------------
with left:
    # --- MODE SELECTION ---
    st.markdown("### 🛠️ Study Mode")
    mode = st.radio(
        "Choose how you want to learn:", 
        ["💬 Chat / Doubt Solver", "📖 Topic Explainer"], 
        index=0
    )
    st.markdown("---")

    # ==========================================
    # MODE 1: CHAT / DOUBT SOLVER
    # ==========================================
    if mode == "💬 Chat / Doubt Solver":
        st.info("Chat below or upload materials to get started.")
        
        st.session_state.input_type = st.radio(
            "I want to upload:", 
            ("None (Just Chat)", "PDF Document", "Image (Problem/Diagram)"), 
            index=0
        )

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

    # ==========================================
    # MODE 2: TOPIC EXPLAINER
    # ==========================================
    elif mode == "📖 Topic Explainer":
        st.markdown("#### 🧠 Explain a Topic")
        
        topic_input = st.text_input("Enter a topic you want to learn:", placeholder="e.g., Recursion, DBMS, Black Holes")
        
        explanation_level = st.selectbox(
            "Choose explanation level:",
            ["ELI5 (Like I'm 5)", "Beginner (High School)", "Intermediate (College)", "Advanced (Research)"]
        )
        
        include_links = st.checkbox("Include YouTube & web links (recommended)", value=True)
        
        if st.button("🧠 Explain Topic", type="primary"):
            if not topic_input.strip():
                st.warning("Please enter a topic first.")
            else:
                # Construct the Prompt
                prompt_text = f"Explain the topic '{topic_input}'."
                prompt_details = f"Level: {explanation_level}.\n"
                if include_links:
                    prompt_details += "Please include 3-5 high-quality references (YouTube links or standard documentation URLs) at the end."
                
                full_prompt = f"{prompt_text}\n{prompt_details}"
                
                if gemini_model:
                    with st.spinner(f"Generating {explanation_level} explanation for '{topic_input}'..."):
                        res = call_gemini([f"You are an expert tutor. {full_prompt}"])
                        if not res.get("error"):
                            # Save to a separate state variable, NOT the chat history
                            st.session_state.topic_explanation = res["text"]
                            st.rerun()
                        else:
                            st.error(res["error"])
                else:
                    st.error("Gemini API Key missing.")

# ---------------- RIGHT COLUMN: Output ----------------
with right:
    
    # ==========================================
    # VIEW 1: CHAT INTERFACE
    # ==========================================
    if mode == "💬 Chat / Doubt Solver":
        
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.messages):
                # Render User Message (IN GREY BOX)
                if msg["role"] == "user":
                    user_text = msg['text'].replace('\n', '<br>')
                    st.markdown(
                        f"""
                        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 15px; color: #000000;">
                            <h4 style="margin: 0 0 5px 0; color: #000000;">👤 You</h4>
                            {user_text}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                # Render AI Message (Simple Header + Text)
                else:
                    st.markdown(f"### 🤖 NexStudy AI")
                    st.markdown(msg['text'])
                    
                    # --- Action Buttons (Study Tools) ---
                    # Buttons appear directly below the text, clean style
                    b1, b2, b3, b4, b5 = st.columns([1,1,1,1,1])
                    
                    if b1.button(f"Simplify", key=f"simp_{i}", help="Explain like I'm 5"):
                        res = call_gemini([f"Explain this response in much simpler terms with an analogy:\n\n{msg['text']}"])
                        if not res.get("error"):
                            append_assistant_message(res["text"])
                            st.rerun()
                            
                    if b2.button(f"Steps", key=f"step_{i}", help="Show step-by-step solution"):
                        res = call_gemini([f"Break this down into clear, numbered steps:\n\n{msg['text']}"])
                        if not res.get("error"):
                            append_assistant_message(res["text"])
                            st.rerun()

                    if b3.button(f"Quiz", key=f"quiz_{i}", help="Generate a quiz based on this"):
                        res = call_gemini([f"Create 3 Multiple Choice Questions (with answers at the end) to test my understanding of this:\n\n{msg['text']}"])
                        if not res.get("error"):
                            append_assistant_message(res["text"])
                            st.rerun()
                            
                    if b4.button(f"Cards", key=f"card_{i}", help="Make flashcards"):
                        res = call_gemini([f"Create 5 Flashcards (Front/Back format) from this content:\n\n{msg['text']}"])
                        if not res.get("error"):
                            append_assistant_message(res["text"])
                            st.rerun()
                            
                    if b5.button(f"Save", key=f"sav_{i}"):
                        st.session_state.saved.append({"text": msg["text"], "timestamp": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))})
                        st.success("Saved!")
                    
                    # Divider to separate message pairs or conversation turns
                    st.divider()

        # ---------------- CHAT INPUT FORM ----------------
        # Using a container at the bottom to keep input separate
        st.write("")
        with st.form(key="chat_form", clear_on_submit=False):
            col_input, col_btn = st.columns([6, 1])
            
            with col_input:
                user_input = st.text_area("Ask a question:", height=100, key="u_in", placeholder="Type here...")
            
            # Uploaders (Only shown if input_type is correct)
            uploaded_pdf = None
            uploaded_image = None
            current_input_type = st.session_state.get("input_type", "None")

            if current_input_type == "PDF Document":
                uploaded_pdf = st.file_uploader("Upload PDF:", type=["pdf"])
            elif current_input_type == "Image (Problem/Diagram)":
                uploaded_image = st.file_uploader("Upload Image:", type=["png","jpg","jpeg"])

            with col_btn:
                st.write("") 
                st.write("") 
                submit_clicked = st.form_submit_button("🚀 Send")

            if submit_clicked:
                content_parts = []
                display_text = []

                system_prompt = "You are NexStudy AI. Answer concisely but helpful."
                content_parts.append(system_prompt)

                if user_input and user_input.strip():
                    content_parts.append(user_input)
                    display_text.append(user_input)

                if uploaded_pdf:
                    pdf_text = extract_text_from_pdf(uploaded_pdf)
                    if pdf_text:
                        content_parts.append(f"Context from uploaded PDF:\n{pdf_text}")
                        display_text.append(f"📄 [Attached PDF: {uploaded_pdf.name}]")
                
                if uploaded_image:
                    try:
                        img = Image.open(uploaded_image)
                        content_parts.append(img)
                        display_text.append(f"🖼️ [Attached Image: {uploaded_image.name}]")
                    except Exception:
                        pass

                if not display_text and not uploaded_image and not uploaded_pdf:
                    st.warning("Please type a message.")
                else:
                    append_user_message("\n".join(display_text))
                    if gemini_model:
                        with st.spinner("Thinking..."):
                            res = call_gemini(content_parts)
                            if not res.get("error"):
                                append_assistant_message(res["text"])
                                st.rerun()
    
    # ==========================================
    # VIEW 2: TOPIC EXPLAINER OUTPUT
    # ==========================================
    elif mode == "📖 Topic Explainer":
        # No chat bubbles, just clean document view
        if st.session_state.topic_explanation:
            st.markdown("### 📝 Explanation")
            st.markdown("---")
            st.markdown(st.session_state.topic_explanation)
            
            st.markdown("---")
            # Optional: Code block to allow copying the full text
            if st.button("📋 Copy to Clipboard (Manual)"):
                 st.code(st.session_state.topic_explanation)
                 st.info("Copy the text above.")
        else:
            st.info("👈 Select a topic on the left sidebar to generate an explanation here.")
            st.markdown("""
            **What you'll get:**
            - Detailed concepts 📚
            - Simple analogies 🧸
            - Key takeaways 🗝️
            - Useful references 🔗
            """)
