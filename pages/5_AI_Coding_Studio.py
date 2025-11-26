import streamlit as st
import re
import random
import google.generativeai as genai
import os

st.set_page_config(page_title="AI Coding Studio", page_icon="💻", layout="wide")

# ------------------------------------------------------------
# ✅ GEMINI INITIALIZATION (ROBUST VERSION)
# ------------------------------------------------------------
@st.cache_resource
def init_gemini(api_key_input):
    # 1. Try getting key from the function argument (User Input)
    key = api_key_input

    # 2. If no user input, try getting from secrets safely
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass # Secrets file might not exist, just ignore

    # 3. If still no key, return None (don't crash)
    if not key:
        return None

    try:
        genai.configure(api_key=key)
        return genai.GenerativeModel("gemini-2.0-flash") 
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ------------------------------------------------------------
# SIDEBAR FOR API KEY
# ------------------------------------------------------------
with st.sidebar:
    # st.header("🔑 API Configuration")
    # Check if key exists in secrets to decide if we show the warning
    has_secret_key = False
    try:
        if st.secrets.get("GEMINI_API_KEY"):
            has_secret_key = True
    except:
        pass

    user_api_key = ""
    if not has_secret_key:
        st.warning("⚠️ No API Key found in secrets.")
        user_api_key = st.text_input("Enter Gemini API Key:", type="password", placeholder="Paste key here...")
        st.markdown("[Get a free key here](https://aistudio.google.com/app/apikey)")
    # else:
        # st.success("✅ API Key loaded from secrets")

# Initialize Model
gemini_model = init_gemini(user_api_key)

# ------------------------------------------------------------
# PAGE CONTENT
# ------------------------------------------------------------
st.title("💻 AI Coding Studio")
st.caption("Generate, debug, and learn to code — all in one place!")

if not gemini_model:
    st.error("❌ Please enter a valid Gemini API Key in the sidebar to continue.")
    st.stop()

tab1, tab2 = st.tabs(["⚙️ Code Generator", "🧠 Smart Debugger"])

# ------------------------------------------------------------
# TAB 1 — CODE GENERATOR
# ------------------------------------------------------------
with tab1:
    st.subheader("⚙️ Code Generator")

    col1, col2 = st.columns([1, 3])
    with col1:
        lang = st.selectbox("Select Language", ["Python", "HTML", "CSS", "JavaScript", "SQL", "C++"], key="gen_lang")
    with col2:
        prompt = st.text_area("Describe what you want to build:", height=100, placeholder="E.g., A snake game in Python...")

    if st.button("🚀 Generate Code", type="primary"):
        if not prompt.strip():
            st.error("Please enter a prompt first.")
            st.stop()

        with st.spinner("✨ Writing code..."):
            try:
                ai_prompt = f"""
                You are an expert {lang} developer.
                Generate fully working, clean and optimized code for: "{prompt}"
                
                RULES:
                1. Output ONLY the code.
                2. No markdown code fences (```) at the start or end.
                3. No explanation text.
                4. Include comments within the code to explain logic.
                """

                response = gemini_model.generate_content(ai_prompt)
                
                # Clean up potential markdown fences
                code_result = response.text.strip()
                if code_result.startswith("```"):
                    lines = code_result.split("\n")
                    if len(lines) > 2:
                        code_result = "\n".join(lines[1:-1])

                st.success(f"✅ Generated {lang} code:")
                st.code(code_result, language=lang.lower())

            except Exception as e:
                st.error(f"Gemini Code Generation Error: {e}")

# ------------------------------------------------------------
# TAB 2 — DEBUGGER
# ------------------------------------------------------------
with tab2:
    st.subheader("🛠️ AI Debugger")

    debug_lang = st.selectbox(
        "Select Language to Debug",
        ["Python", "HTML", "CSS", "JavaScript", "C", "C++", "Java"],
        key="debug_lang"
    )

    buggy_code = st.text_area(
        "Paste your buggy code:",
        height=300,
        placeholder="Paste your code here…"
    )

    if st.button("🐞 Debug Code", type="primary"):
        if not buggy_code.strip():
            st.error("❌ Please paste some code to debug.")
            st.stop()

        with st.spinner("🔍 Analyzing and fixing..."):
            try:
                prompt = f"""
                You are an expert {debug_lang} programmer and debugger.

                TASK:
                1. Detect all syntax and logical errors in the code below.
                2. Explain every issue in simple terms.
                3. Provide a fully corrected version of the code.

                FORMAT STRICTLY:
                ### Issues Found:
                - [Issue 1]
                - [Issue 2]

                ### Explanation:
                [Explanation text]

                ### Fixed Code:
                ```{debug_lang.lower()}
                [Corrected code here]
                ```

                --- CODE TO DEBUG ---
                {buggy_code}
                """

                response = gemini_model.generate_content(prompt)
                
                st.markdown("### 🔍 Debugging Report")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Gemini Debugger Error: {str(e)}")
