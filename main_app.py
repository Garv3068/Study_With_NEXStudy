import streamlit as st
import os
import base64

# -------------------------------------------------
# PAGE CONFIG (SEO)
# -------------------------------------------------
st.set_page_config(
    page_title="NexStudy | Free AI Tutor & Exam Solver",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# GOOGLE ANALYTICS + FIREBASE AUTH JS INJECTION
# -------------------------------------------------

firebase_auth_js = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-L02K682TRE"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-L02K682TRE');
</script>

<!-- Firebase -->
<script type="module">
  import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
  import { getAuth, onAuthStateChanged, signInWithPopup, GoogleAuthProvider, signOut }
    from "https://www.gstatic.com/firebasejs/12.6.0/firebase-auth.js";

  const firebaseConfig = {
    apiKey: "AIzaSyCv-H1-KfgnL0SGPEfAnMiSq34bhAuaXYM",
    authDomain: "studywith-nexstudy.firebaseapp.com",
    projectId: "studywith-nexstudy",
    storageBucket: "studywith-nexstudy.firebasestorage.app",
    messagingSenderId: "72623577486",
    appId: "1:72623577486:web:1e8796027d3e1cfd0eecdf",
    measurementId: "G-RBK405Y2PB"
  };

  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const provider = new GoogleAuthProvider();

  window.nexstudyLogin = function() {
      signInWithPopup(auth, provider)
        .then((result) => {
            localStorage.setItem("nexstudy_user", JSON.stringify(result.user));
            location.reload();
"""       
# ---------------- Footer ----------------
# st.markdown("---")
# st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")

# st.warning("🔒 Your API Key is safe. It is not stored anywhere and is only used for your session.")
# st.markdown("---")
# st.caption("✨ Built with ❤️ by Garv | Powered by AI | NexStudy 2025")
