import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# ---------------- GEMINI API SETUP ----------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ---------------- PDF EXTRACTION ----------------
def extract_text_from_pdf(uploaded_file):
    """Extract text safely from uploaded PDF"""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


# ---------------- GEMINI QUIZ GENERATION ----------------
def generate_questions_ai(text, num_questions=5):
    """Generate MCQ questions using Gemini"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
You are an expert MCQ Quiz Generator.
Generate exactly {num_questions} multiple-choice questions from the text below.

TEXT:
{text}

INSTRUCTIONS:
- Output MUST be valid JSON only.
- NO markdown.
- NO commentary.
- JSON must have a top-level key "questions".
- Each question must include:
    "question": string
    "options": list of 4 strings
    "answer": string (must be exactly one of the options)

RETURN ONLY THIS FORMAT:
{{
  "questions": [
    {{
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answer": "A"
    }}
  ]
}}
"""

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Clean markdown formatting if present
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)
        return data["questions"]

    except Exception as e:
        st.error(f"❌ Gemini Quiz Generation Error: {e}")
        return []


# ---------------- STREAMLIT UI ----------------
st.title("🧠 Smart Quiz Generator")
st.write("Generate quizzes from your notes or PDFs instantly!")

# --- Session State Initialization ---
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
        st.session_state.quiz = generate_questions_ai(text_data)
        st.session_state.quiz_generated = True
        st.session_state.quiz_submitted = False

        for i, q in enumerate(st.session_state.quiz):
            st.session_state[f'answer_{i}'] = q["options"][0]


# ---------------- Input Section ----------------
input_type = st.radio("Choose Input Type:", ("Upload PDF", "Paste Text"), on_change=reset_quiz)
text_data = ""

if input_type == "Upload PDF":
    uploaded_file = st.file_uploader("Upload a PDF (max 10 MB)", type="pdf", on_change=reset_quiz)
    if uploaded_file:
        text_data = extract_text_from_pdf(uploaded_file)
else:
    text_data = st.text_area("Paste your study material here:", key='text_input', on_change=reset_quiz)


# ---------------- Generate Button ----------------
if st.button("Generate Quiz", disabled=not text_data.strip()):
    generate_and_store_quiz(text_data)


# ---------------- QUIZ SECTION ----------------
if st.session_state.quiz_generated and st.session_state.quiz:
    st.subheader("📋 Quiz Time!")

    user_answers_map = {}

    for i, q in enumerate(st.session_state.quiz):
        st.write(f"**Q{i+1}. {q['question']}**")

        current_answer = st.session_state.get(f'answer_{i}', q["options"][0])

        try:
            default_index = q["options"].index(current_answer)
        except ValueError:
            default_index = 0

        chosen = st.radio(
            f"Choose your answer for Q{i+1}",
            q["options"],
            key=f'answer_{i}',
            index=default_index
        )

        user_answers_map[i] = (chosen, q["answer"])

    if st.button("Submit Quiz", disabled=st.session_state.quiz_submitted):
        st.session_state.quiz_submitted = True


    # ---------------- RESULTS SECTION ----------------
    if st.session_state.quiz_submitted:
        st.subheader("📊 Quiz Analysis")

        correct = 0
        total = len(user_answers_map)

        for i, (chosen, correct_ans) in user_answers_map.items():
            if chosen == correct_ans:
                st.markdown(f"✅ **Q{i+1}: Correct!** — Your answer: *{chosen}*")
                correct += 1
            else:
                st.markdown(f"❌ **Q{i+1}: Wrong.** Your answer: *{chosen}*, Correct: *{correct_ans}*")

        score = round((correct / total) * 100, 2)
        st.write("---")
        st.success(f"🎯 Final Score: {correct}/{total} ({score}% accuracy)")

        if score == 100:
            st.balloons()


        # ---------------- Dashboard Stats ----------------
        if "quiz_attempts" not in st.session_state:
            st.session_state.quiz_attempts = 0
        if "average_accuracy" not in st.session_state:
            st.session_state.average_accuracy = 0

        prev = st.session_state.quiz_attempts
        new_total = prev + 1

        st.session_state.average_accuracy = (
            (st.session_state.average_accuracy * prev + score) / new_total
        )
        st.session_state.quiz_attempts = new_total

        if "results" not in st.session_state:
            st.session_state.results = []

        st.session_state.results.append({
            "score": score,
            "correct": correct,
            "total": total
        })
