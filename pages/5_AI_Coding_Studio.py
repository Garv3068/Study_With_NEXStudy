import streamlit as st
import google.generativeai as genai
import re

# ----------------------------------
# API KEY (Gemini Only)
# ----------------------------------
# ---------------------------
# GEMINI INITIALIZATION
# ---------------------------
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

# ----------------------------------
# LANGUAGE OPTIONS
# ----------------------------------

SUPPORTED_LANGUAGES = {
    "Python": "python",
    "HTML": "html",
    "CSS": "css",
    "C": "c",
    "C++": "cpp",
    "Java": "java"
}

# ----------------------------------
# UI HEADER
# ----------------------------------

st.title("🧠 NexStudy – AI Coding Studio")
st.caption("Multi-language AI Code Generator & Rule-based Debugger")

# ----------------------------------
# CREATE TABS
# ----------------------------------

tab1, tab2 = st.tabs(["⚙️ Code Generator ", "🛠️ AI Debugger (Rule-Based)"])

# =====================================================
# TAB 1 — CODE GENERATOR (Gemini)
# =====================================================

with tab1:
    st.subheader("⚙️ AI Code Generator ")

    lang_choice = st.selectbox("Select Language", list(SUPPORTED_LANGUAGES.keys()))
    syntax = SUPPORTED_LANGUAGES[lang_choice]

    prompt = st.text_area(
        "Enter your prompt:",
        height=200,
        placeholder="Describe the code you want..."
    )

    if st.button("Generate Code"):
        if not prompt.strip():
            st.warning("Please enter a prompt.")
            st.stop()

        try:
            with st.spinner(f"Generating {lang_choice} code..."):
                response = gemini_model.generate_content(
                    f"""
                    Generate clean, well-structured {lang_choice} code.
                    Only output valid code.
                    User prompt:
                    {prompt}
                    """
                )

            st.subheader(f"✅ Generated {lang_choice} Code")
            st.code(response.text, language=syntax)

        except Exception as e:
            st.error(f"Gemini Error: {str(e)}")


# =====================================================
# TAB 2 — RULE-BASED DEBUGGER
# =====================================================

with tab2:
    st.subheader("🛠️ Smart Debugger")

    debug_lang = st.selectbox("Select Language to Debug", ["Python", "HTML", "CSS", "JavaScript"])
    buggy_code = st.text_area("Paste your code:", height=250)

    if st.button("Debug Code"):
        if not buggy_code.strip():
            st.error("Please paste some code.")
            st.stop()

        issues = []
        explanation = []
        fixed_code = buggy_code  # initial copy

        # ----------------------------
        # PYTHON DEBUGGER
        # ----------------------------
        if debug_lang == "Python":
            try:
                compile(buggy_code, "<string>", "exec")
                st.success("✅ No syntax errors found.")

            except SyntaxError as e:
                st.error(f"❌ Syntax Error: {e.msg} at line {e.lineno}")

                if "EOL" in str(e) or "unterminated string" in str(e):
                    issues.append("Unclosed string literal.")
                    explanation.append("A missing quote was added.")
                    fixed_code = buggy_code + '"'

                elif "invalid syntax" in str(e):
                    issues.append("General syntax issue.")
                    explanation.append("Possibly missing parentheses.")
                    fixed_code = buggy_code.replace("print ", "print(") + ")"

        # ----------------------------
        # HTML DEBUGGER
        # ----------------------------
        elif debug_lang == "HTML":
            if "<html" not in buggy_code.lower():
                issues.append("Missing <html> tag.")
                fixed_code = "<html>\n" + fixed_code + "\n</html>"
                explanation.append("Wrapped inside <html>.")

            if "<body" not in buggy_code.lower():
                issues.append("Missing <body> tag.")
                fixed_code = fixed_code.replace("</html>", "<body>\n</body>\n</html>")
                explanation.append("Added <body>.")

        # ----------------------------
        # CSS DEBUGGER
        # ----------------------------
        elif debug_lang == "CSS":
            if not buggy_code.strip().endswith("}"):
                issues.append("Missing closing brace.")
                fixed_code += "\n}"
                explanation.append("Added missing '}'.")

            if ":" not in buggy_code:
                issues.append("No property:value pairs.")
                explanation.append("CSS must follow format 'property: value;'.")

        # ----------------------------
        # JAVASCRIPT DEBUGGER
        # ----------------------------
        elif debug_lang == "JavaScript":
            if "console.log" not in buggy_code:
                issues.append("Missing console.log() statement.")
                explanation.append("Suggested adding console.log().")

            if not buggy_code.strip().endswith(";"):
                issues.append("Missing semicolon.")
                fixed_code = buggy_code.strip() + ";"
                explanation.append("Added semicolon.")

        # ----------------------------
        # SHOW RESULTS
        # ----------------------------

        if issues:
            st.warning("⚠️ Issues Found:")
            for i in issues:
                st.write("•", i)

        if explanation:
            st.subheader("💡 Explanation")
            for ex in explanation:
                st.write("–", ex)

        if fixed_code != buggy_code:
            st.subheader("✅ Suggested Corrected Code")
            st.code(fixed_code, language=SUPPORTED_LANGUAGES.get(debug_lang.lower(), "text"))

        if not issues:
            st.success("🎉 No major issues detected!")

