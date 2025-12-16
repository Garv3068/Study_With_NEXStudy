import streamlit as st
import os
import base64
import datetime
import streamlit.components.v1 as components

# =========================================================
# PAGE CONFIG (SEO OPTIMIZED)
# =========================================================
st.set_page_config(
    page_title="NexStudy | Free AI Tutor & Exam Solver",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# FIREBASE DATABASE LOGIC (SAFE – NO CRASH IF NOT CONFIGURED)
# =========================================================
def log_login_to_db(email: str):
    """Save user email + timestamp to Firestore"""
    if not email:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            key_dict = dict(st.secrets["firebase_key"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        db.collection("users").document(email).set(
            {
                "email": email,
                "last_login": datetime.datetime.utcnow(),
                "platform": "Streamlit App",
            },
            merge=True,
        )

    except Exception:
        # Silent fail so app never breaks
        pass

# =========================================================
# SESSION STATE
# =========================================================
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "is_guest" not in st.session_state:
    st.session_state.is_guest = False

if "auth_dialog_shown" not in st.session_state:
    st.session_state.auth_dialog_shown = False

# =========================================================
# AUTO LOGIN FROM URL (VERCEL → STREAMLIT)
# =========================================================
if not st.session_state.user_email:
    params = st.query_params
    if "user" in params:
        email = params["user"]
        st.session_state.user_email = email
        st.session_state.is_guest = False
        log_login_to_db(email)

# =========================================================
# LOGIN DIALOG
# =========================================================
@st.dialog("Welcome to NexStudy 🧠")
def login_dialog():
    st.session_state.auth_dialog_shown = True
    st.write("Sign in to sync your study plans and notes.")

    email = st.text_input("Enter your email address")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Sign In / Sign Up", type="primary", use_container_width=True):
            if email:
                st.session_state.user_email = email
                st.session_state.is_guest = False
                log_login_to_db(email)
                st.rerun()
            else:
                st.warning("Please enter an email.")

    with col2:
        if st.button("Continue as Guest", use_container_width=True):
            st.session_state.is_guest = True
            st.rerun()

# Trigger dialog
if (
    not st.session_state.user_email
    and not st.session_state.is_guest
    and not st.session_state.auth_dialog_shown
):
    login_dialog()

# =========================================================
# GOOGLE ANALYTICS (GTAG)
# =========================================================
components.html(
    """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-L02K682TRE"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-L02K682TRE');
    </script>
    """,
    height=0,
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# HELPER – IMAGE TO BASE64
# =========================================================
def get_img_as_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# =========================================================
# LOGO DETECTION
# =========================================================
if os.path.exists("assets/image.png"):
    logo_path = "assets/image.png"
elif os.path.exists("logo.png"):
    logo_path = "logo.png"
elif os.path.exists("logo.jpg"):
    logo_path = "logo.jpg"
else:
    logo_path = None

# =========================================================
# HERO SECTION
# =========================================================
col_logo, col_title = st.columns([1.5, 4.5])

with col_logo:
    if logo_path:
        img_b64 = get_img_as_base64(logo_path)
        st.markdown(
            f"""
            <style>
            .logo {{
                border-radius: 50%;
                width: 200px;
                height: 200px;
                object-fit: cover;
                display: block;
                margin: auto;
                border: 3px solid #f0f2f6;
            }}
            </style>
            <img src="data:image/png;base64,{img_b64}" class="logo">
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<h1 style='text-align:center'>🧠</h1>", unsafe_allow_html=True)

with col_title:
    st.title("NexStudy")

    if st.session_state.user_email:
        st.caption(f"👋 Welcome back, {st.session_state.user_email}")
    elif st.session_state.is_guest:
        st.caption("👀 Browsing as Guest")

    st.write("### The Unlimited, Free AI Academic Companion")
    st.markdown(
        """
        **Tired of running out of credits?**  
        NexStudy is open, private, and unlimited.

        🚀 Solver · 📅 Planner · 🎧 Audio Notes · 💻 Coding
        """
    )

st.divider()

# =========================================================
# FEATURES
# =========================================================
st.markdown("### 🚀 What can you do here?")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        #### 🤖 NexStudy Chat
        - Homework doubt solver  
        - Concept explainer  
        - Context-aware tutoring
        """
    )
    st.info("👈 Go to **AI Tutor**")

    st.markdown(
        """
        #### 📅 Study Planner
        - Upload syllabus  
        - Exam-based planning  
        - Daily schedules
        """
    )
    st.info("👈 Go to **Study Planner**")

    st.markdown(
        """
        #### 💻 AI Coding Studio
        - Code generation  
        - Debugging assistant
        """
    )
    st.info("👈 Go to **AI Coding Studio**")

with col2:
    st.markdown(
        """
        #### 📝 Past Paper Solver
        - Upload PYQs  
        - Step-by-step solutions
        """
    )
    st.info("👈 Go to **Paper Solver**")

    st.markdown(
        """
        #### 🎧 Audio Notes Studio
        - PDF → Audio  
        - Lecture → Notes
        """
    )
    st.info("👈 Go to **Audio Notes**")

st.divider()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("🌐 **[Official Website](https://studywith-nexstudy.vercel.app/)**")

    if st.session_state.user_email:
        if st.button("Log Out"):
            st.session_state.user_email = None
            st.session_state.is_guest = False
            st.session_state.auth_dialog_shown = False
            st.rerun()
    else:
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
