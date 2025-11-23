import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import tempfile

# Try importing gTTS (Google Text-to-Speech)
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# ---------------- Page config ----------------
st.set_page_config(page_title="Audio Notes Podcaster", page_icon="🎧", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo
_logo_path = "/mnt/data/A_logo_for_EduNex,_an_AI-powered_smart_study_assis.png"
if os.path.exists(_logo_path):
    st.image(_logo_path, width=150)

st.title("🎧 Audio Notes (AI Podcaster)")
st.caption("Turn your boring study notes into an engaging audio podcast.")

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
    
    # Check for API Key
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
    
    st.divider()
    
    # Audio Settings
    st.markdown("### 🎙️ Audio Config")
    speech_speed = st.checkbox("Slow Mode", value=False)
    
    if not HAS_GTTS:
        st.error("⚠️ `gTTS` library missing.")
        st.info("Please run: `pip install gTTS` in your terminal.")

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

def text_to_speech(text, slow=False):
    """Converts text to audio bytes using gTTS"""
    try:
        tts = gTTS(text=text, lang='en', slow=slow)
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Audio Generation Error: {e}")
        return None

# ---------------- Session State ----------------
if "podcast_script" not in st.session_state:
    st.session_state.podcast_script = ""

if "audio_file_path" not in st.session_state:
    st.session_state.audio_file_path = None

# ---------------- Layout ----------------
col_input, col_output = st.columns([1, 1])

# ---------------- LEFT COLUMN: Input ----------------
with col_input:
    st.markdown("### 1. 📤 Upload Material")
    
    input_type = st.radio("Source:", ["Paste Text", "Upload PDF"])
    
    source_text = ""
    
    if input_type == "Paste Text":
        source_text = st.text_area("Paste Notes:", height=200, placeholder="Paste your biology notes, history chapter, or essay here...")
    else:
        uploaded_file = st.file_uploader("Upload PDF:", type=["pdf"])
        if uploaded_file:
            source_text = extract_text_from_pdf(uploaded_file)

    st.markdown("### 2. 🎭 Podcast Style")
    style = st.selectbox("Choose Persona:", [
        "Friendly Teacher (Clear & Encouraging)",
        "Curious Host (Conversational & Fun)",
        "Strict Lecturer (Concise & Academic)",
        "Storyteller (Narrative & Engaging)"
    ])
    
    if st.button("🎙️ Generate Audio Note", type="primary"):
        if not source_text.strip():
            st.warning("Please provide some text or a PDF.")
        elif not HAS_GTTS:
            st.error("Cannot generate audio without `gTTS` installed.")
        else:
            if gemini_model:
                with st.spinner("🤖 Writing the script..."):
                    # Step 1: Generate Script
                    prompt = f"""
                    Convert the following study notes into a spoken audio script.
                    
                    **Persona:** {style}
                    **Goal:** summarizing key points for a student listening on headphones.
                    **Rules:**
                    - Keep it conversational (use "Welcome back", "So basically", etc.).
                    - Avoid reading long lists; summarize them.
                    - Keep it under 500 words (about 3-4 minutes).
                    - No special characters or markdown, just plain text to be read aloud.
                    
                    **Content:**
                    {source_text[:6000]} (truncated)
                    """
                    
                    try:
                        resp = gemini_model.generate_content(prompt)
                        script = resp.text
                        st.session_state.podcast_script = script
                        
                        # Step 2: Convert to Audio
                        with st.spinner("🎧 Recording audio..."):
                            audio_path = text_to_speech(script, slow=speech_speed)
                            st.session_state.audio_file_path = audio_path
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.error("API Key missing.")

# ---------------- RIGHT COLUMN: Player ----------------
with col_output:
    st.markdown("### 🎧 Your Audio Note")
    
    if st.session_state.audio_file_path:
        # Audio Player
        st.audio(st.session_state.audio_file_path, format="audio/mp3")
        
        st.success("✅ Audio generated successfully!")
        
        # Download Button
        with open(st.session_state.audio_file_path, "rb") as file:
            st.download_button(
                label="📥 Download MP3",
                data=file,
                file_name="Study_Podcast.mp3",
                mime="audio/mp3"
            )
            
        st.markdown("---")
        st.markdown("### 📜 Transcript")
        with st.expander("View Script", expanded=True):
            st.write(st.session_state.podcast_script)
            
    else:
        st.info("👈 Generate your first audio note on the left!")
        st.markdown(
            """
            **Why use Audio Notes?**
            - 🚶 **Study on the go:** Listen while walking or commuting.
            - 👀 **Rest your eyes:** Take a break from screens.
            - 🧠 **Active Listening:** Hearing concepts explained conversationally helps retention.
            """
        )
