import streamlit as st
import os
import base64
import streamlit.components.v1 as components  # Import components to inject JS

# ---------------- Page Config (SEO Optimized) ----------------
st.set_page_config(
    page_title="NexStudy | Free AI Tutor & Exam Solver",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- AUTHENTICATION LOGIC ----------------
# 1. Initialize Session State
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False
if "auth_dialog_shown" not in st.session_state:
    st.session_state.auth_dialog_shown = False

# 2. Check URL Parameters (Auto-login from Vercel landing page)
if not st.session_state.user_email:
    params = st.query_params
    if "user" in params:
        st.session_state.user_email = params["user"]
        st.session_state.is_guest = False

# 3. Define the Login Dialog
@st.dialog("Welcome to NexStudy 🧠")
def login_dialog():
    # Mark as shown immediately. If user closes with 'X', 
    # this flag prevents it from reappearing (acting as Guest).
    st.session_state.auth_dialog_shown = True
    
    st.write("Sign in to sync your study plans and audio notes.")
    
    email_input = st.text_input("Enter your email address")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign In / Sign Up", type="primary", use_container_width=True):
            if email_input:
                st.session_state.user_email = email_input
                st.session_state.is_guest = False
                st.rerun()
            else:
                st.warning("Please enter an email.")
    
    with col2:
        if st.button("Continue as Guest", use_container_width=True):
            st.session_state.is_guest = True
            st.rerun()

# 4. Trigger Dialog if not logged in, not guest, and hasn't seen dialog yet
if not st.session_state.user_email and not st.session_state.is_guest and not st.session_state.auth_dialog_shown:
    login_dialog()

# ---------------- GOOGLE ANALYTICS INJECTION ----------------
# This injects the Google Analytics code into the Streamlit app
ga_js = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-L02K682TRE"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-L02K682TRE');
</script>
"""
# Render the script invisibly (height=0)
components.html(ga_js, height=0)

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
    
    # Optional: Display User Status in Title Area
    if st.session_state.user_email:
        st.caption(f"👋 Welcome back, {st.session_state.user_email}")
    elif st.session_state.is_guest:
        st.caption("👀 Browsing as Guest")

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
    st.info("👈 **Go to: AI Tutor** in the sidebar")

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

# ---------------- Sidebar / Footer ----------------
with st.sidebar:
    st.markdown("---")
    st.markdown("🌐 **[Visit Official Website](https://studywith-nexstudy.vercel.app/)**")
    
    # Login / Logout Button Logic
    if st.session_state.user_email:
        if st.button("Log Out"):
            st.session_state.user_email = None
            st.session_state.is_guest = False
            st.rerun()
    else:
        # If guest or not logged in, show login button
        # This button resets the 'auth_dialog_shown' flag so the popup appears again
        if st.button("Log In / Sign Up"):
            st.session_state.is_guest = False
            st.session_state.auth_dialog_shown = False
            st.rerun()
# ---------------- Footer ----------------
# st.markdown("---")
# st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")

# st.warning("🔒 Your API Key is safe. It is not stored anywhere and is only used for your session.")
# st.markdown("---")
# st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")
