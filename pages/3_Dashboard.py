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
if os.path.exists("assets/image.png"):
    st.image("assets/image.png", width=150)
elif os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("📊 Personal Performance Dashboard")
st.caption("Track your learning progress across NexStudy tools.")

# ---------------- Helper: Update Database ----------------
def update_profile_db(user_id, updates):
    """Updates the user's profile in Supabase."""
    if not supabase: return
    try:
        supabase.table("profiles").update(updates).eq("id", user_id).execute()
    except Exception as e:
        # st.error(f"Failed to sync data: {e}")
        pass

# ---------------- Helper: Load Stats ----------------
def load_user_data(user):
    """
    Loads stats and todos.
    If Logged In -> Fetch from Supabase 'profiles' table.
    If Guest -> Fetch from Session State.
    """
    # Default structure
    data = {
        "doubts_solved": 0,
        "plans_created": 0,
        "audio_generated": 0,
        "streak": 0,
        "todos": []
    }

    # 1. GUEST MODE (Session State)
    if not user:
        msgs = st.session_state.get("messages", [])
        data["doubts_solved"] = len([m for m in msgs if m["role"] == "user"])
        data["plans_created"] = 1 if st.session_state.get("session_plan_meta") else 0
        data["audio_generated"] = 1 if st.session_state.get("podcast_script") else 0
        
        # Streak logic for guest (Session based)
        activity_count = data["doubts_solved"] + data["plans_created"] + data["audio_generated"]
        data["streak"] = 1 if activity_count > 0 else 0
        
        # Load guest todos
        data["todos"] = st.session_state.get("todos", [])
        return data

    # 2. LOGGED IN MODE (Supabase)
    if user and supabase:
        try:
            # Fetch profile data using the User ID
            res = supabase.table("profiles").select("*").eq("id", user["id"]).single().execute()
            if res.data:
                profile = res.data
                # Use .get() with defaults to avoid errors if columns are missing
                data["doubts_solved"] = profile.get("doubts_solved", 0) or 0
                data["plans_created"] = profile.get("plans_created", 0) or 0
                data["audio_generated"] = profile.get("audio_generated", 0) or 0
                data["streak"] = profile.get("streak", 0) or 0
                data["todos"] = profile.get("todos", []) or []
        except Exception:
            # If profile doesn't exist yet or fetch fails, stick to defaults
            pass
            
    return data

# ---------------- User State & Data Loading ----------------
user = st.session_state.get("user")
user_data = load_user_data(user)

# To-Do calculations
todos = user_data["todos"]
pending_todos = len([t for t in todos if not t["done"]])
completed_todos = len([t for t in todos if t["done"]])

# Display User Name
if user:
    # Try to get username from profile if available, else email
    username = "User"
    if st.session_state.get("profile") and st.session_state.profile.get("username"):
        username = st.session_state.profile["username"]
    elif user.get("email"):
        username = user.get("email").split("@")[0]
        
    st.subheader(f"Welcome back, {username} 👋")
else:
    st.subheader("Welcome, Guest 👋")

# ---------------- Top Metrics Row ----------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="🔥 Streak", value=f"{user_data['streak']} Days")

with col2:
    st.metric(label="💬 Doubts", value=user_data['doubts_solved'], delta="Total")

with col3:
    st.metric(label="📅 Plans", value=user_data['plans_created'], delta="Created")

with col4:
    st.metric(label="🎧 Audio", value=user_data['audio_generated'], delta="Generated")

with col5:
    st.metric(label="✅ To-Dos", value=f"{completed_todos}/{len(todos)}", delta=f"{pending_todos} Left")

st.markdown("---")

# ---------------- Main Dashboard Grid ----------------
grid_col1, grid_col2 = st.columns([2, 1])

# === LEFT COLUMN: Productivity Chart ===
with grid_col1:
    st.subheader("📈 Productivity Trends")
    
    # Initialize empty data for the week
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    doubts_data = [0] * 7
    hours_data = [0] * 7
    
    # Update "Today's" data point with current stats
    # (In a real app, you'd store daily logs. Here we show total for today to simulate activity)
    today_index = datetime.datetime.today().weekday()
    doubts_data[today_index] = user_data['doubts_solved']
    
    # Calculate simple activity score
    activity_score = (user_data['plans_created'] * 2) + (user_data['audio_generated'] * 2) + (completed_todos * 1) + (user_data['doubts_solved'] * 0.5)
    hours_data[today_index] = activity_score

    chart_data = pd.DataFrame({
        'Day': days,
        'Doubts Solved': doubts_data,
        'Activity Score': hours_data
    })
    
    st.line_chart(chart_data.set_index('Day'))
    
    if not user:
        st.caption("👀 You are viewing **Guest Data**. Sign in to save your history permanently.")

# === RIGHT COLUMN: Quick Actions & To-Do List ===
with grid_col2:
    # 3. Pending Tasks
    st.subheader("📝 Pending Tasks")
    
    # Input for new task
    new_task = st.text_input("Add a new task:", placeholder="e.g. Read Chapter 4", key="new_task_input")
    if st.button("Add Task"):
        if new_task:
            updated_todos = user_data["todos"] + [{"task": new_task, "done": False}]
            
            if user:
                update_profile_db(user["id"], {"todos": updated_todos})
                st.success("Task saved to cloud!")
                st.rerun()
            else:
                st.session_state.todos = updated_todos # Save to session for guest
                st.rerun()

    # Display List
    if pending_todos > 0:
        for idx, t in enumerate(user_data["todos"]):
            if not t["done"]:
                c1, c2 = st.columns([0.8, 0.2])
                with c1:
                    st.write(f"⬜ {t['task']}")
                with c2:
                    if st.button("✅", key=f"done_{idx}"):
                        # Mark as done
                        user_data["todos"][idx]["done"] = True
                        if user:
                            update_profile_db(user["id"], {"todos": user_data["todos"]})
                        else:
                            st.session_state.todos = user_data["todos"]
                        st.rerun()
    else:
        st.info("No pending tasks! Great job.")

    if st.button("View Completed Tasks"):
        with st.expander("Completed History"):
            for t in user_data["todos"]:
                if t["done"]:
                    st.write(f"✅ ~~{t['task']}~~")

    st.markdown("---")

    # 4. AI Tutor Recent Context
    st.subheader("🤖 Recent Session Chat")
    messages = st.session_state.get("messages", [])
    if messages:
        # Get last 2 user messages
        user_msgs = [m['text'] for m in messages if m['role'] == 'user'][-2:]
        if user_msgs:
            for msg in reversed(user_msgs):
                st.markdown(f"❓ *{msg[:40]}...*")
            
            if st.button("Continue Chatting"):
                st.switch_page("pages/2_NexStudy.py")
        else:
            st.info("No questions asked in this session.")
    else:
        st.markdown("[👉 Start Chatting](pages/2_NexStudy.py)")

# ---------------- Footer / Goals ----------------
st.markdown("---")
st.subheader("🏆 Weekly Goals")

col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    st.checkbox("Solve 5 Past Papers", value=(user_data['doubts_solved'] >= 5), disabled=True)
with col_g2:
    st.checkbox("Complete 10 tasks", value=(completed_todos >= 10), disabled=True)
with col_g3:
    st.checkbox("Create 3 Audio Summaries", value=(user_data['audio_generated'] >= 3), disabled=True)
