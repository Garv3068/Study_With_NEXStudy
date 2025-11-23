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
st.set_page_config(page_title="Audio Notes", page_icon="🎧", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# Optional logo
# _logo_path = "/mnt/data/A_logo_for_EduNex,_an_AI-powered_smart_study_assis.png"
# if os.path.exists(_logo_path):
    # st.image(_logo_path, width=150)
if os.path.exists("image.png"):
    st.image("image.png", width=200)

st.title("🎧 Audio Notes Studio")
st.caption("Convert text to audio podcasts OR transcribe lecture recordings into notes.")

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
    
    # Check libraries
    if not HAS_GTTS:
        st.error("⚠️ `gTTS` library missing.")
        st.info("Run `pip install gTTS` to use the Podcaster feature.")

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
if "transcription_result" not in st.session_state:
    st.session_state.transcription_result = ""

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["📝 Notes -> Audio (Podcaster)", "🎙️ Audio -> Notes (Transcriber)"])

# =======================================================
# TAB 1: TEXT TO AUDIO (PODCASTER)
# =======================================================
with tab1:
    col_input, col_output = st.columns([1, 1])

    # LEFT: Input
    with col_input:
        st.markdown("### 1. 📤 Source Material")
        input_type = st.radio("Input Source:", ["Paste Text", "Upload PDF"], key="tts_radio")
        
        source_text = ""
        if input_type == "Paste Text":
            source_text = st.text_area("Paste Notes:", height=200, placeholder="Paste biology notes, history chapter...", key="tts_area")
        else:
            uploaded_file = st.file_uploader("Upload PDF:", type=["pdf"], key="tts_pdf")
            if uploaded_file:
                source_text = extract_text_from_pdf(uploaded_file)

        st.markdown("### 2. 🎭 Podcast Style")
        style = st.selectbox("Choose Persona:", [
            "Friendly Teacher (Clear & Encouraging)",
            "Curious Host (Conversational & Fun)",
            "Strict Lecturer (Concise & Academic)",
            "Storyteller (Narrative & Engaging)"
        ])
        
        speed_check = st.checkbox("Slow Speed", value=False)
        
        if st.button("🎙️ Generate Audio", type="primary"):
            if not source_text.strip():
                st.warning("Please provide text/PDF.")
            elif not HAS_GTTS:
                st.error("gTTS missing.")
            else:
                if gemini_model:
                    with st.spinner("🤖 Writing script..."):
                        prompt = f"""
                        Convert these notes into a spoken audio script.
                        **Persona:** {style}
                        **Rules:** Conversational, summarize lists, under 500 words. No markdown.
                        **Content:** {source_text[:6000]}
                        """
                        try:
                            resp = gemini_model.generate_content(prompt)
                            st.session_state.podcast_script = resp.text
                            
                            with st.spinner("🎧 Recording..."):
                                audio_path = text_to_speech(st.session_state.podcast_script, slow=speed_check)
                                st.session_state.audio_file_path = audio_path
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.error("API Key missing.")

    # RIGHT: Player
    with col_output:
        # st.markdown("### 🎧 Podcast Player")
        if st.session_state.audio_file_path:
            st.audio(st.session_state.audio_file_path, format="audio/mp3")
            with open(st.session_state.audio_file_path, "rb") as file:
                st.download_button("📥 Download MP3", file, "Study_Podcast.mp3", "audio/mp3")
            
            with st.expander("📜 View Script", expanded=False):
                st.write(st.session_state.podcast_script)
        # else:
            # st.info("👈 Generate audio to listen here.")

# =======================================================
# TAB 2: AUDIO TO NOTES (TRANSCRIBER)
# =======================================================
with tab2:
    st.markdown("### 🎙️ Lecture to Notes")
    st.caption("Upload a lecture recording (MP3/WAV) and get structured study notes.")
    
    col_up, col_res = st.columns([1, 2])
    
    with col_up:
        uploaded_audio = st.file_uploader("Upload Audio:", type=["mp3", "wav", "m4a", "ogg"])
        
        detail_level = st.select_slider(
            "Summary Detail:", 
            options=["Brief Overview", "Key Points Bulletins", "Detailed Study Notes"]
        )
        
        if st.button("📝 Transcribe & Summarize", type="primary"):
            if not uploaded_audio:
                st.warning("Please upload an audio file first.")
            elif not gemini_model:
                st.error("API Key missing.")
            else:
                with st.spinner("🎧 Listening and analyzing... (This may take a minute)"):
                    try:
                        # Prepare audio data for Gemini
                        audio_bytes = uploaded_audio.read()
                        
                        prompt_text = f"""
                        Listen to this audio file and transcribe it into {detail_level}.
                        
                        **Format Requirements:**
                        1. **Title:** Give it a relevant title.
                        2. **Summary:** A brief paragraph intro.
                        3. **Key Concepts:** Use bullet points with bold headers.
                        4. **Important Terms:** Define any technical terms mentioned.
                        5. **Quiz:** 3 short review questions at the end.
                        """
                        
                        # Gemini 1.5/2.0 accepts audio bytes directly
                        content = [
                            prompt_text,
                            {
                                "mime_type": uploaded_audio.type,
                                "data": audio_bytes
                            }
                        ]
                        
                        response = gemini_model.generate_content(content)
                        st.session_state.transcription_result = response.text
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Processing Error: {str(e)}")
                        st.info("Note: Large audio files (>20MB) may timeout in this demo.")

    with col_res:
        if st.session_state.transcription_result:
            st.markdown("### 📝 Generated Notes")
            st.markdown("---")
            st.markdown(st.session_state.transcription_result)
            
            st.markdown("---")
            st.download_button(
                "📥 Download Notes", 
                st.session_state.transcription_result, 
                "Lecture_Notes.md", 
                "text/markdown"
            )
        else:
            st.info("👈 Upload a recording to generate notes.")
            st.markdown("""
            **Perfect for:**
            - 🏛️ Recorded University Lectures
            - 🗣️ Voice memos of your own ideas
            - 📹 Podcast summaries
            """)
