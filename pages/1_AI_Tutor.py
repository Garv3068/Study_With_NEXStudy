import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
import json
from supabase import create_client, Client
from PIL import Image

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy", page_icon="🧠", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("assets/image.png"):
    st.image("assets/image.png", width=150)
elif os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("🧠 NexStudy")
st.caption("Your personal AI academic companion. Solve doubts, learn topics, and master your syllabus.")

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

# ---------------- Database Helper ----------------
def save_chat_to_db():
    """Saves current chat history to Supabase."""
    if user and supabase:
        try:
            # We save the whole list. In production apps, you might append, 
            # but replacing the JSON array is easier for this scale.
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
        st.info("Guest Mode. Log in on Home to save chat history.")

    # API Key Handling
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

def append_user_message(text):
    msg = {"role": "user", "text": text}
    st.session_state.messages.append(msg)
    save_chat_to_db() # Auto-save

def append_assistant_message(text):
    msg = {"role": "assistant", "text": text}
    st.session_state.messages.append(msg)
    save_chat_to_db() # Auto-save

def get_chat_history_text():
    history_context = ""
    recent_messages = st.session_state.messages[-6:]
    for msg in recent_messages:
        role = "User" if msg["role"] == "user" else "NexStudy AI"
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
                if user and supabase:
                    # Clear DB too
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
        st.markdown("#### 🧠 Learn a Concept")
        topic_input = st.text_input("Topic:", placeholder="e.g. Thermodynamics")
        explanation_level = st.selectbox("Depth:", ["ELI5", "High School", "College", "PhD"])
        include_links = st.checkbox("Include Video Links", value=True)
        
        if st.button("🚀 Explain", type="primary"):
            if not topic_input.strip():
                st.warning("Enter a topic.")
            else:
                prompt = f"Explain '{topic_input}'. Level: {explanation_level}."
                if include_links: prompt += " Include 3 YouTube resource links."
                
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
    
    if mode == "💬 Doubt Solver & Chat":
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.messages):
                if msg["role"] == "user":
                    user_text = msg['text'].replace('\n', '<br>')
                    st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; color: #000000;">
                            <h5 style="margin: 0 0 8px 0; color: #444;">👤 You</h5>
                            <div style="font-size: 1rem;">{user_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"### 🧠 NexStudy")
                    st.markdown(msg['text'])
                    
                    b1, b2, b3 = st.columns([1,1,1])
                    if b1.button("Simplify", key=f"s_{i}"):
                        res = call_gemini([f"Simplify this:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()
                    if b2.button("Steps", key=f"st_{i}"):
                        res = call_gemini([f"Show steps:\n\n{msg['text']}"])
                        if not res.get("error"): append_assistant_message(res["text"]); st.rerun()
                    if b3.button("Save", key=f"sv_{i}"):
                        st.session_state.saved.append({"text": msg["text"], "timestamp": str(datetime.datetime.now())})
                        st.success("Saved!")
                    st.divider()

        # Input Form
        st.write("")
        with st.form(key="chat_form", clear_on_submit=True):
            col_in, col_btn = st.columns([6, 1])
            with col_in:
                user_input = st.text_area("Type your question...", height=80, key="u_in")
            
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
                    history_text = get_chat_history_text()
                    system_prompt = f"You are NexStudy. Context:\n{history_text}\nAnswer the new question."
                    
                    content_parts = [system_prompt]
                    display_text = []

                    if user_input.strip():
                        content_parts.append(user_input)
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
    
    elif mode == "📖 Topic Explainer":
        if st.session_state.topic_explanation:
            st.markdown("### 📝 Topic Guide")
            st.markdown(st.session_state.topic_explanation)
        else:
            st.info("👈 Use the sidebar to generate a topic guide.")
