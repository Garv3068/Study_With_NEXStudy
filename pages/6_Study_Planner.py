import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
import io
import json
from datetime import date, timedelta

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy — Study Planner Pro", page_icon="📅", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
# if os.path.exists("assets/image.png"):
    # st.image("assets/image.png", width=150)
# elif os.path.exists("logo.png"):
    # st.image("logo.png", width=150)
# elif os.path.exists("logo.jpg"):
    # st.image("logo.jpg", width=150)

st.title("📅 NexStudy — Study Planner (Pro)")
st.write("Pro features: save/load plans, intensity control, ICS export, and AI customization.")

# ---------------- Ensure storage folder ----------------
SAVE_DIR = "nexstudy_plans"
os.makedirs(SAVE_DIR, exist_ok=True)

# ---------------- Gemini Initialization ----------------
@st.cache_resource
def init_gemini(api_key_input: str | None = None):
    key = None
    # 1. Prefer input key
    if api_key_input:
        key = api_key_input
    # 2. Else check secrets
    else:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

    if not key:
        return None

    try:
        genai.configure(api_key=key)
        # Try latest model, fallback to stable
        try:
            return genai.GenerativeModel("gemini-2.0-flash")
        except Exception:
            return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ---------------- Sidebar: Settings ----------------
with st.sidebar:
    # st.header("⚙️ Settings")
    
    # Check for API Key in Session State or Secrets
    api_key = None
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        # st.success("✅ API Key loaded from secrets")
    else:
        api_key = st.text_input("Enter Gemini API Key:", type="password")

    st.markdown("---")
    st.header("🛠️ Planner Options")
    st.checkbox("Enable verbose plan (more detail)", value=True, key="verbose_plan")
    
    # User Info from Session State (Central Login)
    user_email = st.session_state.get("user_email")
    if user_email:
        st.info(f"Logged in as: {user_email}")
        st.caption(f"Plans save to: {SAVE_DIR}")
    else:
        st.warning("You are in Guest Mode. Sign in on the Home page to save plans permanently.")

gemini_model = init_gemini(api_key)

# ---------------- Helper functions ----------------
def extract_text_from_pdf(uploaded_file) -> str:
    try:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text.strip()
    except Exception as e:
        st.error(f"PDF extraction error: {e}")
        return ""

def call_gemini(prompt: str, generation_config=None) -> dict:
    """Safe wrapper to call gemini and return dict with keys 'text' or 'error'"""
    if gemini_model is None:
        return {"error": "Gemini model not initialized. Provide API key."}
    try:
        resp = gemini_model.generate_content(prompt, generation_config=generation_config)
        return {"text": resp.text or ""}
    except Exception as e:
        return {"error": str(e)}

def generate_plan_markdown(plan_meta: dict, day_plan: list) -> str:
    """Create full markdown text of the plan"""
    header = f"# NexStudy — Study Plan for {plan_meta.get('name','Student')}\n\n"
    header += f"- Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    header += f"- Exam date: {plan_meta['exam_date']}\n"
    header += f"- Days left: {plan_meta['days_left']}\n"
    header += f"- Daily study hours: {plan_meta['daily_hours']} hours\n"
    header += f"- Intensity: {plan_meta['intensity']}\n\n"
    header += "## Motivational Quote\n\n"
    header += f"> {plan_meta.get('quote','Stay consistent — small daily wins add up!')}\n\n"
    header += "## Day-by-day Plan\n\n"
    header += "| Day | Date | Topic | Activity |\n|---|---:|---|---|\n"
    for idx, day in enumerate(day_plan, start=1):
        header += f"| Day {idx} | {day.get('date')} | {day.get('topic')} | {day.get('activity')} |\n"
    header += "\n\n## Strategy for Success\n"
    header += "\n".join([f"- {p}" for p in plan_meta.get("strategy", [])])
    return header

def save_plan_to_disk(email: str, plan_data: dict) -> str:
    """Saves the plan JSON to SAVE_DIR and returns filepath"""
    safe_email = email.replace("@","_at_").replace(".","_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"plan_{safe_email}_{timestamp}.json"
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2)
    return path

def list_saved_plans(email: str) -> list:
    """Return list of saved plan files for this email (sorted newest first)"""
    files = []
    safe = email.replace("@","_at_").replace(".","_")
    if os.path.exists(SAVE_DIR):
        for fname in os.listdir(SAVE_DIR):
            if fname.startswith(f"plan_{safe}_"):
                files.append(os.path.join(SAVE_DIR, fname))
    files.sort(reverse=True)
    return files

def load_plan_from_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def create_ics(plan_meta: dict, day_plan: list) -> str:
    """Return content for an .ics file (string) representing daily study events."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//NexStudy//StudyPlannerPro//EN"
    ]
    for idx, d in enumerate(day_plan, start=1):
        try:
            dt = datetime.datetime.strptime(d["date"], "%Y-%m-%d")
            dtstart = dt.strftime("%Y%m%d")
            uid = f"nexstudy-{plan_meta.get('email','local')}-{idx}"
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{datetime.datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"SUMMARY:Study: {d.get('topic', 'Topic')}",
                f"DESCRIPTION:{d.get('activity', 'Study')}",
                "END:VEVENT"
            ]
        except:
            continue
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

# ---------------- UI: Planner form ----------------
col_left, col_right = st.columns([1.1, 1.9])

with col_left:
    st.subheader("Plan configuration")
    with st.form("planner_pro_form"):
        name = st.text_input("Your name (optional):")
        syllabus_source = st.radio("Syllabus input:", ["Paste text", "Upload PDF"], index=0)
        syllabus_text = ""
        uploaded_file = None
        if syllabus_source == "Paste text":
            syllabus_text = st.text_area("Paste chapters/topics (one per line):", height=180,
                                        placeholder="1. Algebra\n2. Calculus\n3. Coordinate Geometry")
        else:
            uploaded_file = st.file_uploader("Upload syllabus PDF (≤ 10 MB):", type=["pdf"])
        
        today_dt = date.today()
        exam_dt = st.date_input("Exam date:", min_value=today_dt + timedelta(days=1))
        daily_hours = st.slider("Daily study hours:", 1, 12, 4)
        intensity = st.selectbox("Intensity:", ["Light (easier pace)", "Normal", "Intensive (more practice)"])
        focus_areas = st.text_input("Focus areas (comma separated):", placeholder="e.g. Organic Chemistry, Integration")
        prefer_review_days = st.number_input("Reserve days before exam for revision:", min_value=0, max_value=30, value=7)
        generate = st.form_submit_button("🚀 Generate Pro Plan")

    # Only show Saved Plans if logged in
    if user_email:
        st.markdown("---")
        st.subheader("Saved Plans")
        files = list_saved_plans(user_email)
        if files:
            sel = st.selectbox("Load a saved plan:", ["-- select saved plan --"] + files)
            if sel and sel != "-- select saved plan --":
                if st.button("Load selected plan"):
                    loaded = load_plan_from_file(sel)
                    st.session_state["loaded_plan"] = loaded
                    st.success("Loaded plan into view.")
                    st.rerun()
        else:
            st.info("No saved plans yet.")

with col_right:
    st.subheader("Plan preview / results")
    # If a plan has been loaded externally, show that
    if st.session_state.get("loaded_plan"):
        plan_obj = st.session_state.get("loaded_plan")
        md = plan_obj.get("markdown", "")
        st.markdown("### Loaded plan")
        st.markdown(md)
        st.download_button("Download loaded plan (MD)", data=md, file_name="loaded_plan.md", mime="text/markdown")
        # Offer ICS too if present
        if st.button("Download loaded plan as ICS"):
            ics_content = create_ics(plan_obj.get("meta",{}), plan_obj.get("days", []))
            st.download_button("Download ICS", data=ics_content, file_name="loaded_plan.ics", mime="text/calendar")
        
        if st.button("Clear Loaded Plan"):
            del st.session_state["loaded_plan"]
            st.rerun()
            
    else:
        # Show instructions or existing session plan
        if "session_plan_markdown" in st.session_state:
            st.markdown("### Current generated plan (unsaved)")
            st.markdown(st.session_state["session_plan_markdown"])
        else:
            st.info("After you fill the configuration and click Generate, the plan will appear here.")

# ---------------- Generate plan logic ----------------
if 'generate' in locals() and generate:
    # Prepare final syllabus text
    final_syllabus = syllabus_text
    if syllabus_source == "Upload PDF" and uploaded_file:
        final_syllabus = extract_text_from_pdf(uploaded_file)
    if not final_syllabus or final_syllabus.strip() == "":
        st.warning("Please provide a syllabus (paste text or upload a PDF).")
    else:
        # Calculate days left
        days_left = (exam_dt - today_dt).days
        if days_left <= (prefer_review_days + 1):
            st.warning("Too few days left for the selected revision days. Reduce revision days or choose later exam date.")
        else:
            # Prepare prompt for Gemini
            topics = [t.strip() for t in final_syllabus.splitlines() if t.strip()]
            if not topics or len(topics) < 3:
                topics = [t.strip() for t in final_syllabus.replace("\n",",").split(",") if t.strip()]

            plan_meta = {
                "name": name or "Student",
                "email": user_email or "local",
                "exam_date": exam_dt.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "daily_hours": daily_hours,
                "intensity": intensity,
                "focus_areas": [f.strip() for f in focus_areas.split(",") if f.strip()],
            }

            # Formulate the prompt
            prompt = f"""
            You are an expert study strategist. Create a day-by-day study plan given the following constraints.

            Syllabus topics (short list):
            {json.dumps(topics[:200], ensure_ascii=False)}

            Exam date: {exam_dt.strftime('%Y-%m-%d')}
            Days remaining: {days_left}
            Daily study hours: {daily_hours}
            Intensity: {intensity}
            Reserve {prefer_review_days} days at the end for revision.
            Focus areas (prioritize these): {plan_meta['focus_areas']}

            Output a strictly valid JSON with:
            - "quote": motivational short sentence
            - "strategy": list of 3 quick bullet points
            - "days": list of objects with keys: "date" (YYYY-MM-DD), "topic", "activity" (Read/Practice/Revise), "duration_hours"
            Return only JSON.
            """
            
            # Call Gemini
            with st.spinner("Generating plan (Pro AI)..."):
                # Enforce JSON mode for reliability
                res = call_gemini(prompt, generation_config={"response_mime_type": "application/json"})
                if res.get("error"):
                    st.error(f"AI Error: {res['error']}")
                else:
                    raw = res["text"].strip()
                    try:
                        parsed = json.loads(raw)
                    except Exception as e:
                        st.error("Failed to parse AI output as JSON.")
                        st.code(raw)
                        parsed = None

                    if parsed:
                        # Compose day plan markdown and meta
                        days = parsed.get("days", [])
                        days = days[:days_left] # limit days to days_left
                        
                        plan_meta["quote"] = parsed.get("quote", "Stay consistent.")
                        plan_meta["strategy"] = parsed.get("strategy", ["Focus on weak areas"])

                        md_days = []
                        for d in days:
                            md_days.append({
                                "date": d.get("date"), 
                                "topic": d.get("topic", "Topic"), 
                                "activity": d.get("activity", "Study"), 
                                "duration_hours": d.get("duration_hours", daily_hours)
                            })

                        md_text = generate_plan_markdown(plan_meta, md_days)

                        # store in session_state
                        st.session_state["session_plan_meta"] = plan_meta
                        st.session_state["session_plan_days"] = md_days
                        st.session_state["session_plan_markdown"] = md_text

                        st.success("✅ Plan generated.")
                        st.rerun()

# ---------------- Actions: Save, Export, ICS ----------------
if st.session_state.get("session_plan_markdown"):
    st.sidebar.markdown("---")
    st.sidebar.subheader("Plan Actions")
    if user_email:
        if st.sidebar.button("Save Plan (to server)"):
            plan_package = {
                "meta": st.session_state.get("session_plan_meta", {}),
                "days": st.session_state.get("session_plan_days", []),
                "markdown": st.session_state.get("session_plan_markdown", "")
            }
            saved_path = save_plan_to_disk(user_email, plan_package)
            st.sidebar.success(f"Saved!")
    
    st.sidebar.download_button("Download Plan (MD)", data=st.session_state["session_plan_markdown"],
                               file_name="NexStudy_Plan.md", mime="text/markdown")
    
    if st.sidebar.button("Download Plan (ICS)"):
        ics = create_ics(st.session_state.get("session_plan_meta", {}), st.session_state.get("session_plan_days", []))
        st.sidebar.download_button("Download ICS file", data=ics, file_name="NexStudy_Plan.ics", mime="text/calendar")
        st.sidebar.success("ICS generated.")
