import streamlit as st
import random

st.title("💡 Smart Study Tips")
# st.set_page_config(page_title="Study Tips", page_icon="💡", layout="wide")
# st.markdown("<style>footer{visibility:hidden;} </style>", unsafe_allow_html=True)


tips = [
    "Break your study sessions into 25-minute chunks (Pomodoro).",
    "Explain a topic aloud — if you can teach it, you truly understand it.",
    "Revise difficult topics first when your mind is fresh.",
    "Make digital flashcards for quick daily revision.",
    "Avoid multitasking — deep focus for short intervals is more effective.",
    "Sleep well. Retention improves drastically with rest.",
    "After studying, write a one-line summary for every concept you learned.",
    "Use AI tools like NexStudy to summarize, quiz, and review efficiently!"
]

if st.button("Generate a Study Tip"):
    st.success(random.choice(tips))
else:
    st.info("Click the button for a helpful tip to boost your learning!")
