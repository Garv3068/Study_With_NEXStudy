# pages/6_AI_Tutor.py
import streamlit as st
import textwrap

# Try import Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except Exception:
    GEMINI_SDK_AVAILABLE = False

st.set_page_config(page_title="AI Tutor", page_icon="🎓", layout="wide")
st.title("🎓 EduNex — AI Tutor (Explain ● Notes ● Quiz)")
st.caption("Uses Gemini Flash for clear student-friendly explanations. Session memory is kept for the conversation.")

# -------------------------
# Initialize Gemini model
# -------------------------
@st.cache_resource(show_spinner=False)
def init_gemini_model():
    # Returns model object or None
    if not GEMINI_SDK_AVAILABLE:
        return None
    # Read key from secrets safely
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    if not key:
        return None
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except Exception:
        return None

gemini_model = init_gemini_model()

# -------------------------
# Session state defaults
# -------------------------
if "tutor_history" not in st.session_state:
    st.session_state.tutor_history = []  # list of dicts: {topic, explanation, notes, quiz}

# -------------------------
# Helper: safe extract text from Gemini response
# -------------------------
def extract_gemini_text(response):
    """
    Try common shapes for the SDK response and return a string.
    """
    try:
        # object with candidates -> content -> text (newer SDK)
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            # cand.content might be a list of items with 'text' fields
            content = getattr(cand, "content", None)
            if isinstance(content, (list, tuple)) and len(content) > 0:
                maybe = content[0]
                # try attribute or dict
                text = getattr(maybe, "text", None) or (maybe.get("text") if isinstance(maybe, dict) else None)
                if text:
                    return text
            # fallback to candidate.display or str(cand)
            text = getattr(cand, "display", None) or str(cand)
            return text
        # older shape: response.text
        if hasattr(response, "text") and response.text:
            return response.text
        # dict-like shapes
        if isinstance(response, dict):
            try:
                return response["candidates"][0]["content"][0]["text"]
            except Exception:
                pass
        return str(response)
    except Exception:
        try:
            return str(response)
        except Exception:
            return "Error extracting model output."

# -------------------------
# Prompts templates
# -------------------------
def build_explain_prompt(topic: str) -> str:
    return textwrap.dedent(f"""
        You are a kind, clear, and concise college-level tutor. Explain the following topic in plain English
        aimed at undergraduate students. Structure the response with:
        1) A short one-line definition.
        2) A step-by-step, easy-to-follow detailed explanation in simple language.
        3) One coding or real-world example (if relevant), with brief code or steps.
        4) 3-5 key takeaway bullet points at the end.

        Topic: {topic}

        Keep language English, avoid irrelevant cultural references, and be direct and helpful.
    """)

def build_notes_prompt(explanation_text: str) -> str:
    # Ask the model to extract concise revision notes from an explanation
    return textwrap.dedent(f"""
        You are an assistant that converts an explanation into short revision notes.
        Given the following explanation, produce 5 concise bullet points (each 1-2 short sentences) that capture the key ideas.
        Keep each bullet simple and actionable for quick revision.

        Explanation:
        {explanation_text}
    """)

def build_quiz_prompt(explanation_text: str, topic: str) -> str:
    # Ask model to create adaptive quiz: MCQs when possible, otherwise short conceptual questions
    return textwrap.dedent(f"""
        You are an educational content generator. Create a short revision quiz about the topic "{topic}" using the provided explanation.
        Output exactly 3 questions. For each question include:
        - Question line
        - If appropriate, 3-4 options labeled (A), (B), (C), (D)
        - Indicate the correct option or answer clearly after the question block (for example: Correct: B)

        Use simple language suitable for undergraduate students. Prefer multiple-choice for factual parts and short-answer for conceptual parts.
        Explanation for quiz creation:
        {explanation_text}
    """)

# -------------------------
# UI: Input area & buttons
# -------------------------
col1, col2 = st.columns([4,1])
with col1:
    user_topic = st.text_area("Enter topic / question / or paste text (for summarization)", height=160, placeholder="e.g., Explain recursion in programming with a Python example")
with col2:
    st.write("")  # spacer
    if gemini_model is None:
        st.warning("Gemini Flash not configured (GEMINI_API_KEY missing or SDK unavailable). Add key in .streamlit/secrets.toml to enable high-quality outputs.")
        explain_disabled = True
    else:
        explain_disabled = False

btn_col1, btn_col2, btn_col3 = st.columns(3)
explain_clicked = btn_col1.button("🧠 Explain", disabled=explain_disabled)
notes_clicked = btn_col2.button("📋 Generate Smart Notes", disabled=explain_disabled)
quiz_clicked = btn_col3.button("📝 Generate Adaptive Quiz", disabled=explain_disabled)

# -------------------------
# Core actions
# -------------------------
def call_gemini(prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
    if gemini_model is None:
        raise RuntimeError("Gemini model not available.")
    resp = gemini_model.generate_content(prompt=prompt, temperature=temperature, max_output_tokens=max_tokens)
    return extract_gemini_text(resp)

# Explain action
if explain_clicked:
    if not user_topic.strip():
        st.warning("Please enter a topic or text to explain.")
    else:
        with st.spinner("Generating explanation..."):
            try:
                prompt = build_explain_prompt(user_topic.strip())
                explanation_text = call_gemini(prompt, max_tokens=600, temperature=0.0)
                # store in session history
                entry = {"topic": user_topic.strip(), "explanation": explanation_text, "notes": None, "quiz": None}
                st.session_state.tutor_history.append(entry)
                st.success("Explanation generated.")
            except Exception as e:
                st.error(f"Error generating explanation: {e}")
                explanation_text = None

# Notes action (generate from last explanation or current input)
if notes_clicked:
    # choose source text: last explanation if exists and topic matches, else use user input
    source_text = None
    if st.session_state.tutor_history:
        source_text = st.session_state.tutor_history[-1].get("explanation")
    if not source_text:
        # if no prior explanation, attempt to use user input as explanation
        source_text = user_topic.strip()
    if not source_text:
        st.warning("No explanation or text available to generate notes from. First generate an explanation or paste text.")
    else:
        with st.spinner("Generating smart notes..."):
            try:
                notes_prompt = build_notes_prompt(source_text)
                notes_text = call_gemini(notes_prompt, max_tokens=300, temperature=0.0)
                # attach notes to latest history entry if exists, else create new entry
                if st.session_state.tutor_history:
                    st.session_state.tutor_history[-1]["notes"] = notes_text
                else:
                    st.session_state.tutor_history.append({"topic": user_topic.strip(), "explanation": None, "notes": notes_text, "quiz": None})
                st.success("Smart notes created.")
            except Exception as e:
                st.error(f"Error generating notes: {e}")

# Quiz action
if quiz_clicked:
    source_text = None
    last_topic = user_topic.strip()
    if st.session_state.tutor_history:
        # prefer last explanation and topic
        last_entry = st.session_state.tutor_history[-1]
        source_text = last_entry.get("explanation") or last_entry.get("notes")
        last_topic = last_entry.get("topic") or last_topic
    if not source_text:
        source_text = user_topic.strip()
    if not source_text:
        st.warning("No content available to make a quiz from. First generate an explanation or paste text.")
    else:
        with st.spinner("Generating adaptive quiz..."):
            try:
                quiz_prompt = build_quiz_prompt(source_text, last_topic or "the topic")
                quiz_text = call_gemini(quiz_prompt, max_tokens=400, temperature=0.0)
                if st.session_state.tutor_history:
                    st.session_state.tutor_history[-1]["quiz"] = quiz_text
                else:
                    st.session_state.tutor_history.append({"topic": last_topic, "explanation": None, "notes": None, "quiz": quiz_text})
                st.success("Quiz generated.")
            except Exception as e:
                st.error(f"Error generating quiz: {e}")

# -------------------------
# Display latest results
# -------------------------
st.markdown("---")
st.subheader("Session — Latest Outputs")

if st.session_state.tutor_history:
    last = st.session_state.tutor_history[-1]
    if last.get("topic"):
        st.markdown(f"**Topic:** {last['topic']}")
    if last.get("explanation"):
        st.markdown("### 📘 Explanation")
        st.write(last["explanation"])
    if last.get("notes"):
        st.markdown("### 📝 Smart Notes")
        # Try to show as bullet points if possible (split on newlines)
        notes = last["notes"].strip()
        # naive split to bullets by newlines; if not, show raw
        lines = [ln.strip("-• ") for ln in notes.splitlines() if ln.strip()]
        if len(lines) > 1:
            for ln in lines:
                st.write(f"- {ln}")
        else:
            st.write(notes)
    if last.get("quiz"):
        st.markdown("### 🧪 Adaptive Quiz")
        st.write(last["quiz"])
else:
    st.info("No outputs yet. Ask a topic and click 'Explain' to start.")

# -------------------------
# Conversation history (compact)
# -------------------------
st.markdown("---")
with st.expander("Conversation History (latest first)"):
    for entry in reversed(st.session_state.tutor_history[-10:]):
        t = entry.get("topic", "")
        st.markdown(f"**Topic:** {t}")
        if entry.get("explanation"):
            st.write(entry["explanation"])
        if entry.get("notes"):
            st.write("**Notes:**")
            st.write(entry["notes"])
        if entry.get("quiz"):
            st.write("**Quiz:**")
            st.write(entry["quiz"])
        st.markdown("---")

# -------------------------
# Utilities: clear history
# -------------------------
if st.button("Clear Session History"):
    st.session_state.tutor_history = []
    st.success("Session history cleared.")
