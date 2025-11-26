import streamlit as st
import os
import base64

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

# ---------------- Helper: Load Image as Base64 ----------------
def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ---------------- Logo & Hero Section ----------------
# Check for path preference: assets/image.png -> logo.png -> logo.jpg
if os.path.exists("assets/image.png"):
    logo_path = "assets/image.png"
elif os.path.exists("logo.png"):
    logo_path = "logo.png"
elif os.path.exists("logo.jpg"):
    logo_path = "logo.jpg"
else:
    logo_path = None

col_logo, col_title = st.columns([1.5, 4.5])

with col_logo:
    if logo_path and os.path.exists(logo_path):
        # Convert image to base64 so it works in the HTML img tag
        img_b64 = get_img_as_base64(logo_path)
        
        st.markdown(
            f"""
            <style>
                .circular-logo {{
                    border-radius: 50%;
                    width: 200px;
                    height: 200px;
                    object-fit: cover;
                    display: block;
                    margin-left: auto;
                    margin-right: auto;
                    border: 3px solid #f0f2f6; /* Optional border for clean look */
                }}
            </style>
            <img src="data:image/png;base64,{img_b64}" class="circular-logo">
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<h1 style='text-align: center;'>🧠</h1>", unsafe_allow_html=True)

with col_title:
    st.title("NexStudy")
    st.write("### The Unlimited, Free AI Academic Companion")
    st.markdown(
        """
        **Tired of running out of credits on other apps?** NexStudy is open, private, and unlimited. Bring your own free API Key and study without limits.

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

# ---------------- Footer ----------------
st.markdown("---")
st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")

# st.warning("🔒 Your API Key is safe. It is not stored anywhere and is only used for your session.")
st.markdown("---")
st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")
