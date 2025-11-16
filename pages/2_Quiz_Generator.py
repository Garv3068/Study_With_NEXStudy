import streamlit as st
import random
import re
import pdfplumber
import string

# ---------------- Helper Functions ----------------
def extract_text_from_pdf(uploaded_file):
    """Extract text safely from uploaded PDF."""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def split_into_sentences(text):
    """Simple lightweight sentence tokenizer using regex instead of NLTK."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 25]


def clean_text(text):
    """Remove punctuation for consistent processing."""
    return text.translate(str.maketrans("", "", string.punctuation))


def extract_keywords(text):
    """Extract simple keywords by frequency without NLTK."""
    text = clean_text(text.lower())
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
    stop_words = {
        "this", "that", "there", "where", "when", "which", "from", "with",
        "have", "been", "were", "will", "shall", "would", "should", "could",
        "they", "them", "their", "about", "your", "into", "because", "these",
        "those", "while", "after", "before", "also", "some", "many"
    }

    filtered = [w for w in words if w not in stop_words]
    freq = {}

    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, c in sorted_words[:50]]


def generate_questions(text, num_questions=5):
    """Generate simple fill-in-the-blank MCQ questions."""
    sentences = split_into_sentences(text)
    keywords = extract_keywords(text)

    if not sentences or not keywords:
        return [{
            "question": "Unable to generate questions due to insufficient content.",
            "options": ["N/A"],
            "answer": "N/A"
        }]

    questions = []

    for _ in range(num_questions):
        if not sentences:
            break

        sent = random.choice(sentences)
        sentences.remove(sent)

        words = [w.lower() for w in re.findall(r'\b\w+\b', sent)]
        keywords_in_sent = [w for w in words if w in keywords]

        if not keywords_in_sent:
            continue

        answer = random.choice(keywords_in_sent)
        question = re.sub(answer, "______", sent, count=1)

        # Generate options
        options_pool = [w for w in keywords if w != answer]
        if len(options_pool) < 3:
            continue

        options = random.sample(options_pool, 3)
        options.append(answer)
        random.shuffle(options)

        questions.append({
            "question": question,
            "options": options,
            "answer": answer
        })

    return questions


# ---------------- Streamlit App ----------------
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
        st.session_state.quiz = generate_questions(text_data)
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

# ---------------- Generate Quiz Button ----------------
if st.button("Generate Quiz", disabled=not text_data.strip()):
    generate_and_store_quiz(text_data)

# ---------------- Quiz Section ----------------
if st.session_state.quiz_generated and st.session_state.quiz:
    st.subheader("📋 Quiz Time!")

    user_answers_map = {}
    for i, q in enumerate(st.session_state.quiz):
        st.write(f"**Q{i+1}.** {q['question']}")

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

        score = round((correct / total) * 100, 2)
        st.write("---")
        st.success(f"🎯 Final Score: {correct}/{total} ({score}% accuracy)")

        # Celebration
        if score == 100:
            st.balloons()
            st.info("🌟 Perfect! You're a quiz master!")
        elif score >= 70:
            st.info("👏 Great job! Keep it up!")
        elif score >= 40:
            st.warning("💪 Good effort! Review and try again!")
        else:
            st.error("📚 Don’t give up — practice makes progress!")

