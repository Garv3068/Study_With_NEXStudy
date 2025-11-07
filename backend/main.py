import streamlit as st
import random
from datetime import date

# --- Motivational Quote Section ---
quotes = [
    "Push yourself, because no one else is going to do it for you.",
    "Success doesn’t just find you. You have to go out and get it.",
    "Dream bigger. Do bigger.",
    "Wake up with determination. Go to bed with satisfaction."
]
def get_daily_quote():
    random.seed(date.today().toordinal())
    return random.choice(quotes)

st.title("🌟 EduNex – Your AI Study Helper")
st.subheader("💬 Daily Motivation")
st.success(get_daily_quote())

# --- Mnemonic Generator Section ---
st.divider()
st.subheader("🧠 Mnemonic Generator")

topic = st.text_input("Enter a topic or concept:")
if st.button("Generate Mnemonic"):
    if topic.strip() == "":
        st.warning("Please enter a topic first.")
    else:
        words = topic.upper().split()
        letters = [w[0] for w in words]
        mnemonic = " ".join(letters)
        # Simple random phrase builder
        sample_words = ["Memory", "Note", "Idea", "Concept", "Habit", "Understand", "Master"]
        phrase = " - ".join(random.sample(sample_words, min(len(letters), len(sample_words))))
        st.info(f"**Mnemonic:** {mnemonic}")
        st.write(f"💡 Try remembering it as: {phrase}")
