import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# ---------------------------
# API KEY CONFIGURATION
# ---------------------------

# Gemini API Key (for Code Generation)
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# OpenAI API Key (for Code Debugger)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# GEMINI MODEL (Code Generation)
# ---------------------------

gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------------------
# STREAMLIT UI
# ---------------------------

st.title("🧠 NexStudy – AI Coding Studio")
st.caption("Generate & Debug Code using Gemini + OpenAI")

option = st.selectbox(
    "Choose your action:",
    ["Generate Code (Gemini)", "Debug Code (OpenAI)"]
)

code_input = st.text_area("Enter your prompt/code here:", height=250)

if st.button("Run"):
    if not code_input.strip():
        st.warning("Please enter some text or code.")
        st.stop()

    # -------------------------------------------------
    # OPTION 1: CODE GENERATION USING GEMINI
    # -------------------------------------------------
    if option == "Generate Code (Gemini)":
        try:
            with st.spinner("Generating code using Gemini…"):
                response = gemini_model.generate_content(
                    f"Write clean, functioning, optimized code.\nUser request:\n{code_input}"
                )
            
            generated_code = response.text
            st.subheader("✅ Generated Code (Gemini)")
            st.code(generated_code, language="python")

        except Exception as e:
            st.error(f"Gemini Error: {str(e)}")

    # -------------------------------------------------
    # OPTION 2: CODE DEBUGGING USING OPENAI
    # -------------------------------------------------
    else:
        try:
            with st.spinner("Debugging code using OpenAI…"):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": f"Fix bugs and provide corrected code:\n{code_input}"}
                    ]
                )
            
            debugged_code = response.choices[0].message.content
            st.subheader("🛠️ Debugged Code (OpenAI)")
            st.code(debugged_code, language="python")

        except Exception as e:
            st.error(f"OpenAI Debugger Error: {str(e)}")
