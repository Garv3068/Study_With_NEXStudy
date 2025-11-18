# pages/6_AI_Tutor.py
import streamlit as st
import google.generativeai as genai
import re
import datetime

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(
    page_title="AI Tutor | NexStudy",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 NexStudy AI Tutor")
st.caption("Your personal AI-powered learning companion — choose explanation depth and get helpful links.")

# ---------------------------
# CONSTANTS & USAGE LIMIT
# ---------------------------
DAILY_LIMIT = 7     # requests per user per day

# ---------------------------
# SESSION STATE (usage counting)
# ---------------------------
if "usage_count" not in st.session_state:
    st.session_state["usage_count"] = 0
if "last_reset" not in st.session_state:
    st.session_state["last_reset"] = str(datetime.date.today())
# auto reset each day
today = str(datetime.date.today())
if st.session_state["last_reset"] != today:
    st.session_state["usage_count"] = 0
    st.session_state["last_reset"] = today

# ---------------------------
# GEMINI INITIALIZATION
# ---------------------------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=key)
        try:
            return genai.GenerativeModel("gemini-2.5-flash-lite")
        except Exception:
            st.warning("⚠️ Gemini 2.5 Flash not available. Switching to Gemini 2.0 Flash.")
            return genai.GenerativeModel("gemini-2.0-flash-lite")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

gemini_model = init_gemini()

# ---------------------------
# UTILS: prompt builder + link extractor
# ---------------------------
def build_prompt(topic: str, level: str, request_youtube: bool = True, max_examples: int = 2):
    """
    Build a prompt tailored to the chosen explanation level.
    """
    level_map = {
        "ELI5": "Explain the topic in the simplest possible terms using analogies and short sentences. Assume the reader is 5 years old.",
        "School": "Explain the topic clearly at school level, with short examples and simple definitions.",
        "College": "Explain the topic in technical but clear terms suitable for a college student. Include key definitions and a short example.",
        "Exam": "Provide a concise, exam-oriented answer with bullet points, key formulas, and a short revision checklist. Keep it crisp and to the point.",
        "Research": "Provide an in-depth explanation, mention common pitfalls, further reading pointers, and 2-3 advanced resources."
    }
    instruction = level_map.get(level, level_map["College"])

    extra = ""
    if request_youtube:
        extra = "Also include 2–3 relevant YouTube links and 2–3 web links (if available) that help understand the topic. " \
                "Mark links clearly so they can be extracted (e.g., start links on a new line)."

    prompt = (
        f"You are an expert tutor. {instruction}\n\n"
        f"Topic: {topic}\n\n"
        f"{extra}\n\n"
        "Answer in English. Use short paragraphs or bullet points depending on the 'level'.\n"
    )
    return prompt

def extract_links(text: str):
    # Find URLs in the text
    urls = re.findall(r'(https?://[^\s)>\]]+)', text)
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered

# ---------------------------
# UI: show remaining requests (live)
# ---------------------------
requests_left = DAILY_LIMIT - st.session_state["usage_count"]
st.info(f"📊 Requests Left Today: {requests_left}/{DAILY_LIMIT}")
st.progress(min(st.session_state["usage_count"]/DAILY_LIMIT, 1.0))

# ---------------------------
# User controls
# ---------------------------
st.markdown("### 📘 Ask your AI Tutor")
topic = st.text_input("Enter a topic you want to learn (e.g., Recursion, HTML Tags, Machine Learning):")

level = st.selectbox("Choose explanation level:", ["ELI5", "School", "College", "Exam", "Research"])
include_links = st.checkbox("Include YouTube & web links (recommended)", value=True)

# ---------------------------
# Guard: usage limit
# ---------------------------
if requests_left <= 0:
    st.error("🚫 Daily limit reached! You can ask more questions tomorrow.")
    st.stop()

# ---------------------------
# Core function: call Gemini
# ---------------------------
def get_explanation(topic_text: str, level_choice: str, include_links_flag: bool):
    if not gemini_model:
        return {"error": "Gemini model not initialized."}

    prompt = build_prompt(topic_text, level_choice, request_youtube=include_links_flag)
    try:
        resp = gemini_model.generate_content(prompt)
        raw = resp.text or ""
        links = extract_links(raw)
        return {"text": raw.strip(), "links": links}
    except Exception as e:
        return {"error": str(e)}

# ---------------------------
# Action: Explain
# ---------------------------
if st.button("🧠 Explain Topic"):
    if not topic.strip():
        st.warning("Please enter a topic before clicking 'Explain Topic'.")
    else:
        # increment usage count immediately to avoid race
        st.session_state["usage_count"] += 1
        requests_left = DAILY_LIMIT - st.session_state["usage_count"]

        with st.spinner("📚 Generating explanation..."):
            result = get_explanation(topic, level, include_links)

        if result.get("error"):
            st.error(f"Error generating explanation: {result['error']}")
        else:
            st.markdown("---")
            st.markdown(result["text"])
            st.markdown("---")
            if result["links"]:
                st.subheader("🔗 Links & Videos")
                for u in result["links"]:
                    # show cleaned display
                    st.write(f"- [{u}]({u})")
            st.success(f"✨ Request used! Remaining: {requests_left}/{DAILY_LIMIT}")
            st.progress(min(st.session_state["usage_count"]/DAILY_LIMIT, 1.0))

# ---------------------------
# Footer help
# ---------------------------
st.markdown("<br/><br/>", unsafe_allow_html=True)
st.info("💡 Tip: Use 'ELI5' for quick intuitive understanding, 'Exam' for concise revision notes.")
