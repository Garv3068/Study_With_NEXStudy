import streamlit as st

# ---------------- GOOGLE VERIFICATION CODE ----------------
# Replace "YOUR_LONG_CODE_HERE" with the code from Google
google_verification_code = """
<meta name="google-site-verification" content="YOUR_LONG_CODE_HERE" />
"""
st.markdown(google-site-verification=XYcIyBJuua3DGj9HYfU0bpUVu9cGV1IczmvqjVuQcMA, unsafe_allow_html=True)
# ----------------------------------------------------------
st.set_page_config(
    page_title="NexStudy - Your AI Study Helper",
    page_icon="🧠",
    layout="wide"
)


# --- Main Home Content ---
st.title("🎓 Welcome to NexStudy – Your AI Study Helper")
st.markdown("""
NexStudy empowers students with AI-driven learning tools.  
🚀 Learn smarter, not harder.
""")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.header("🧾 Summarize Notes")
    st.write("Upload PDFs or text to generate AI-powered summaries.")
    st.page_link("pages/1_Summarizer.py", label="Go to Summarizer", icon="➡️")

with col2:
    st.header("🧠 Generate Quizzes")
    st.write("Turn your notes into interactive quizzes and test yourself.")
    st.page_link("pages/2_Quiz_Generator.py", label="Go to Quiz Generator", icon="➡️")

with col3:
    st.header("💡 Smart Study Tips")
    st.write("Boost productivity with AI-generated study hacks.")
    st.page_link("pages/Smart_Tips.py", label="Get Tips", icon="➡️")

st.markdown("---")

col4, col5 = st.columns(2)
with col4:
    st.header("🗂️ Flashcards")
    st.write("Quickly review key points using auto-generated flashcards.")
    st.page_link("pages/Flashcards.py", label="Open Flashcards", icon="➡️")

with col5:
    st.header("📊 Dashboard")
    st.write("Track your quiz performance and progress over time.")
    st.page_link("pages/3_Dashboard.py", label="Open Dashboard", icon="➡️")

st.markdown("---")
st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")
