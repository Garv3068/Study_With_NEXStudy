import streamlit as st
import google.generativeai as genai
import re

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(
    page_title="AI Tutor | EduNex",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 EduNex AI Tutor")
st.caption("Your personal AI-powered learning companion — explain any topic clearly with real web insights.")

# ---------------------------
# GEMINI INITIALIZATION
# ---------------------------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=key)

        # Try preferred model
        try:
            return genai.GenerativeModel("gemini-2.5-flash")
        except Exception:
            st.warning("⚠️ Gemini 2.5 Flash model not found, switching to Gemini 2.0 Flash.")
            return genai.GenerativeModel("gemini-2.0-flash")

    except KeyError:
        st.error("🔑 Gemini API key not found in secrets.toml file.")
        return None
    except Exception as e:
        st.error(f"Error initializing Gemini: {e}")
        return None


gemini_model = init_gemini()

# ---------------------------
# AI TUTOR FUNCTION
# ---------------------------
def get_explanation(topic):
    if not gemini_model:
        return "Gemini model not initialized properly."

    try:
        # Construct the system-style prompt for educational context
        prompt_text = (
            f"You are an educational AI tutor. Explain the topic '{topic}' "
            "in a clear, simple, and structured way for a student. "
            "Also, provide 2–3 relevant YouTube video links that help in understanding the topic better."
        )

        response = gemini_model.generate_content(prompt_text)
        if not response or not response.text.strip():
            return "Sorry, I couldn’t generate a helpful explanation. Please try again."

        return response.text

    except Exception as e:
        return f"Error generating explanation: {e}"

# ---------------------------
# USER INPUT SECTION
# ---------------------------
st.markdown("### 📘 Ask your AI Tutor")

topic = st.text_input("Enter a topic you want to learn about (e.g., Recursion, HTML Tags, Machine Learning):")

if st.button("🧠 Explain Topic"):
    if topic.strip():
        with st.spinner("📚 Generating a detailed explanation..."):
            explanation = get_explanation(topic)
            st.markdown("---")
            st.markdown(explanation)
            st.markdown("---")
    else:
        st.warning("Please enter a topic before clicking 'Explain Topic'.")

# ---------------------------
# FOOTER
# ---------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.info("💡 Tip: Try asking conceptual or programming-related topics for best results!")

