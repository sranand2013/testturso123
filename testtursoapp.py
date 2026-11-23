import streamlit as st
import libsql_experimental as libsql
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Turso Cloud Persistence Test", layout="centered")

# 1. Connect directly to Turso Cloud SQLite
@st.cache_resource
def get_db_connection():
    return libsql.connect(
        database=st.secrets["TURSO_DATABASE_URL"],
        auth_token=st.secrets["TURSO_AUTH_TOKEN"]
    )

conn = get_db_connection()

# 2. Create table in Turso if it doesn't exist
conn.execute("""
    CREATE TABLE IF NOT EXISTS event_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT NOT NULL,
        student_name TEXT NOT NULL,
        fee_paid REAL NOT NULL,
        created_at TEXT NOT NULL
    )
""")
conn.commit()

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
            conn.execute(
                "INSERT INTO event_registrations (reg_no, student_name, fee_paid, created_at) VALUES (?, ?, ?, ?)",
                (reg_no.strip().upper(), student_name.strip(), fee_paid, now_str)
            )
            conn.commit()
            st.success(f"Saved {student_name} ({reg_no.upper()}) to Turso!")
        else:
            st.warning("Please enter both Register Number and Student Name.")

st.divider()

# 4. Read and display live data from Turso
st.subheader("Stored Records in Turso")
cursor = conn.execute("SELECT id, reg_no, student_name, fee_paid, created_at FROM event_registrations ORDER BY id DESC")
rows = cursor.fetchall()

if rows:
    df = pd.DataFrame(rows, columns=["ID", "Register No", "Student Name", "Fee (₹)", "Timestamp"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Optional delete test
    del_id = st.number_input("Enter ID to delete", min_value=1, step=1)
    if st.button("Delete Record"):
        conn.execute("DELETE FROM event_registrations WHERE id = ?", (del_id,))
        conn.commit()
        st.rerun()
else:
    st.info("No records found yet. Add a student above to test.")
