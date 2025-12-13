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
# We try to load persistent stats if the user is logged in
def load_user_stats(email):
    # In a real app, this would be a database call. 
    # For now, we mock it or rely on session state availability.
    # We will prioritize what is currently in the active session.
    return {
        "doubts_solved": len([m for m in st.session_state.get("messages", []) if m["role"] == "user"]),
        "plans_created": 1 if st.session_state.get("session_plan_meta") else 0,
        "audio_generated": 1 if st.session_state.get("podcast_script") else 0,
        "streak": 3 # Mock streak for motivation
    }

# ---------------- User State ----------------
user_email = st.session_state.get("user_email", "Guest")
stats = load_user_stats(user_email)

# ---------------- Top Metrics Row ----------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="🔥 Study Streak", value=f"{stats['streak']} Days")

with col2:
    st.metric(label="💬 Doubts Asked", value=stats['doubts_solved'], delta="AI Tutor")

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
        exam_date = datetime.datetime.strptime(plan_meta['exam_date'], "%Y-%m-%d").date()
        days_left = (exam_date - datetime.date.today()).days
        
        # Progress Bar Logic
        total_duration = plan_meta.get('days_left', 30) # Default to 30 if missing
        progress = max(0.0, min(1.0, (total_duration - days_left) / total_duration)) if total_duration > 0 else 0
        
        st.info(f"**Focus:** {', '.join(plan_meta.get('focus_areas', ['General']))}")
        st.progress(progress, text=f"{days_left} days remaining until Exams")
        
        # Mini Calendar View of upcoming tasks
        if "session_plan_days" in st.session_state:
            days_data = st.session_state["session_plan_days"]
            # Convert to DataFrame for display
            df = pd.DataFrame(days_data)
            if not df.empty:
                # Show next 3 tasks
                st.write("**Up Next:**")
                st.dataframe(
                    df[["date", "topic", "activity"]].head(3),
                    hide_index=True,
                    use_container_width=True
                )
    else:
        st.warning("⚠️ No active study plan found.")
        st.markdown("[👉 Create a Study Plan](Study_Planner)")

    st.markdown("---")

    # 2. Activity Chart (Mock Data for Visual)
    st.subheader("📈 Productivity Trends")
    chart_data = pd.DataFrame({
        'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'Hours Studied': [2, 3, 4, 2, 5, 6, 4],
        'Doubts Solved': [1, 5, 2, 0, 3, 8, 2]
    })
    st.line_chart(chart_data.set_index('Day'))

# === RIGHT COLUMN: Quick Actions & History ===
with grid_col2:
    # 3. AI Tutor Recent Context
    st.subheader("🤖 Recent Doubts")
    messages = st.session_state.get("messages", [])
    if messages:
        # Get last 3 user messages
        user_msgs = [m['text'] for m in messages if m['role'] == 'user'][-3:]
        for msg in reversed(user_msgs):
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 0.9em;">
                ❓ {msg[:60]}...
            </div>
            """, unsafe_allow_html=True)
        st.caption(f"Total conversation depth: {len(messages)} messages")
        if st.button("Continue Chatting"):
            st.switch_page("pages/2_NexStudy.py")
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
