import streamlit as st
import os

# ---------------- Page Config (SEO Optimized) ----------------
st.set_page_config(
    page_title="NexStudy | Free AI Tutor & Exam Solver",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Custom CSS (Optional: Clean up UI) ----------------
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------- Logo & Hero Section ----------------
# Ensure 'logo.jpg' is in the same directory
logo_path = "assets/image.png"

col_logo, col_title = st.columns([2, 4])

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.write("🧠") # Fallback icon if logo is missing

with col_title:
    st.title("NexStudy")
    st.subheader("The Unlimited, Free AI Academic Companion")
    st.markdown(
        """
        **Tired of running out of credits on other apps?** 
        NexStudy is open, private, and unlimited..
        
        🚀 **Solver** · 📅 **Planner** · 🎧 **Audio Notes** · 💻 **Coding**
        """
    )

st.divider()

# ---------------- Feature Grid ----------------
st.markdown("### 🚀 What can you do here?")

col1, col2 = st.columns(2)

# --- Left Column Features ---
with col1:
    st.markdown(
        """
        #### 🤖 **NexStudy Chat**
        The core of your learning.
        - **Doubt Solver:** Upload homework images/PDFs.
        - **Topic Explainer:** Get deep dives into complex concepts.
        - **Tutor Mode:** Ask follow-up questions freely (Context Aware).
        """
    )
    st.info("👈 **Go to: NexStudy** in the sidebar")

    st.markdown(
        """
        #### 📅 **Study Planner**
        Never miss a deadline again.
        - Upload your syllabus PDF.
        - Set your exam date.
        - Get a **day-by-day** optimized schedule.
        """
    )
    st.info("👈 **Go to: Study Planner** in the sidebar")
    
    st.markdown(
        """
        #### 💻 **AI Coding Studio**
        Master programming effortlessly.
        - Generate Python, HTML, JS code.
        - **AI Debugger:** Find and fix errors instantly.
        """
    )
    st.info("👈 **Go to: AI Coding Studio** in the sidebar")

# --- Right Column Features ---
with col2:
    st.markdown(
        """
        #### 📝 **Past Paper Solver**
        The ultimate exam hack.
        - Upload previous year question papers.
        - Get full **Answer Keys** and step-by-step solutions.
        """
    )
    st.info("👈 **Go to: Paper Solver** in the sidebar")

    st.markdown(
        """
        #### 🎧 **Audio Notes Studio**
        Study while you walk.
        - **Podcaster:** Turn PDF notes into audio summaries.
        - **Transcriber:** Turn lecture recordings into text notes.
        """
    )
    st.info("👈 **Go to: Audio Notes** in the sidebar")

st.divider()

# ---------------- Footer / Getting Started ----------------
# st.markdown("### ⚡ Getting Started")
# st.markdown(
    # """
    # 1. **Get a Gemini API Key:** It's free! [Get it here](https://aistudio.google.com/app/apikey).
    # 2. **Enter it in the Sidebar:** Paste it once, and it works for all tools.
    # 3. **Select a Tool:** Choose what you need from the menu on the left.
    # """
# )

# st.warning("🔒 Your API Key is safe. It is not stored anywhere and is only used for your session.")
st.markdown("---")
st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")
