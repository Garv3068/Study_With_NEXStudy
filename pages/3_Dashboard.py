import streamlit as st
import pandas as pd
import datetime
import os
import json
from supabase import create_client, Client

# ---------------- Page Config ----------------
st.set_page_config(page_title="My Dashboard", page_icon="📊", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Supabase Client ----------------
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None

supabase = get_supabase()

# ---------------- Logo Logic ----------------
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("📊 Personal Performance Dashboard")
st.caption("Track your learning progress across NexStudy tools.")

# ---------------- Helper: Load Stats ----------------
def load_user_stats(user):
    # Default stats (for guests or new users)
    stats = {
        "doubts_solved": 0,
        "plans_created": 0,
        "audio_generated": 0,
        "streak": 0,
        "pending_todos": 0,
        "completed_todos": 0
    }

    # 1. Get Session Stats (Always available)
    msgs = st.session_state.get("messages", [])
    session_doubts = len([m for m in msgs if m["role"] == "user"])
    
    has_plan = 1 if st.session_state.get("session_plan_meta") else 0
    has_audio = 1 if st.session_state.get("podcast_script") else 0
    
    # Get To-Do stats from session
    todos = st.session_state.get("todos", [])
    pending_todos = len([t for t in todos if not t["done"]])
    completed_todos = len([t for t in todos if t["done"]])

    # 2. Get Persistent Stats from Supabase (if logged in)
    if user and supabase:
        try:
            # Fetch profile data
            res = supabase.table("profiles").select("*").eq("id", user["id"]).single().execute()
            if res.data:
                profile = res.data
                # Assuming you might store these in profile later. 
                # For now, we'll use session data but you can expand this.
                # Example: stats["streak"] = profile.get("streak", 0)
                pass
        except Exception:
            pass

    # Combine/Update stats
    stats["doubts_solved"] = session_doubts
    stats["plans_created"] = has_plan
    stats["audio_generated"] = has_audio
    stats["pending_todos"] = pending_todos
    stats["completed_todos"] = completed_todos
    
    # Simple streak logic (Mock calculation)
    activity_count = session_doubts + has_plan + has_audio + len(todos)
    stats["streak"] = 1 if activity_count > 0 else 0
    
    return stats

# ---------------- User State ----------------
user = st.session_state.get("user")
stats = load_user_stats(user)

# Display User Name
if st.session_state.user:
        if st.session_state.profile and "username" in st.session_state.profile:
            name = st.session_state.profile["username"]
        else:
            name = st.session_state.user.get("email", "")
    st.subheader(f"Welcome back, {name} 👋")
else:
    st.subheader("Welcome, Guest 👋")

# ---------------- Top Metrics Row ----------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="🔥 Streak", value=f"{stats['streak']} Days")

with col2:
    st.metric(label="💬 Doubts", value=stats['doubts_solved'], delta="Session")

with col3:
    st.metric(label="📅 Plans", value=stats['plans_created'], delta="Planner")

with col4:
    st.metric(label="🎧 Audio", value=stats['audio_generated'], delta="Podcaster")

with col5:
    st.metric(label="✅ To-Dos", value=f"{stats['completed_todos']}/{stats['pending_todos'] + stats['completed_todos']}", delta=f"{stats['pending_todos']} Left")

st.markdown("---")

# ---------------- Main Dashboard Grid ----------------
grid_col1, grid_col2 = st.columns([2, 1])

# === LEFT COLUMN: Productivity Chart ===
with grid_col1:
    # Activity Chart (REAL-TIME SESSION DATA)
    st.subheader("📈 Productivity Trends")
    
    # Initialize empty data for the week
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    doubts_data = [0] * 7
    hours_data = [0] * 7
    
    # Update "Today's" data point with current session stats
    today_index = datetime.datetime.today().weekday() # 0 is Monday, 6 is Sunday
    doubts_data[today_index] = stats['doubts_solved']
    
    # Calculate simple activity score
    # Doubts + Plans + Audio + Completed Tasks
    activity_score = (stats['plans_created'] * 2) + (stats['audio_generated'] * 2) + (stats['completed_todos'] * 1) + (stats['doubts_solved'] * 0.5)
    hours_data[today_index] = activity_score

    chart_data = pd.DataFrame({
        'Day': days,
        'Doubts Solved': doubts_data,
        'Activity Score': hours_data
    })
    
    st.line_chart(chart_data.set_index('Day'))
    
    if not user:
        st.caption("👀 You are viewing **Guest Data** (Current Session Only). Sign in to save history.")

# === RIGHT COLUMN: Quick Actions & History ===
with grid_col2:
    # 3. Pending Tasks (NEW)
    st.subheader("📝 Pending Tasks")
    todos = st.session_state.get("todos", [])
    pending = [t for t in todos if not t["done"]]
    
    if pending:
        for t in pending[:3]: # Show top 3
            st.markdown(f"- ⬜ {t['task']}")
        if len(pending) > 3:
            st.caption(f"...and {len(pending) - 3} more.")
        
        if st.button("Manage Tasks"):
            st.switch_page("pages/6_Study_Planner.py")
    else:
        st.success("🎉 All caught up!")
        if st.button("Add Tasks"):
            st.switch_page("pages/6_Study_Planner.py")

    st.markdown("---")

    # 4. AI Tutor Recent Context
    st.subheader("🤖 Recent Doubts")
    messages = st.session_state.get("messages", [])
    if messages:
        # Get last 3 user messages
        user_msgs = [m['text'] for m in messages if m['role'] == 'user'][-3:]
        if user_msgs:
            for msg in reversed(user_msgs):
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 0.9em; color: black;">
                    ❓ {msg[:60]}...
                </div>
                """, unsafe_allow_html=True)
            if st.button("Continue Chatting"):
                st.switch_page("pages/1_AI_Tutor.py")
        else:
             st.info("No questions asked yet.")
    else:
        st.info("No doubts asked yet.")
        st.markdown("[👉 Start Chatting](pages/1_AI_Tutor.py)")

# ---------------- Footer / Goals ----------------
st.markdown("---")
st.subheader("🏆 Your Weekly Goals")

col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    st.checkbox("Solve 5 Past Papers", value=False)
with col_g2:
    st.checkbox("Complete 10 tasks", value=(stats['completed_todos'] >= 10), disabled=True)
with col_g3:
    st.checkbox("Create 3 Audio Summaries", value=(stats['audio_generated'] >= 3), disabled=True)
