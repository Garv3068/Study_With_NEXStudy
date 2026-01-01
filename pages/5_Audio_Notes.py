import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import tempfile
import datetime
import json
from supabase import create_client, Client

# Try importing gTTS (Google Text-to-Speech)
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# ---------------- Page config ----------------
st.set_page_config(page_title="Audio Notes", page_icon="🎧", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("assets/image.png"):
    st.image("assets/image.png", width=150)
elif os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("🎧 Audio Notes Studio")
st.caption("Convert text to audio podcasts OR transcribe lecture recordings into notes.")

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

# ---------------- Session State ----------------
user = st.session_state.get("user")

if "podcast_script" not in st.session_state:
    st.session_state.podcast_script = ""
if "audio_file_path" not in st.session_state:
    st.session_state.audio_file_path = None
if "transcription_result" not in st.session_state:
    st.session_state.transcription_result = ""

# ---------------- Database Functions ----------------
def fetch_saved_audio():
    """Fetch saved_audio array from Supabase profiles"""
    if not user or not supabase: return []
    try:
        res = supabase.table("profiles").select("saved_audio").eq("id", user["id"]).single().execute()
        if res.data and res.data.get("saved_audio"):
            return res.data["saved_audio"]
    except: pass
    return []

def save_audio_entry(entry):
    """Append new audio/transcript entry to saved_audio in Supabase"""
    if not user or not supabase: return False
    try:
        current_data = fetch_saved_audio()
        # Add timestamp title if missing
        if "title" not in entry:
            entry["title"] = f"Audio Note {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        current_data.append(entry)
        
        # Update DB
        supabase.table("profiles").update({"saved_audio": current_data}).eq("id", user["id"]).execute()
        
        # Update stats
        try:
            res = supabase.table("profiles").select("audio_generated").eq("id", user["id"]).single().execute()
            count = res.data.get("audio_generated", 0) or 0
            supabase.table("profiles").update({"audio_generated": count + 1}).eq("id", user["id"]).execute()
        except: pass
            
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

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
        return genai.GenerativeModel("gemini-2.5-flash-lite")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    if user:
        st.success(f"Logged in: {user.get('email')}")
    else:
        st.warning("Guest Mode. Sign in to save audio notes.")
    
    api_key_input = None
    if "GEMINI_API_KEY" in st.secrets:
        api_key_input = st.secrets["GEMINI_API_KEY"]
    else:
        api_key_input = st.text_input("Enter Gemini API Key:", type="password")
    
    st.divider()
    if not HAS_GTTS:
        st.error("⚠️ `gTTS` library missing. Run `pip install gTTS`.")

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

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📝 Notes ➡️ Audio", "🎙️ Audio ➡️ Notes", "💾 Saved Library"])

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
            "Friendly Teacher", "Curious Host", "Strict Lecturer", "Storyteller"
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
        st.markdown("### 🎧 Podcast Player")
        if st.session_state.audio_file_path:
            st.audio(st.session_state.audio_file_path, format="audio/mp3")
            with open(st.session_state.audio_file_path, "rb") as file:
                st.download_button("📥 Download MP3", file, "Study_Podcast.mp3", "audio/mp3")
            
            with st.expander("📜 View Script", expanded=True):
                st.write(st.session_state.podcast_script)
                
            if user:
                if st.button("💾 Save Script to Library"):
                    entry = {
                        "type": "podcast_script",
                        "content": st.session_state.podcast_script,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "tags": [style]
                    }
                    if save_audio_entry(entry):
                        st.success("Saved to Library!")
        else:
            st.info("👈 Generate audio to listen here.")

# =======================================================
# TAB 2: AUDIO TO NOTES (TRANSCRIBER)
# =======================================================
with tab2:
    st.markdown("### 🎙️ Lecture to Notes")
    st.caption("Upload a lecture recording (MP3/WAV) and get structured study notes.")
    
    col_up, col_res = st.columns([1, 2])
    
    with col_up:
        uploaded_audio = st.file_uploader("Upload Audio:", type=["mp3", "wav", "m4a", "ogg"])
        detail_level = st.select_slider("Summary Detail:", ["Brief", "Key Points", "Detailed"])
        
        if st.button("📝 Transcribe", type="primary"):
            if not uploaded_audio:
                st.warning("Upload audio first.")
            elif not gemini_model:
                st.error("API Key missing.")
            else:
                with st.spinner("🎧 Analyzing..."):
                    try:
                        audio_bytes = uploaded_audio.read()
                        prompt_text = f"""
                        Listen to this audio. Transcribe and summarize it ({detail_level}).
                        Format: Title, Summary, Key Concepts (Bullet points), Quiz (3 questions).
                        """
                        content = [prompt_text, {"mime_type": uploaded_audio.type, "data": audio_bytes}]
                        
                        response = gemini_model.generate_content(content)
                        st.session_state.transcription_result = response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col_res:
        if st.session_state.transcription_result:
            st.markdown(st.session_state.transcription_result)
            st.download_button("📥 Download Notes", st.session_state.transcription_result, "Notes.md")
            
            if user:
                if st.button("💾 Save Notes to Library"):
                    entry = {
                        "type": "transcript",
                        "content": st.session_state.transcription_result,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "title": f"Lecture Notes ({datetime.datetime.now().strftime('%m/%d')})"
                    }
                    if save_audio_entry(entry):
                        st.success("Saved!")
        else:
            st.info("👈 Upload audio to start.")

# =======================================================
# TAB 3: SAVED LIBRARY
# =======================================================
with tab3:
    st.markdown("### 📚 Your Saved Audio & Notes")
    if user and supabase:
        saved_items = fetch_saved_audio()
        if saved_items:
            for i, item in enumerate(reversed(saved_items)):
                with st.expander(f"{item.get('title', 'Untitled')} ({item.get('date')}) - {item.get('type')}"):
                    st.markdown(item.get('content'))
                    if item.get('type') == 'podcast_script':
                        if st.button("🔄 Regenerate Audio", key=f"regen_{i}"):
                            with st.spinner("Regenerating..."):
                                path = text_to_speech(item['content'])
                                st.session_state.audio_file_path = path
                                st.session_state.podcast_script = item['content']
                                st.rerun()
        else:
            st.info("Library is empty.")
    else:
        st.warning("Log in to view your library.")
