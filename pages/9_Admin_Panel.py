import streamlit as st
import pandas as pd
import datetime

# ---------------- Page Config ----------------
st.set_page_config(page_title="Admin Panel", page_icon="🔐", layout="wide")

st.title("🔐 Admin Panel")

# ---------------- Password Protection ----------------
# Change "admin123" to a stronger password!
password = st.text_input("Enter Admin Password", type="password")

if password != "admin123":
    st.error("Access Denied")
    st.stop()

st.success("Access Granted")

# ---------------- Load Data from Firestore ----------------
def get_all_users():
    try:
        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore

        # Initialize if not already done (same as main_app)
        if not firebase_admin._apps:
            key_dict = dict(st.secrets["firebase_key"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        
        # Fetch all documents in 'users' collection
        users_ref = db.collection("users")
        docs = users_ref.stream()
        
        users_data = []
        for doc in docs:
            data = doc.to_dict()
            users_data.append(data)
            
        return users_data
    except Exception as e:
        st.error(f"Database Error: {e}")
        return []

if st.button("🔄 Refresh User List"):
    users = get_all_users()
    
    if users:
        st.metric("Total Users", len(users))
        
        # Convert to DataFrame for nice table
        df = pd.DataFrame(users)
        
        # Format columns if they exist
        if "last_login" in df.columns:
            df["last_login"] = pd.to_datetime(df["last_login"]).dt.strftime('%Y-%m-%d %H:%M:%S')
            
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users found in database yet.")
