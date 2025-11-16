import streamlit as st
import pdfplumber
import json
import re
import random
import google.generativeai as genai
from typing import List, Dict

# ---------------- Page config ----------------
st.set_page_config(page_title="Quiz Generator | NexStudy", layout="wide")
st.title("🧠 NexStudy — AI Quiz Generator (Gemini)")
st.write("Upload a PDF or paste text and generate MCQs automatically.")

# ---------------- Gemini init ----------------
@st.cache_resource
def init_gemini_model():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Prefer 2.5 flash; fallback handled in exception
        try:
            return genai.GenerativeModel("gemini-2.5-flash")
        except Exception:
            # fallback to an older/smaller model name if unavailable
            return genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

model = init_gemini_model()

# ---------------- Helpers ----------------
def extract_text_from_pdf(uploaded_file) -> str:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def safe_trim_text(text: str, max_chars: int = 8000) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    # try to keep whole paragraphs: split on double newline and accumulate
    parts = re.split(r'\n\s*\n', text)
    acc = ""
    for p in parts:
        if len(acc) + len(p) + 2 > max_chars:
            break
        acc += p + "\n\n"
    if not acc:
        return text[:max_chars]
    return acc

def parse_gemini_json(text: str):
    """
    Attempt to locate and parse JSON from the model response text.
    Returns a Python object or raises ValueError.
    """
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        # Try to extract the first JSON block using regex
        m = re.search(r'(\{[\s\S]*\})', text)
        if m:
            candidate = m.group(1)
            try:
                return json.loads(candidate)
            except Exception:
                pass
        # Try to find a JSON array
        m2 = re.search(r'(\[[\s\S]*\])', text)
        if m2:
            candidate = m2.group(1)
            try:
                return json.loads(candidate)
            except Exception:
                pass
    raise ValueError("Unable to parse JSON from model response.")

def fallback_generate_questions(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Lightweight fallback: split into sentences and produce simple MCQ-like items
    by blanking out frequent words. Useful when Gemini fails.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    if not sentences:
        return [{
            "question": "Unable to generate questions. Text is too short or unclear.",
            "options": ["N/A", "N/A", "N/A", "N/A"],
            "answer": "N/A"
        }]
    questions = []
    # build simple frequency list
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    freq = {}
    stop = {"which","that","this","these","those","have","with","from","your","their","there","where"}
    for w in words:
        if w in stop: continue
        freq[w] = freq.get(w, 0) + 1
    common = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    common_words = [w for w,_ in common[:50]]

    for i in range(min(num_questions, len(sentences))):
        sent = random.choice(sentences)
        # choose an answer word from sentence that's in common_words
        sent_words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', sent.lower()) if w in common_words]
        if not sent_words:
            # pick any noun-like word
            sent_words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', sent.lower())]
        if not sent_words:
            continue
        ans = random.choice(sent_words)
        qtext = re.sub(r'\b' + re.escape(ans) + r'\b', '______', sent, count=1, flags=re.IGNORECASE)
        # options from common_words
        pool = [w for w in common_words if w != ans]
        opts = (random.sample(pool, min(3, len(pool))) if pool else []) + [ans]
        random.shuffle(opts)
        opts = [o.capitalize() for o in opts]
        questions.append({"question": qtext, "options": opts, "answer": ans.capitalize()})
    if not questions:
        # fallback single message
        return [{
            "question": "Unable to auto-generate quiz from this content.",
            "options": ["N/A","N/A","N/A","N/A"],
            "answer": "N/A"
        }]
    return questions

# ---------------- UI: Input ----------------
st.markdown("## Input")
input_mode = st.radio("Input mode:", ("Upload PDF", "Paste Text"))
text_data = ""

if input_mode == "Upload PDF":
    uploaded = st.file_uploader("Upload PDF (<= 10 MB)", type=["pdf"])
    if uploaded:
        with st.spinner("Extracting text..."):
            text_data = extract_text_from_pdf(uploaded)
else:
    text_data = st.text_area("Paste your study material here (long text or chapter):", height=240)

num_questions = st.slider("Number of questions", min_value=3, max_value=15, value=5, step=1)

generate_btn = st.button("Generate MCQs (Gemini)")

# ---------------- Generate Logic ----------------
if generate_btn:
    if not text_data or not text_data.strip():
        st.warning("Please provide text or upload a PDF first.")
    else:
        # Prepare trimmed input for the model
        trimmed = safe_trim_text(text_data, max_chars=8000)
        prompt = (
            "You are an expert exam-writer for students. Create high-quality multiple-choice questions (MCQs) "
            "based on the provided text. Return output strictly as a JSON array of objects. "
            "Each object must have these keys: 'question' (string), 'options' (array of 4 strings), 'answer' (one of the options), "
            "and optionally 'explanation' (string). Do NOT include any extra commentary or explanation outside the JSON.\n\n"
            f"Text:\n{trimmed}\n\n"
            f"Generate exactly {num_questions} MCQs. Make distractors plausible. Use clear, simple language suitable for college students."
        )

        st.session_state.quiz_error = None
        st.session_state.quiz = []
        st.session_state.quiz_generated = False
        st.session_state.quiz_submitted = False

        if not model:
            st.error("Gemini model not initialized. Falling back to local generation.")
            st.session_state.quiz = fallback_generate_questions(trimmed, num_questions=num_questions)
            st.session_state.quiz_generated = True
        else:
            with st.spinner("Generating MCQs using Gemini..."):
                try:
                    response = model.generate_content(prompt)
                    raw_text = response.text.strip()

                    try:
                        parsed = parse_gemini_json(raw_text)
                        # Expecting a list of question dicts
                        if isinstance(parsed, dict):
                            # if user returned a dict with root key, try to find list inside
                            # e.g., {"questions": [...]}
                            for v in parsed.values():
                                if isinstance(v, list):
                                    parsed = v
                                    break
                        if not isinstance(parsed, list):
                            raise ValueError("Model returned JSON but not a list of questions.")

                        # Basic validation and normalization
                        normalized = []
                        for item in parsed[:num_questions]:
                            q = item.get("question") if isinstance(item, dict) else None
                            opts = item.get("options") if isinstance(item, dict) else None
                            ans = item.get("answer") if isinstance(item, dict) else None
                            expl = item.get("explanation") if isinstance(item, dict) else None

                            if not q or not opts or not ans:
                                continue
                            # Ensure 4 options
                            if not isinstance(opts, list) or len(opts) < 4:
                                # attempt to split string into options
                                if isinstance(opts, str):
                                    opts = [o.strip() for o in re.split(r'[;\n]', opts) if o.strip()]
                                # if still <4, fill with plausible dummy options
                                while len(opts) < 4:
                                    opts.append("None of the above")
                            # Ensure answer is one of options
                            if ans not in opts:
                                # try case-insensitive match
                                match = next((o for o in opts if o.lower() == str(ans).lower()), None)
                                if match:
                                    ans = match
                                else:
                                    # fallback: pick first option as answer
                                    ans = opts[0]

                            normalized.append({
                                "question": q.strip(),
                                "options": [str(x).strip() for x in opts],
                                "answer": str(ans).strip(),
                                "explanation": (str(expl).strip() if expl else "")
                            })

                        if not normalized:
                            raise ValueError("Parsed JSON contained no valid questions.")

                        st.session_state.quiz = normalized
                        st.session_state.quiz_generated = True

                    except Exception as parse_err:
                        # parsing failed — fallback
                        st.warning(f"Could not parse model JSON: {parse_err}. Using local fallback.")
                        st.session_state.quiz = fallback_generate_questions(trimmed, num_questions=num_questions)
                        st.session_state.quiz_generated = True

                except Exception as api_err:
                    st.error(f"Error calling Gemini: {api_err}. Using local fallback.")
                    st.session_state.quiz = fallback_generate_questions(trimmed, num_questions=num_questions)
                    st.session_state.quiz_generated = True

# ---------------- Display Quiz ----------------
if st.session_state.get("quiz_generated", False) and st.session_state.get("quiz"):
    st.markdown("---")
    st.subheader("📋 Generated Quiz")

    # initialize answers in session_state if not present
    for i, q in enumerate(st.session_state.quiz):
        if f"answer_{i}" not in st.session_state:
            st.session_state[f"answer_{i}"] = q["options"][0]

    user_answers = {}
    for i, q in enumerate(st.session_state.quiz):
        st.write(f"**Q{i+1}.** {q['question']}")
        # radio with session state default
        current = st.session_state.get(f"answer_{i}", q["options"][0])
        try:
            default_index = q["options"].index(current)
        except ValueError:
            default_index = 0

        choice = st.radio(f"Choose for Q{i+1}", q["options"], key=f"answer_{i}", index=default_index)
        user_answers[i] = (choice, q["answer"])

    if st.button("Submit Answers"):
        correct = 0
        total = len(user_answers)
        for i, (chosen, correct_ans) in user_answers.items():
            if str(chosen).strip().lower() == str(correct_ans).strip().lower():
                correct += 1

        score = round((correct / total) * 100, 2) if total else 0
        st.success(f"🎯 You scored {correct}/{total} — {score}%")
        # show per-question feedback
        st.markdown("### Details")
        for i, (chosen, correct_ans) in user_answers.items():
            if str(chosen).strip().lower() == str(correct_ans).strip().lower():
                st.markdown(f"✅ Q{i+1} — Correct — Your: `{chosen}`")
            else:
                st.markdown(f"❌ Q{i+1} — Incorrect — Your: `{chosen}` | Correct: `{correct_ans}`")
        # save results to session_state results list
        if "results" not in st.session_state:
            st.session_state["results"] = []
        st.session_state["results"].append({
            "timestamp": str(st.session_state.get("last_generated_time", "") ),
            "score": score,
            "correct": correct,
            "total": total
        })
        # mark submitted
        st.session_state["quiz_submitted"] = True

    # allow user to download quiz as JSON
    if st.button("Download Quiz (JSON)"):
        st.download_button("Download Questions", data=json.dumps(st.session_state.quiz, indent=2), file_name="quiz.json", mime="application/json")
