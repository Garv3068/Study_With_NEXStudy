import streamlit as st
import os
import base64
import datetime
import streamlit.components.v1 as components
from supabase import create_client, Client

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
# SUPABASE CLIENT
# =========================================================
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# =========================================================
# SESSION STATE
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None          # full auth user object (dict)
if "profile" not in st.session_state:
    st.session_state.profile = None       # row from profiles table
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False
if "auth_dialog_shown" not in st.session_state:
    st.session_state.auth_dialog_shown = False
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # "login" or "signup"

# =========================================================
# HELPER: LOAD PROFILE
# =========================================================
def load_profile(user_id: str):
    try:
        res = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if res.data:
            st.session_state.profile = res.data
    except Exception:
        st.session_state.profile = None

# =========================================================
# AUTO LOGIN FROM URL (OPTIONAL, USING EMAIL QUERY PARAM)
# =========================================================
# NOTE: this is legacy from Vercel; it only sets a "guest identity" now.
params = st.query_params
if not st.session_state.user and not st.session_state.is_guest:
    if "user" in params:
        email = params["user"]
        # treat as guest with known email (no password)
        st.session_state.is_guest = True
        st.session_state.profile = {"username": email.split("@")[0], "email": email}

# =========================================================
# AUTH HELPERS (SUPABASE)
# =========================================================
def signup(email: str, password: str, username: str):
    try:
        # 1) create auth user
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.get("error"):
            return False, res["error"]["message"]

        user = res["user"]
        user_id = user["id"]

        # 2) create profile with username
        prof_res = (
            supabase
            .table("profiles")
            .insert({"id": user_id, "username": username})
            .execute()
        )
        if prof_res.error:
            return False, prof_res.error.message

        # store in session
        st.session_state.user = user
        st.session_state.profile = {"id": user_id, "username": username, "email": email}
        st.session_state.is_guest = False
        return True, None
    except Exception as e:
        return False, str(e)


def login(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.get("error"):
            return None, res["error"]["message"]

        user = res["user"]
        st.session_state.user = user
        st.session_state.is_guest = False

        # load profile
        load_profile(user["id"])
        return user, None
    except Exception as e:
        return None, str(e)

# =========================================================
# LOGIN / SIGNUP DIALOG
# =========================================================
@st.dialog("Welcome to NexStudy 🧠")
def login_dialog():
    st.session_state.auth_dialog_shown = True

    mode = st.session_state.auth_mode

    tabs = st.tabs(["Log In", "Sign Up"])
    if mode == "login":
        login_tab, signup_tab = tabs
    else:
        signup_tab, login_tab = tabs  # just to keep both present

    # --------- LOGIN TAB ----------
    with tabs[0]:
        st.subheader("Log In")
        st.caption("Sign in with your email and password to sync your study data.")
        email_login = st.text_input("Email", key="login_email")
        password_login = st.text_input("Password", type="password", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Log In", type="primary", use_container_width=True, key="login_btn"):
                if email_login and password_login:
                    user, err = login(email_login, password_login)
                    if err:
                        st.error(err)
                    else:
                        st.success("Logged in successfully!")
                        st.rerun()
                else:
                    st.warning("Please enter email and password.")

        with col2:
            if st.button("Continue as Guest", use_container_width=True, key="guest_btn"):
                st.session_state.is_guest = True
                st.session_state.user = None
                st.session_state.profile = None
                st.rerun()

    # --------- SIGNUP TAB ----------
    with tabs[1]:
        st.subheader("Sign Up")
        st.caption("Create a free NexStudy account.")
        username_signup = st.text_input("Username", key="signup_username")
        email_signup = st.text_input("Email", key="signup_email")
        password_signup = st.text_input("Password", type="password", key="signup_password")

        if st.button("Create Account", type="primary", use_container_width=True, key="signup_btn"):
            if username_signup and email_signup and password_signup:
                ok, err = signup(email_signup, password_signup, username_signup)
                if ok:
                    st.success("Account created and logged in!")
                    st.rerun()
                else:
                    st.error(err or "Could not sign up.")
            else:
                st.warning("Please fill all fields.")

# Trigger dialog if no user and not guest
if (
    not st.session_state.user
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

    # Greeting
    if st.session_state.user:
        name = st.session_state.profile["username"] if st.session_state.profile else st.session_state.user.get("email", "")
        st.caption(f"👋 Welcome back, {name}")
    elif st.session_state.is_guest:
        # guest label
        guest_name = ""
        if st.session_state.profile and st.session_state.profile.get("username"):
            guest_name = st.session_state.profile["username"]
        st.caption(f"👀 Browsing as Guest {guest_name}")
    else:
        st.caption("🚀 Sign in above to save your progress")

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

    if st.session_state.user:
        if st.button("Log Out"):
            # Supabase sign out (optional – mostly affects tokens)
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.user = None
            st.session_state.profile = None
            st.session_state.is_guest = False
            st.session_state.auth_dialog_shown = False
            st.rerun()
    else:
        if st.button("Log In / Sign Up"):
            st.session_state.is_guest = False
            st.session_state.auth_dialog_shown = False
            st.session_state.auth_mode = "login"
            st.rerun()

# ---------------- Footer ----------------
# st.markdown("---")
# st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")

# st.warning("🔒 Your API Key is safe. It is not stored anywhere and is only used for your session.")
# st.markdown("---")
# st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")
