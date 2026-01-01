import streamlit as st
import google.generativeai as genai
import pdfplumber
import os
import datetime
import json
from datetime import date, timedelta
from supabase import create_client, Client

# ---------------- Page config ----------------
st.set_page_config(page_title="NexStudy — Study Planner Pro", page_icon="📅", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("assets/image.png"):
    st.image("assets/image.png", width=150)
elif os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("📅 NexStudy — Study Planner (Pro)")
st.write("Pro features: save/load plans, intensity control, ICS export, and AI customization.")

# ---------------- Supabase Client ----------------
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
        return None

supabase = get_supabase()

# ---------------- Session State Init ----------------
if "todos" not in st.session_state:
    st.session_state.todos = []

# ---------------- Gemini Initialization ----------------
@st.cache_resource
def init_gemini(api_key_input: str | None = None):
    key = api_key_input
    # 1. Prefer input key
    if not key:
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
            return genai.GenerativeModel("gemini-2.5-flash-lite")
        except Exception:
            return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        st.error(f"Gemini initialization error: {e}")
        return None

# ---------------- Sidebar: Settings ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Check for API Key in Session State or Secrets
    api_key = None
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Enter Gemini API Key:", type="password")

    st.header("🛠️ Planner Options")
    st.checkbox("Enable verbose plan (more detail)", value=True, key="verbose_plan")
    
    # User Info from Session State
    user = st.session_state.get("user")
    if user:
        st.info(f"Logged in as: {user.get('email')}")
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

# ---------------- Database Functions ----------------
def fetch_saved_plans():
    """Fetch saved_plans array from Supabase profiles"""
    if not user or not supabase: return []
    try:
        res = supabase.table("profiles").select("saved_plans").eq("id", user["id"]).single().execute()
        if res.data:
            return res.data.get("saved_plans") or []
    except Exception as e:
        # st.error(f"Error fetching plans: {e}")
        pass
    return []

def save_plan_to_db(plan_package):
    """Append new plan to saved_plans in Supabase"""
    if not user or not supabase: return
    try:
        current_plans = fetch_saved_plans()
        # Add timestamp title if missing
        if "title" not in plan_package:
            plan_package["title"] = f"Plan {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        current_plans.append(plan_package)
        
        # Update DB
        supabase.table("profiles").update({"saved_plans": current_plans}).eq("id", user["id"]).execute()
        
        # Optional: Increment plans_created count if column exists
        try:
            # We first get current count
            res = supabase.table("profiles").select("plans_created").eq("id", user["id"]).single().execute()
            current_count = res.data.get("plans_created", 0) or 0
            supabase.table("profiles").update({"plans_created": current_count + 1}).eq("id", user["id"]).execute()
        except: 
            pass
            
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

def sync_todos():
    """Sync todos to Supabase"""
    if user and supabase:
        try:
            supabase.table("profiles").update({"todos": st.session_state.todos}).eq("id", user["id"]).execute()
        except Exception as e:
            st.warning(f"Could not sync todos: {e}")

# ---------------- To-Do List Helpers ----------------
def add_todo():
    task = st.session_state.new_todo
    if task:
        st.session_state.todos.append({"task": task, "done": False})
        st.session_state.new_todo = "" # Clear input
        sync_todos()

def toggle_todo(index):
    st.session_state.todos[index]["done"] = not st.session_state.todos[index]["done"]
    sync_todos()

def delete_todo(index):
    st.session_state.todos.pop(index)
    sync_todos()
    st.rerun()

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

    # Show Saved Plans if logged in
    if user and supabase:
        st.markdown("---")
        st.subheader("Saved Plans")
        saved_plans = fetch_saved_plans()
        if saved_plans:
            # Create a dict for easy lookup
            plan_options = {p.get("title", f"Plan {i}"): p for i, p in enumerate(saved_plans)}
            sel_name = st.selectbox("Load a saved plan:", ["-- select saved plan --"] + list(plan_options.keys()))
            
            if sel_name and sel_name != "-- select saved plan --":
                if st.button("Load selected plan"):
                    loaded = plan_options[sel_name]
                    st.session_state["loaded_plan"] = loaded
                    st.success("Loaded plan into view.")
                    st.rerun()
        else:
            st.info("No saved plans yet.")

with col_right:
    # TABS: Switch between AI Plan and Personal To-Do List
    tab_plan, tab_todo = st.tabs(["📅 AI Study Plan", "✅ Personal To-Do"])
    
    with tab_plan:
        # Check if we have a loaded plan OR a newly generated one
        display_plan = st.session_state.get("loaded_plan") or {
            "markdown": st.session_state.get("session_plan_markdown"),
            "meta": st.session_state.get("session_plan_meta"),
            "days": st.session_state.get("session_plan_days")
        }

        if display_plan.get("markdown"):
            st.markdown("### Active Plan")
            st.markdown(display_plan["markdown"])
            
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("Download (MD)", data=display_plan["markdown"], file_name="NexStudy_Plan.md", mime="text/markdown")
            with c2:
                if st.button("Download (ICS)"):
                    ics_content = create_ics(display_plan.get("meta",{}), display_plan.get("days", []))
                    st.download_button("Click to Download ICS", data=ics_content, file_name="NexStudy_Plan.ics", mime="text/calendar")
            
            if user:
                if st.button("💾 Save this Plan to Cloud"):
                    success = save_plan_to_db(display_plan)
                    if success:
                        st.success("Plan Saved!")
                        st.rerun()
                
                if st.session_state.get("loaded_plan") and st.button("Clear View"):
                    del st.session_state["loaded_plan"]
                    st.rerun()
        else:
            st.info("After you fill the configuration and click Generate, the plan will appear here.")

    with tab_todo:
        st.markdown("### My Study Tasks")
        st.caption("Add your own manual tasks here. Synced to your account.")
        
        # Load todos from Supabase if logged in and session todos empty
        if user and not st.session_state.todos:
             try:
                 res = supabase.table("profiles").select("todos").eq("id", user["id"]).single().execute()
                 if res.data and res.data.get("todos"):
                     st.session_state.todos = res.data["todos"]
             except: pass

        # Add Todo Input
        st.text_input("Add a new task:", key="new_todo", on_change=add_todo, placeholder="e.g. Read Chapter 4 by tonight")
        
        # Display Todos
        if st.session_state.todos:
            st.markdown("---")
            for i, todo in enumerate(st.session_state.todos):
                c1, c2, c3 = st.columns([0.1, 0.8, 0.1])
                with c1:
                    st.checkbox("", value=todo["done"], key=f"todo_{i}", on_change=toggle_todo, args=(i,))
                with c2:
                    if todo["done"]:
                        st.markdown(f"~~{todo['task']}~~")
                    else:
                        st.markdown(todo['task'])
                with c3:
                    if st.button("🗑️", key=f"del_{i}"):
                        delete_todo(i)
            
            if st.button("Clear Completed Tasks"):
                st.session_state.todos = [t for t in st.session_state.todos if not t["done"]]
                sync_todos()
                st.rerun()
        else:
            st.info("No tasks yet.")

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
            if len(topics) < 3:
                topics = [t.strip() for t in final_syllabus.replace("\n",",").split(",") if t.strip()]

            plan_meta = {
                "name": name or "Student",
                "email": user.get("email") if user else "local",
                "exam_date": exam_dt.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "daily_hours": daily_hours,
                "intensity": intensity,
                "focus_areas": [f.strip() for f in focus_areas.split(",") if f.strip()],
            }

            prompt = f"""
            You are an expert study planner.
            Context: Exam in {days_left} days. Daily hours: {daily_hours}.
            Topics: {json.dumps(topics[:300], ensure_ascii=False)}
            Focus: {plan_meta['focus_areas']}
            
            Task: Create a daily schedule.
            Output JSON ONLY:
            {{
                "quote": "string",
                "strategy": ["string", "string"],
                "days": [
                    {{"date": "YYYY-MM-DD", "topic": "string", "activity": "string", "duration_hours": int}}
                ]
            }}
            """
            
            # Call Gemini
            with st.spinner("Generating plan (Pro AI)..."):
                # Enforce JSON mode
                res = call_gemini(prompt, generation_config={"response_mime_type": "application/json"})
                
                if res.get("error"):
                    st.error(f"AI Error: {res['error']}")
                else:
                    raw = res["text"].strip()
                    # Clean markdown code blocks if present
                    if "```" in raw:
                        raw = raw.replace("```json", "").replace("```", "")
                    
                    try:
                        parsed = json.loads(raw)
                        
                        # Process Data
                        days = parsed.get("days", [])
                        # Ensure we don't exceed days_left
                        days = days[:days_left]
                        
                        plan_meta["quote"] = parsed.get("quote", "Keep going!")
                        plan_meta["strategy"] = parsed.get("strategy", [])

                        md_days = []
                        for d in days:
                            md_days.append({
                                "date": d.get("date", "Unknown"), 
                                "topic": d.get("topic", "Review"), 
                                "activity": d.get("activity", "Study"), 
                                "duration_hours": d.get("duration_hours", daily_hours)
                            })

                        md_text = generate_plan_markdown(plan_meta, md_days)

                        # Save to session
                        st.session_state["session_plan_meta"] = plan_meta
                        st.session_state["session_plan_days"] = md_days
                        st.session_state["session_plan_markdown"] = md_text
                        
                        # Clear any loaded plan so the new one shows
                        if "loaded_plan" in st.session_state:
                            del st.session_state["loaded_plan"]

                        st.success("✅ Plan generated.")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Failed to parse plan. Raw output:\n{raw}")
