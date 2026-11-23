import streamlit as st
import libsql
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Turso Cloud Persistence Test", layout="centered")

# 1. Connect to Turso using embedded replica + sync_url
@st.cache_resource
def get_db_connection():
    # Ensure URL uses libsql:// scheme
    db_url = st.secrets["TURSO_DATABASE_URL"].strip().replace("https://", "libsql://")
    auth_token = st.secrets["TURSO_AUTH_TOKEN"].strip()
    
    conn = libsql.connect(
        "turso_local.db",
        sync_url=db_url,
        auth_token=auth_token
    )
    conn.sync()
    return conn

try:
    conn = get_db_connection()
    cur = conn.cursor()

    # 2. Create table in Turso if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS event_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT NOT NULL,
            student_name TEXT NOT NULL,
            fee_paid REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.sync()
except Exception as e:
    st.error(f"Database connection/setup failed: {e}")
    st.stop()

st.title("Student Event Registration (Turso Persistent DB)")

# 3. Form to insert new record
with st.form("reg_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    reg_no = col1.text_input("Register Number", placeholder="e.g., 24BCAR0101")
    student_name = col2.text_input("Student Name", placeholder="e.g., Rahul Sharma")
    fee_paid = st.number_input("Fee Amount (₹)", min_value=0, value=250, step=50)
    submitted = st.form_submit_button("Save Permanently to Cloud")

    if submitted:
        if reg_no.strip() and student_name.strip():
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO event_registrations (reg_no, student_name, fee_paid, created_at) VALUES (?, ?, ?, ?)",
                (reg_no.strip().upper(), student_name.strip(), fee_paid, now_str)
            )
            conn.commit()
            conn.sync()  # Pushes the write to Turso Cloud immediately
            st.success(f"Saved {student_name} ({reg_no.upper()}) to Turso!")
        else:
            st.warning("Please enter both Register Number and Student Name.")

st.divider()

# 4. Read and display live data from Turso
st.subheader("Stored Records in Turso")
conn.sync()  # Ensures latest cloud rows are pulled
cur = conn.cursor()
cur.execute("SELECT id, reg_no, student_name, fee_paid, created_at FROM event_registrations ORDER BY id DESC")
rows = cur.fetchall()

if rows:
    df = pd.DataFrame(rows, columns=["ID", "Register No", "Student Name", "Fee (₹)", "Timestamp"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    del_id = st.number_input("Enter ID to delete", min_value=1, step=1)
    if st.button("Delete Record"):
        cur = conn.cursor()
        cur.execute("DELETE FROM event_registrations WHERE id = ?", (del_id,))
        conn.commit()
        conn.sync()
        st.rerun()
else:
    st.info("No records found yet. Add a student above to test.")
