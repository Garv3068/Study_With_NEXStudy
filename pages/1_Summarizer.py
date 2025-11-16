import streamlit as st
import google.generativeai as genai

@st.cache_resource
def init_gemini():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=key)

        try:
            return genai.GenerativeModel("gemini-2.5-flash")
        except:
            st.warning("⚠️ Gemini 2.5 Flash not available. Switching to Gemini 2.0 Flash.")
            return genai.GenerativeModel("gemini-2.0-flash")

    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None


gemini_model = init_gemini()

# --- Page title ---
st.title("📄 Smart Text Summarizer (NexStudy)")
st.write(
    "Upload or paste your study material below and get a clear, concise summary with key points for quick revision."
)

# --- Input area ---
text_input = st.text_area("✍️ Enter or paste your text here:", height=200)


# --- Summarization function ---
def generate_summary(text):
    try:
        response = model.generate_content(f"Summarize this text clearly and simply:\n\n{text}")
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None


# --- Keyword extraction function ---
def extract_keywords(summary):
    try:
        response = model.generate_content(
            f"Extract 5–10 important keywords from this summary, comma-separated:\n\n{summary}"
        )
        keywords = response.text.strip()
        return keywords
    except Exception as e:
        st.error(f"Error extracting keywords: {e}")
        return None


# --- Main Logic ---
if st.button("✨ Generate Summary"):
    if text_input.strip():
        with st.spinner("Analyzing and summarizing..."):
            summary = generate_summary(text_input)

            if summary:
                st.subheader("🧠 Summary")
                st.write(summary)

                # --- Download option ---
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name="summary.txt",
                    mime="text/plain",
                )

                # --- Extract Keywords ---
                with st.spinner("Finding key concepts..."):
                    keywords = extract_keywords(summary)
                    if keywords:
                        st.subheader("🔑 Key Concepts / Keywords")
                        st.success(keywords)
    else:
        st.warning("Please enter some text before summarizing.")
