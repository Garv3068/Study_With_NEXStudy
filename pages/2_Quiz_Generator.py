from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import string
import google.generativeai as genai   # ✅ Added for Gemini

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
# This ensures Streamlit Cloud won't crash if resources are missing
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
@@ -18,66 +37,66 @@
except LookupError:
    nltk.download('stopwords')


# ---------------- Helper Functions ----------------
def extract_text_from_pdf(uploaded_file):
    """Extract text safely from uploaded PDF"""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def clean_text(text):
    """Remove punctuation for better keyword extraction"""
    return text.translate(str.maketrans("", "", string.punctuation))

def generate_questions(text, num_questions=5):
    """Generate fill-in-the-blank questions from text"""
    sentences = sent_tokenize(text)
    sentences = [clean_text(s) for s in sentences if s.strip()]

    words = [w for w in word_tokenize(text.lower()) if w.isalpha()]
    stop_words = set(stopwords.words("english"))
    words = [w for w in words if w not in stop_words]
# ---------------- REPLACED WITH GEMINI ----------------
def generate_questions(text, num_questions=5):
    """Generate MCQ quiz using Gemini instead of rule-based system"""

    freq_dist = nltk.FreqDist(words)
    important_words = [word for word, _ in freq_dist.most_common(50)]
    if gemini_model is None:
        st.error("❌ Gemini model is not initialized.")
        return []

    questions = []
    prompt = f"""
    You are an expert quiz generator.

    for _ in range(num_questions):
        if not sentences:
            break
    Create {num_questions} high-quality MCQs from the following study material:

        sent = random.choice(sentences)
        sentences.remove(sent)
    ---CONTENT START---
    {text[:15000]}
    ---CONTENT END---

        keywords_in_sent = [w for w in word_tokenize(sent.lower()) if w in important_words]
        if not keywords_in_sent:
            continue
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

        answer = random.choice(keywords_in_sent)
        question = sent.replace(answer, "______", 1)
    try:
        response = gemini_model.generate_content(prompt)
        quiz = eval(response.text)  # safe because Gemini outputs JSON list

        options_pool = [w for w in important_words if w != answer]
        options = random.sample(options_pool, min(3, len(options_pool)))
        if answer not in options:
            options.append(answer)
        random.shuffle(options)
        return quiz

        questions.append({
            "question": question,
            "options": options,
            "answer": answer
        })
    except Exception as e:
        st.error(f"❌ Gemini Quiz Generation Error: {e}")
        return []

    return questions

# ---------------- Streamlit App ----------------
# ---------------- Streamlit UI (UNCHANGED) ----------------
st.title("🧠 Smart Quiz Generator")
st.write("Generate quizzes from your notes or PDFs instantly!")

# --- Session State Initialization ---
if 'quiz' not in st.session_state:
    st.session_state.quiz = []
if 'quiz_generated' not in st.session_state:
@@ -95,8 +114,7 @@ def generate_and_store_quiz(text_data):
        st.session_state.quiz = generate_questions(text_data)
        st.session_state.quiz_generated = True
        st.session_state.quiz_submitted = False
        for i, q in enumerate(st.session_state.quiz):
            st.session_state[f'answer_{i}'] = q["options"][0]


# ---------------- Input Section ----------------
input_type = st.radio("Choose Input Type:", ("Upload PDF", "Paste Text"), on_change=reset_quiz)
@@ -109,10 +127,12 @@ def generate_and_store_quiz(text_data):
else:
    text_data = st.text_area("Paste your study material here:", key='text_input', on_change=reset_quiz)


# ---------------- Generate Quiz Button ----------------
if st.button("Generate Quiz", disabled=not text_data.strip()):
    generate_and_store_quiz(text_data)


# ---------------- Quiz Section ----------------
if st.session_state.quiz_generated and st.session_state.quiz:
    st.subheader("📋 Quiz Time!")
@@ -121,56 +141,37 @@ def generate_and_store_quiz(text_data):
    for i, q in enumerate(st.session_state.quiz):
        st.write(f"**Q{i+1}.** {q['question']}")

        current_answer = st.session_state.get(f'answer_{i}', q["options"][0])
        try:
            default_index = q["options"].index(current_answer)
        except ValueError:
            default_index = 0

        options = q["options"]
        chosen = st.radio(
            f"Choose your answer for Q{i+1}",
            q["options"],
            key=f'answer_{i}',
            index=default_index
            options,
            key=f'answer_{i}'
        )

        user_answers_map[i] = (chosen, q["answer"])

    def submit_quiz():
        st.session_state.quiz_submitted = True

    if st.button("Submit Quiz", disabled=st.session_state.quiz_submitted):
        submit_quiz()
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
                st.markdown(f"❌ **Q{i+1}: Incorrect.** Your answer: *{chosen}* | Correct answer: *{correct_ans}*")
                st.markdown(
                    f"❌ **Q{i+1}: Incorrect.** Your answer: *{chosen}* | Correct: *{correct_ans}*"
                )

        score = round((correct / total) * 100, 2)
        st.write("---")
        st.success(f"🎯 Final Score: {correct}/{total} ({score}% accuracy)")
        # --- Update Dashboard Stats ---
        if "quiz_attempts" not in st.session_state:
            st.session_state.quiz_attempts = 0
        if "average_accuracy" not in st.session_state:
            st.session_state.average_accuracy = 0

# Update stats dynamically
        prev_total = st.session_state.quiz_attempts
        new_total = prev_total + 1
        st.session_state.average_accuracy = (
        (st.session_state.average_accuracy * prev_total + accuracy) / new_total
)
        st.session_state.quiz_attempts = new_total


        if score == 100:
@@ -181,15 +182,4 @@ def submit_quiz():
        elif score >= 40:
            st.warning("💪 Good effort! Review and try again!")
        else:
            st.error("📚 Don’t give up — practice makes progress!")
        # Save result in session_state for Dashboard
        if "results" not in st.session_state:
            st.session_state.results = []

        st.session_state.results.append({
        "score": score,
        "correct": correct,
        "total": total,
        "timestamp": st.session_state.get("quiz_timestamp", st.session_state.get("run_id", "N/A"))
})
        
            st.error("📚 Practice more — you'll get better!")
