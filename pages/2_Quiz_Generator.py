import streamlit as st
import random
import nltk
import pdfplumber
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import string
import google.generativeai as genai
import json # ✅ FIX 1: Import the json library for safe JSON parsing

# ---------------- GEMINI INIT ----------------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=key)

        try:
            return genai.GenerativeModel("gemini-2.5-flash-lite")
        except:
            return genai.GenerativeModel("gemini-2.0-flash-lite")

    except Exception as e:
        st.error(f"❌ Gemini initialization failed: {e}")
        return None

gemini_model = init_gemini()


# ---------------- NLTK Resource Setup ----------------
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


# ---------------- Helper Functions ----------------
def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def clean_text(text):
    return text.translate(str.maketrans("", "", string.punctuation))


# ---------------- REPLACED WITH GEMINI ----------------
def generate_questions(text, num_questions=5):
    """Generate MCQ quiz using Gemini instead of rule-based system"""

    if gemini_model is None:
        st.error("❌ Gemini model is not initialized.")
        return []

    prompt = f"""
    You are an expert quiz generator.

    Create {num_questions} high-quality MCQs from the following study material:

    ---CONTENT START---
    {text[:15000]}
    ---CONTENT END---

    Rules:
    - Each question must be clear and based only on the provided text.
    - Each MCQ must have: 1 correct answer + 3 wrong options.
    - Output strictly in JSON list format:
      [
        {{
          "question": "text",
          "options": ["A","B","C","D"],
          "answer": "correct option"
        }},
        ...
      ]
    """

    try:
        response = gemini_model.generate_content(prompt)
        quiz = json.loads(response.text)  # ✅ FIX 2: Replace eval() with json.loads()

        return quiz

    except Exception as e:
        st.error(f"❌ Gemini Quiz Generation Error: {e}")
        return []


# ---------------- Streamlit UI (UNCHANGED) ----------------
st.title("🧠 Smart Quiz Generator")
st.write("Generate quizzes from your notes or PDFs instantly!")

if 'quiz' not in st.session_state:
    st.session_state.quiz = []
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False

def reset_quiz():
    st.session_state.quiz = []
    st.session_state.quiz_generated = False
    st.session_state.quiz_submitted = False

def generate_and_store_quiz(text_data):
    if text_data.strip():
        st.session_state.quiz = generate_questions(text_data)
        st.session_state.quiz_generated = True
        st.session_state.quiz_submitted = False


# ---------------- Input Section ----------------
input_type = st.radio("Choose Input Type:", ("Upload PDF", "Paste Text"), on_change=reset_quiz)
text_data = ""

if input_type == "Upload PDF":
    uploaded_file = st.file_uploader("Upload a PDF (max 10 MB)", type="pdf", on_change=reset_quiz)
    if uploaded_file:
        text_data = extract_text_from_pdf(uploaded_file)
else:
    text_data = st.text_area("Paste your study material here:", key='text_input', on_change=reset_quiz)


# ---------------- Generate Quiz Button ----------------
if st.button("Generate Quiz", disabled=not text_data.strip()):
    generate_and_store_quiz(text_data)


# ---------------- Quiz Section ----------------
if st.session_state.quiz_generated and st.session_state.quiz:
    st.subheader("📋 Quiz Time!")

    user_answers_map = {}
    for i, q in enumerate(st.session_state.quiz):
        st.write(f"**Q{i+1}.** {q['question']}")

        options = q["options"]
        chosen = st.radio(
            f"Choose your answer for Q{i+1}",
            options,
            key=f'answer_{i}'
        )

        user_answers_map[i] = (chosen, q["answer"])


    if st.button("Submit Quiz", disabled=st.session_state.quiz_submitted):
        st.session_state.quiz_submitted = True

    # ---------------- Results Section ----------------
    if st.session_state.quiz_submitted:
        st.subheader("📊 Quiz Analysis")

        correct = 0
        total = len(user_answers_map)

        for i, (chosen, correct_ans) in user_answers_map.items():
            if chosen == correct_ans:
                st.markdown(f"✅ **Q{i+1}: Correct!** — Your answer: *{chosen}*")
                correct += 1
            else:
                st.markdown(
                    f"❌ **Q{i+1}: Incorrect.** Your answer: *{chosen}* | Correct: *{correct_ans}*"
                )

        score = round((correct / total) * 100, 2)
        st.success(f"🎯 Final Score: {correct}/{total} ({score}% accuracy)")


        if score == 100:
            st.balloons()
            st.info("🌟 Perfect! You're a quiz master!")
        elif score >= 70:
            st.info("👏 Great job! Keep going strong!")
        elif score >= 40:
            st.warning("💪 Good effort! Review and try again!")
        else:
            st.error("📚 Practice more — you'll get better!")
