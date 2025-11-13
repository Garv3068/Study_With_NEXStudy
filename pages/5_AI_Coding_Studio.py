import streamlit as st
import re
import random

st.set_page_config(page_title="AI Coding Studio", page_icon="💻")

st.title("💻 AI Coding Studio")
st.caption("Generate, debug, and learn to code — all in one place!")

# --------------------------------------------------------------------
# Tabs for two main features
# --------------------------------------------------------------------
tab1, tab2 = st.tabs(["⚙️ Code Generator", "🧠 Smart Debugger"])

# --------------------------------------------------------------------
# TAB 1 — AI CODE GENERATOR
# --------------------------------------------------------------------
with tab1:
    st.subheader("⚙️ Code Generator")

    lang = st.selectbox("Select Language", ["Python", "HTML", "CSS", "JavaScript"])
    prompt = st.text_area("Describe what you want to build:")

    if st.button("🚀 Generate Code"):
        if not prompt.strip():
            st.error("Please enter a prompt first.")
        else:
            st.write("🧠 Generating code...")

            # --- Simple offline rule-based generation (Phase 1) ---
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

# --------------------------------------------------------------------
# TAB 2 — AI DEBUGGER (with Auto Fix + Explanation)
# --------------------------------------------------------------------
with tab2:
    st.subheader("🧠 Smart Debugger — Find and Fix Your Code")

    lang = st.selectbox("Select Language to Debug", ["Python", "HTML", "CSS", "JavaScript"])
    buggy_code = st.text_area("Paste your code here to debug:")

    if st.button("🔍 Debug Code"):
        if not buggy_code.strip():
            st.error("Please paste some code first.")
        else:
            st.write("🔍 Analyzing your code...")
            fixed_code = buggy_code
            issues = []
            explanation = []

            # ----------------------------
            # 🐍 PYTHON DEBUGGER
            # ----------------------------
            if lang == "Python":
                try:
                    compile(buggy_code, "<string>", "exec")
                    st.success("✅ No syntax errors found.")
                    if "def" not in buggy_code:
                        issues.append("No function defined.")
                        explanation.append("Adding functions can make your code modular and reusable.")
                    if "print(" not in buggy_code:
                        issues.append("No print statement found.")
                        explanation.append("Add print() to display output.")
                except SyntaxError as e:
                    st.error(f"❌ Syntax Error: {e.msg} at line {e.lineno}")

                    if "unterminated string" in str(e) or "EOL" in str(e):
                        fixed_code = re.sub(r'print\(([^)]*)$', r'print(\1")', buggy_code)
                        issues.append("Unclosed string literal detected.")
                        explanation.append("A missing quote was added to close your string.")
                    elif "invalid syntax" in str(e):
                        fixed_code = buggy_code.replace("print ", "print(").replace("\n", ")\n")
                        issues.append("Likely missing parentheses.")
                        explanation.append("Added parentheses to fix print syntax.")
                    else:
                        explanation.append("Syntax issue found; review your code manually.")

                except Exception as e:
                    st.error(f"⚠️ Runtime Error: {str(e)}")
                    issues.append("Runtime error.")
                    explanation.append("This could be due to undefined variables or imports.")

                if issues:
                    st.warning("⚠️ Issues Found:")
                    for i in issues:
                        st.write("•", i)

                    st.subheader("💡 Explanation")
                    for e in explanation:
                        st.write("-", e)

                if fixed_code != buggy_code:
                    st.subheader("✅ Suggested Fixed Code")
                    st.code(fixed_code, language="python")

            # ----------------------------
            # 🌐 HTML DEBUGGER
            # ----------------------------
            elif lang == "HTML":
                if "<html" not in buggy_code.lower():
                    issues.append("Missing <html> tag.")
                    fixed_code = "<html>\n" + buggy_code + "\n</html>"
                    explanation.append("Added missing <html> wrapper.")
                if "<body" not in buggy_code.lower():
                    issues.append("Missing <body> tag.")
                    fixed_code = fixed_code.replace("</html>", "<body>\n</body>\n</html>")
                    explanation.append("Added missing <body> section.")
                if "<!DOCTYPE" not in buggy_code.lower():
                    fixed_code = "<!DOCTYPE html>\n" + fixed_code
                    issues.append("Added missing <!DOCTYPE html> declaration.")
                    explanation.append("Added doctype to define HTML version.")

                if issues:
                    st.warning("⚠️ Issues Found:")
                    for i in issues:
                        st.write("•", i)
                    st.subheader("✅ Corrected HTML")
                    st.code(fixed_code, language="html")

            # ----------------------------
            # 🎨 CSS DEBUGGER
            # ----------------------------
            elif lang == "CSS":
                if not buggy_code.strip().endswith("}"):
                    fixed_code = buggy_code + "\n}"
                    issues.append("Added missing closing brace '}'.")
                    explanation.append("Every CSS block must end with '}'.")
                if ":" not in buggy_code:
                    issues.append("No property:value pair found.")
                    explanation.append("Use format like `color: red;`.")
                if issues:
                    st.warning("⚠️ Issues Found:")
                    for i in issues:
                        st.write("•", i)
                    st.subheader("✅ Corrected CSS")
                    st.code(fixed_code, language="css")

            # ----------------------------
            # ⚙️ JAVASCRIPT DEBUGGER
            # ----------------------------
            elif lang == "JavaScript":
                if "function" not in buggy_code and "=>" not in buggy_code:
                    issues.append("No function found.")
                    explanation.append("Consider defining a function.")
                if "console.log" not in buggy_code:
                    issues.append("Add console.log() for output.")
                    explanation.append("Use console.log() to print results in JS.")
                if not buggy_code.strip().endswith(";"):
                    fixed_code = buggy_code.strip() + ";"
                    issues.append("Added missing semicolon.")
                    explanation.append("Statements should end with semicolons.")

                if issues:
                    st.warning("⚠️ Issues Found:")
                    for i in issues:
                        st.write("•", i)
                    st.subheader("✅ Corrected JavaScript")
                    st.code(fixed_code, language="javascript")
                    
