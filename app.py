import os
import re
import sqlite3
import hashlib
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_conn, create_user, get_user, init_db
from scoring import score_resume

init_db()
os.makedirs("data/jds", exist_ok=True)
os.makedirs("data/resumes", exist_ok=True)

st.set_page_config(page_title="INNOMATICS RESEARCH LABS – Resume Relevance", layout="wide")

st.markdown(
    """
    <style>
    .stExpander { margin-bottom: 0.75rem; }
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="st-"], [class*="css-"] { font-family: 'Poppins', sans-serif; }
    [data-testid="stAppViewContainer"] > .main {
        background-image: linear-gradient(120deg, #0f0c29, #302b63, #24243e);
        background-size: 200% 200%;
        animation: gradientAnimation 20s ease infinite;
        color: #e5e7eb;
    }
    @keyframes gradientAnimation { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .header, .card {
        background: rgba(31,41,55,.6);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,.1);
        padding: 25px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,.37);
    }
    .header { font-size: 2.5rem; font-weight: 700; text-align: center; color: #fff; }
    .card h3 { color: #fff; border-bottom: 2px solid #0891b2; padding-bottom: 10px; }
    [data-testid="stSidebar"] { background-color: #111827; }
    .stButton>button {
        background-color:#0891b2;color:#fff;font-weight:600;border:none;border-radius:8px;padding:12px 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.app_state = "main"

def process_jd_upload(role, file):
    save_path = os.path.join("data", "jds", file.name)
    with open(save_path, "wb") as f:
        f.write(file.getvalue())
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs(role, jd_file) VALUES(?, ?)", (role, file.name))
    conn.commit()
    conn.close()
    return {"message": "JD uploaded", "role": role, "jd_file": file.name}

def process_resume(student_name, jd_file, file):
    save_path = os.path.join("data", "resumes", file.name)
    with open(save_path, "wb") as f:
        f.write(file.getvalue())
    jd_path = os.path.join("data", "jds", jd_file)
    score, verdict, missing = score_resume(save_path, jd_path)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO resumes(student_name, file_path, jd_file, relevance_score, verdict) VALUES(?,?,?,?,?)",
        (student_name, save_path, jd_file, score, verdict),
    )
    conn.commit()
    conn.close()
    return {"score": score, "verdict": verdict, "missing": missing}

def main_page():
    st.markdown('<div class="header">INNOMATICS RESEARCH LABS</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">### Welcome</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    if col1.button("Sign In"):
        st.session_state.app_state = "login"
        st.session_state.pre_filled_role = "student"
        st.rerun()
    if col2.button("Sign Up"):
        st.session_state.app_state = "signup"
        st.rerun()
    if col3.button("Admin"):
        st.session_state.app_state = "login"
        st.session_state.pre_filled_role = "admin"
        st.rerun()

def login_page():
    st.markdown('<div class="header">Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["student", "admin"])
    if st.button("Login"):
        if role == "admin" and username == "admin" and password == "admin123":
            st.session_state.user = username
            st.session_state.role = role
            st.session_state.app_state = "admin"
            st.rerun()
        elif role == "student":
            user = get_user(username, password)
            if user:
                st.session_state.user = user[1]
                st.session_state.role = role
                st.session_state.app_state = "student"
                st.rerun()
            else:
                st.error("Invalid student credentials.")

def signup_page():
    st.markdown('<div class="header">Sign Up</div>', unsafe_allow_html=True)
    username = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        if create_user(username, email, password):
            st.session_state.user = username
            st.session_state.role = "student"
            st.session_state.app_state = "student"
            st.success("Sign up successful!")
            st.rerun()
        else:
            st.error("User already exists.")

def student_page():
    st.markdown('<div class="header">Student Portal</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** 👋")
    if st.sidebar.button("Logout"):
        st.session_state.user, st.session_state.role = None, None
        st.session_state.app_state = "main"
        st.rerun()
    conn = get_conn()
    jds = pd.read_sql_query("SELECT role, jd_file, created_at FROM jobs ORDER BY datetime(created_at) DESC", conn)
    conn.close()
    if jds.empty:
        st.info("No Job Descriptions posted yet.")
        return
    selected_role = st.selectbox("Choose a job:", jds["role"].tolist())
    jd_row = jds[jds["role"] == selected_role].iloc[0]
    jd_file = jd_row["jd_file"]
    st.write(f"📄 Job Description: {jd_file}")
    jd_path = os.path.join("data", "jds", jd_file)
    if os.path.exists(jd_path):
        with open(jd_path, "rb") as fh:
            st.download_button("Download JD", fh.read(), file_name=jd_file)
    uploaded = st.file_uploader("Upload your Resume", type=["pdf", "docx", "txt"])
    if st.button("Submit Application"):
        if uploaded:
            resp = process_resume(st.session_state.user, jd_file, uploaded)
            st.success(f"Application submitted! Verdict: {resp['verdict']} (Score: {resp['score']:.2f}%)")
        else:
            st.warning("Upload a resume before submitting.")

def admin_page():
    st.markdown('<div class="header">Admin Dashboard</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** 👋")
    if st.sidebar.button("Logout"):
        st.session_state.user, st.session_state.role = None, None
        st.session_state.app_state = "main"
        st.rerun()
    if st.sidebar.button("Post New JD"):
        st.session_state.app_state = "post_jd"
        st.rerun()
    conn = get_conn()
    resumes_df = pd.read_sql_query("SELECT student_name, file_path, jd_file, relevance_score, verdict, created_at FROM resumes", conn)
    jds_df = pd.read_sql_query("SELECT role, jd_file, created_at FROM jobs", conn)
    conn.close()
    st.metric("Total JDs", len(jds_df))
    st.metric("Total Resumes", len(resumes_df))
    if not resumes_df.empty:
        st.dataframe(resumes_df)

def post_jd_page():
    st.markdown('<div class="header">Post JD</div>', unsafe_allow_html=True)
    role = st.text_input("Job Title")
    uploaded_file = st.file_uploader("Upload JD", type=["pdf", "docx"])
    if st.button("Post Job"):
        if role and uploaded_file:
            process_jd_upload(role, uploaded_file)
            st.success(f"Job '{role}' posted successfully!")
        else:
            st.warning("Provide job title and file.")
    if st.button("Back"):
        st.session_state.app_state = "admin"
        st.rerun()

if st.session_state.user is None:
    if st.session_state.app_state == "signup":
        signup_page()
    elif st.session_state.app_state == "login":
        login_page()
    else:
        main_page()
else:
    if st.session_state.role == "student":
        student_page()
    elif st.session_state.role == "admin" and st.session_state.app_state == "post_jd":
        post_jd_page()
    else:
        admin_page()
