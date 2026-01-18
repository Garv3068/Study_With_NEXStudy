import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
import json
from supabase import create_client, Client
from PIL import Image

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy Tutor", page_icon="🧠", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo & Header Logic ----------------
logo_path = None
if os.path.exists("assets/image.png"):
    logo_path = "assets/image.png"
elif os.path.exists("logo.png"):
    logo_path = "logo.png"
elif os.path.exists("logo.jpg"):
    logo_path = "logo.jpg"

col_logo, col_header = st.columns([1, 6])

with col_logo:
    if logo_path:
        st.image(logo_path, width=100)
    else:
        st.write("🧠")

with col_header:
    st.title("NexStudy AI Tutor")
    st.caption("Your personalized academic guide. Choose your learning style below.")

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

# ---------------- Session State & Data Loading ----------------
user = st.session_state.get("user")

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# SYNC LOGIC: Load history from Supabase if logged in
if user and supabase and not st.session_state.get("chat_history_loaded", False):
    try:
        res = supabase.table("profiles").select("chat_history").eq("id", user["id"]).single().execute()
        if res.data and res.data.get("chat_history"):
            st.session_state.messages = res.data["chat_history"]
    except Exception:
        pass # Fallback to empty if no history
    st.session_state.chat_history_loaded = True

if "saved" not in st.session_state:
    st.session_state.saved = []

if "topic_explanation" not in st.session_state:
    st.session_state.topic_explanation = ""
if "current_topic_query" not in st.session_state:
    st.session_state.current_topic_query = ""

# ---------------- Database Helper ----------------
def save_chat_to_db():
    """Saves current chat history to Supabase."""
    if user and supabase:
        try:
            supabase.table("profiles").update({"chat_history": st.session_state.messages}).eq("id", user["id"]).execute()
            
            # Also update the 'doubts_solved' count for the dashboard
            current_doubts = len([m for m in st.session_state.messages if m["role"] == "user"])
            supabase.table("profiles").update({"doubts_solved": current_doubts}).eq("id", user["id"]).execute()
        except Exception:
            pass

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
        # 🚀 UPGRADE: Using the newer 2.5 Flash model
        return genai.GenerativeModel("gemini-2.5-flash-lite")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Tutor Settings")
    
    if user:
        st.success(f"Logged in: {user.get('email')}")
    else:
        st.info("Guest Mode. Log in on Home to save chat history.")

    # API Key Handling
    api_key_input = None
    if "GEMINI_API_KEY" in st.secrets:
        api_key_input = st.secrets["GEMINI_API_KEY"]
    # else:
        # with st.expander("🔧 Advanced: Use Custom Key"):
            # api_key_input = st.text_input("Enter Gemini API Key:", type="password")

    st.markdown("---")
    
    # 🎭 NEW: Teaching Style Selector
    st.subheader("🎭 Teaching Style")
    teaching_style = st.radio(
        "How should I help you?",
        [
            "Direct Solution (Step-by-step)", 
            "Socratic Guide (Give hints, don't solve)", 
            "ELI5 (Simple language)",
            "Strict Professor (Deep theory)"
        ],
        index=0
    )

# gemini_model = init_gemini(api_key_input)

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
    msg = {"role": "user", "text": text}
    st.session_state.messages.append(msg)
    save_chat_to_db()

def append_assistant_message(text):
    msg = {"role": "assistant", "text": text}
    st.session_state.messages.append(msg)
    save_chat_to_db()

def get_chat_history_text():
    history_context = ""
    # Look deeper into history for better context (last 10 turns)
    recent_messages = st.session_state.messages[-10:]
    for msg in recent_messages:
        role = "Student" if msg["role"] == "user" else "Tutor"
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
        index=0,
        label_visibility="collapsed"
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
                if user and supabase:
                    try:
                        supabase.table("profiles").update({"chat_history": []}).eq("id", user["id"]).execute()
                    except: pass
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
        st.markdown("#### 🧠 Deep Dive")
        topic_input = st.text_input("Concept:", placeholder="e.g. Black Holes, Recursion")
        explanation_level = st.selectbox("Depth:", ["ELI5", "High School", "College", "PhD"])
        # include_links = st.checkbox("Include Video Search Links", value=True)
        
        if st.button("🚀 Explain", type="primary"):
            if not topic_input.strip():
                st.warning("Enter a topic.")
            else:
                st.session_state.current_topic_query = topic_input
                # PROMPT FIX: Explicitly tell AI NOT to generate fake URLs
                prompt = f"Explain '{topic_input}'. Level: {explanation_level}."
                # if include_links: 
                    # prompt += " Recommend 3 YouTube channels or video titles to watch. Do NOT provide direct links (URLs), just the names."
                
                if gemini_model:
                    with st.spinner("Explaining..."):
                        res = call_gemini([f"You are an expert tutor. {prompt}"])
                        if not res.get("error"):
                            st.session_state.topic_explanation = res["text"]
                            st.rerun()
                        else:
                            st.error(res["error"])
                else:
                    st.error("API Key missing.")

# ---------------- RIGHT COLUMN: Interaction Area ----------------
with right:
    
    # === CHAT VIEW ===
    if mode == "💬 Doubt Solver & Chat":
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.messages):
                if msg["role"] == "user":
                    user_text = msg['text'].replace('\n', '<br>')
                    st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; color: #000000; border-left: 5px solid #4F46E5;">
                            <h5 style="margin: 0 0 8px 0; color: #444;">👤 You</h5>
                            <div style="font-size: 1rem;">{user_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"### 🤖 NexStudy")
                    st.markdown(msg['text'])
                    
                    # Tool Buttons below AI text
                    b1, b2, b3 = st.columns([1,1,1])
                    if b1.button("Simplify 👶", key=f"s_{i}"):
                        res = call_gemini([f"Simplify this specific explanation:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()
                    if b2.button("Show Steps 🪜", key=f"st_{i}"):
                        res = call_gemini([f"Break this down into numbered step-by-step logic:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()
                    if b3.button("Save 💾", key=f"sv_{i}"):
                        st.session_state.saved.append({"text": msg["text"], "timestamp": str(datetime.datetime.now())})
                        st.success("Saved!")
                    st.divider()

        # Input Form
        st.write("")
        with st.form(key="chat_form", clear_on_submit=True):
            col_in, col_btn = st.columns([6, 1])
            with col_in:
                user_input = st.text_area("Ask a question...", height=80, key="u_in", placeholder="How do I calculate...?")
            
            uploaded_pdf = None
            uploaded_image = None
            
            # Conditional uploaders based on selection
            if st.session_state.get("input_type") == "PDF Document":
                uploaded_pdf = st.file_uploader("PDF:", type=["pdf"])
            elif st.session_state.get("input_type") == "Image (Problem)":
                uploaded_image = st.file_uploader("Image:", type=["png","jpg","jpeg"])

            with col_btn:
                st.write("")
                st.write("")
                if st.form_submit_button("🚀 Send"):
                    history_text = get_chat_history_text()
                    
                    # 🎭 DYNAMIC SYSTEM PROMPT BASED ON STYLE
                    persona_instruction = ""
                    if teaching_style == "Direct Solution (Step-by-step)":
                        persona_instruction = "Provide a clear, correct, and direct answer. Show all steps if it is a math/science problem."
                    elif teaching_style == "Socratic Guide (Give hints, don't solve)":
                        persona_instruction = "Do NOT give the final answer immediately. Ask the student a guiding question to help them figure it out. Act like a supportive coach."
                    elif teaching_style == "ELI5 (Simple language)":
                        persona_instruction = "Explain like the user is 5 years old. Use analogies (cars, pizza, games). Avoid jargon."
                    elif teaching_style == "Strict Professor (Deep theory)":
                        persona_instruction = "Be formal and academic. Focus on the underlying theory and definitions. Use precise terminology."

                    # PROMPT FIX: Added strict instruction to avoid fake links
                    system_prompt = f"""
                    You are NexStudy, an expert AI Tutor.
                    **Current Teaching Style:** {teaching_style}
                    **Instruction:** {persona_instruction}
                    
                    **Context from previous conversation:**
                    {history_text}
                    
                    **Task:** Answer the new user question/file below.
                    After your answer, suggest 3 short follow-up questions the student might want to ask next to deepen their understanding.
                    
                    **IMPORTANT:** Do NOT generate direct URL links (like youtube.com/...) as they are often incorrect/hallucinated. If you recommend a video, just give the Title and Channel Name.
                    """
                    
                    content_parts = [system_prompt]
                    display_text = []

                    if user_input.strip():
                        content_parts.append(f"Student Question: {user_input}")
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
    
    # === TOPIC EXPLAINER VIEW ===
    elif mode == "📖 Topic Explainer":
        if st.session_state.topic_explanation:
            st.markdown("### 📝 Topic Guide")
            st.markdown(st.session_state.topic_explanation)
            
            # UI FIX: Provide a REAL working search button instead of fake links
            st.markdown("---")
            if st.session_state.get("current_topic_query"):
                search_term = st.session_state.current_topic_query.replace(' ', '+')
                st.link_button("📺 Search This Topic on YouTube", f"https://www.youtube.com/results?search_query={search_term}")
            
            if st.button("📋 Copy Text"):
                 st.code(st.session_state.topic_explanation)
        else:
            st.info("👈 Use the sidebar to generate a deep-dive topic guide.")
