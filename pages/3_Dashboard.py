import streamlit as st
import pandas as pd
import datetime
import os
import json

# ---------------- Page Config ----------------
st.set_page_config(page_title="My Dashboard", page_icon="📊", layout="wide")
st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)

# ---------------- Logo Logic ----------------
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)
elif os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=150)

st.title("📊 Personal Performance Dashboard")
st.caption("Track your learning progress across NexStudy tools.")

# ---------------- Helper: Load Stats ----------------
def load_user_stats(email):
    # In a real app with a database, we would load historical data here.
    # For now, we calculate stats from the CURRENT active session.
    
    # Count user messages in chat
    msgs = st.session_state.get("messages", [])
    doubts_count = len([m for m in msgs if m["role"] == "user"])
    
    # Check if other features were used
    has_plan = 1 if st.session_state.get("session_plan_meta") else 0
    has_audio = 1 if st.session_state.get("podcast_script") else 0
    
    # Streak logic (Mock for guest, or calculate real for DB)
    streak = 1 if (doubts_count + has_plan + has_audio) > 0 else 0
    
    return {
        "doubts_solved": doubts_count,
        "plans_created": has_plan,
        "audio_generated": has_audio,
        "streak": streak
    }

# ---------------- User State ----------------
user_email = st.session_state.get("user_email")
display_user = user_email if user_email else "Guest"
stats = load_user_stats(display_user)

# ---------------- Top Metrics Row ----------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="🔥 Current Streak", value=f"{stats['streak']} Days")

with col2:
    st.metric(label="💬 Doubts Asked", value=stats['doubts_solved'], delta="Session")

with col3:
    st.metric(label="📅 Active Plans", value=stats['plans_created'], delta="Planner")

with col4:
    st.metric(label="🎧 Audio Notes", value=stats['audio_generated'], delta="Podcaster")

st.markdown("---")

# ---------------- Main Dashboard Grid ----------------
grid_col1, grid_col2 = st.columns([2, 1])

# === LEFT COLUMN: Deep Insights ===
with grid_col1:
    # 1. Study Planner Tracking
    st.subheader("📅 Exam Countdown & Plan")
    plan_meta = st.session_state.get("session_plan_meta")
    
    if plan_meta:
        try:
            exam_date = datetime.datetime.strptime(plan_meta['exam_date'], "%Y-%m-%d").date()
            days_left = (exam_date - datetime.date.today()).days
            
            # Progress Bar Logic
            total_duration = plan_meta.get('days_left', 30) # Default to 30 if missing
            if total_duration <= 0: total_duration = 1
            progress = max(0.0, min(1.0, (total_duration - days_left) / total_duration))
            
            st.info(f"**Focus:** {', '.join(plan_meta.get('focus_areas', ['General']))}")
            st.progress(progress, text=f"{days_left} days remaining until Exams")
            
            # Mini Calendar View of upcoming tasks
            if "session_plan_days" in st.session_state:
                days_data = st.session_state["session_plan_days"]
                df = pd.DataFrame(days_data)
                if not df.empty:
                    st.write("**Up Next:**")
                    st.dataframe(
                        df[["date", "topic", "activity"]].head(3),
                        hide_index=True,
                        use_container_width=True
                    )
        except Exception as e:
            st.error("Error reading plan data. Try regenerating your plan.")
    else:
        st.warning("⚠️ No active study plan found.")
        st.markdown("[👉 Create a Study Plan](Study_Planner)")

    st.markdown("---")

    # 2. Activity Chart (REAL-TIME SESSION DATA)
    st.subheader("📈 Productivity Trends")
    
    # Initialize empty data for the week
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    doubts_data = [0] * 7
    hours_data = [0] * 7
    
    # Update "Today's" data point with current session stats
    today_index = datetime.datetime.today().weekday() # 0 is Monday, 6 is Sunday
    doubts_data[today_index] = stats['doubts_solved']
    # We assume roughly 15 mins per doubt or track simple activity for demo
    hours_data[today_index] = stats['plans_created'] * 1 + stats['audio_generated'] * 0.5 

    chart_data = pd.DataFrame({
        'Day': days,
        'Doubts Solved': doubts_data,
        'Activity Score': hours_data
    })
    
    st.line_chart(chart_data.set_index('Day'))
    
    if not user_email:
        st.caption("👀 You are viewing **Guest Data** (Current Session Only). Sign in to save history.")

# === RIGHT COLUMN: Quick Actions & History ===
with grid_col2:
    # 3. AI Tutor Recent Context
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
            st.caption(f"Total conversation depth: {len(messages)} messages")
            if st.button("Continue Chatting"):
                st.switch_page("pages/2_NexStudy.py")
        else:
             st.info("No questions asked yet.")
    else:
        st.info("No doubts asked yet.")
        st.markdown("[👉 Start Chatting](NexStudy)")

    st.markdown("---")

    # 4. Audio Notes Status
    st.subheader("🎧 Last Audio Note")
    if st.session_state.get("audio_file_path"):
        st.success("Ready to play")
        st.audio(st.session_state["audio_file_path"])
        with st.expander("View Script Snippet"):
            st.write(st.session_state.get("podcast_script", "")[:200] + "...")
    else:
        st.info("No audio generated this session.")
        st.markdown("[👉 Create Audio Note](Audio_Notes)")

# ---------------- Footer / Goals ----------------
st.markdown("---")
st.subheader("🏆 Your Weekly Goals")

col_g1, col_g2, col_g3 = st.columns(3)
with col_g1:
    st.checkbox("Solve 5 Past Papers", value=False)
with col_g2:
    st.checkbox("Complete 10 hours study", value=True, disabled=True)
with col_g3:
    st.checkbox("Create 3 Audio Summaries", value=False)
