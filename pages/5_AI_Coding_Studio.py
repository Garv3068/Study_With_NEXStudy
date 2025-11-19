import streamlit as st
import re
import random
import google.generativeai as genai   # ✅ Added for Gemini

st.set_page_config(page_title="AI Coding Studio", page_icon="💻")

# ------------------------------------------------------------
# ✅ GEMINI INITIALIZATION ADDED (Required for Debugger)
# ------------------------------------------------------------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=key)

        try:
            return genai.GenerativeModel("gemini-2.5-flash")
        except:
            st.warning("⚠️ Gemini 2.5 Flash not available. Using Gemini 2.0 Flash.")
            return genai.GenerativeModel("gemini-2.0-flash")

    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

gemini_model = init_gemini()  # ✅ Now available everywhere

# ------------------------------------------------------------
# PAGE TITLE + TABS
# ------------------------------------------------------------
st.title("💻 AI Coding Studio")
st.caption("Generate, debug, and learn to code — all in one place!")

tab1, tab2 = st.tabs(["⚙️ Code Generator", "🧠 Smart Debugger"])

# ------------------------------------------------------------
# TAB 1 — RULE-BASED CODE GENERATOR (unchanged)
# ------------------------------------------------------------
with tab1:
    st.subheader("⚙️ Code Generator")

    lang = st.selectbox("Select Language", ["Python", "HTML", "CSS", "JavaScript"])
    prompt = st.text_area("Describe what you want to build:")

    if st.button("🚀 Generate Code"):
        if not prompt.strip():
            st.error("Please enter a prompt first.")
        else:
            st.write("🧠 Generating code...")

            code = ""
            if lang == "Python":
                if "calculator" in prompt.lower():
                    code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b if b != 0 else "Cannot divide by zero"

print("Calculator Example:")
print(add(10, 5))
"""
                elif "hello" in prompt.lower():
                    code = 'print("Hello, World!")'
                else:
                    code = f'# Basic Python Template\nprint("Code for: {prompt}")'

            elif lang == "HTML":
                code = f"""
<!DOCTYPE html>
<html>
<head>
<title>{prompt.title()}</title>
</head>
<body>
<h1>{prompt.title()}</h1>
<p>This is a simple webpage created by AI.</p>
</body>
</html>
"""

            elif lang == "CSS":
                code = """
body {
    background-color: black;
    color: white;
    font-family: Arial;
}
"""

            elif lang == "JavaScript":
                code = f"""
// Auto-generated JS code
function greet() {{
  console.log("Hello from NexStudy AI — {prompt}!");
}}
greet();
"""

            st.success(f"✅ Generated {lang} code below:")
            st.code(code, language=lang.lower())

# ------------------------------------------------------------
# TAB 2 — GEMINI-POWERED DEBUGGER
# ------------------------------------------------------------
with tab2:
    st.subheader("🛠️ AI Debugger")

    debug_lang = st.selectbox(
        "Select Language to Debug",
        ["Python", "HTML", "CSS", "JavaScript", "C", "C++", "Java"]
    )

    buggy_code = st.text_area(
        "Paste your buggy code:",
        height=250,
        placeholder="Paste your code here…"
    )

    if st.button("Debug Code"):

        if not buggy_code.strip():
            st.error("❌ Please paste some code to debug.")
            st.stop()

        if gemini_model is None:
            st.error("Gemini model not initialized.")
            st.stop()

        with st.spinner("🔍Debugging Code......."):
            try:
                prompt = f"""
                You are an expert {debug_lang} programmer and debugger.

                TASK:
                - Detect all syntax and logical errors.
                - Explain every issue in simple terms.
                - Provide a fully corrected version of the code.
                - Provide best practices.

                FORMAT STRICTLY:
                ### Issues Found:
                - issue 1
                - issue 2

                ### Explanation:
                explanation text...

                ### Fixed Code:
                ```{debug_lang.lower()}
                corrected code here
                ```

                ### Best Practices:
                - tip 1
                - tip 2

                --- CODE BEGIN ---
                {buggy_code}
                --- CODE END ---
                """

                response = gemini_model.generate_content(prompt)

                st.subheader("🔍 Debugging Report")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Gemini Debugger Error: {str(e)}")
