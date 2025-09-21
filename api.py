import os
import re
import sqlite3
from datetime import date

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import hashlib
from database import get_conn, create_user, get_user, init_db

API_BASE = "http://127.0.0.1:8000"

# Initialize the database on startup
init_db()

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
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,.1);
        padding: 25px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,.37);
    }
    .header { font-size: 2.5rem; font-weight: 700; text-align: center; color: #fff; text-shadow: 2px 2px 8px rgba(0,0,0,.3); }
    .card h3 { color: #fff; border-bottom: 2px solid #0891b2; padding-bottom: 10px; margin-top: 0; }
    [data-testid="stSidebar"] { background-color: #111827; }
    .stButton>button{
        background-color:#0891b2;color:#fff;font-weight:600;border:none;border-radius:8px;padding:12px 24px;
        transition:transform .2s ease, box-shadow .2s ease; box-shadow:0 4px 15px rgba(0,0,0,.2);
    }
    .stButton>button:hover{ transform:translateY(-3px); box-shadow:0 6px 20px rgba(8,145,178,.5); }
    .stButton>button:active{ transform:translateY(-1px); }
    .stTextInput>div>div>input, .stSelectbox>div>div{ background-color:rgba(17,24,39,.8); color:#e5e7eb; border-radius:8px; }
    [data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.app_state = "main"

def main_page():
    st.markdown('<div class="header">INNOMATICS RESEARCH LABS</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Welcome")
    
    st.markdown("Please choose an option to continue:")
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
        
    st.markdown("</div>", unsafe_allow_html=True)


def login_page():
    st.markdown('<div class="header">INNOMATICS RESEARCH LABS</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Welcome Back")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    initial_role = st.session_state.get("pre_filled_role", "student")
    role = st.selectbox("Role", ["student", "admin"], index=["student", "admin"].index(initial_role))
    
    if st.button("Login"):
        if not username.strip() or not password.strip():
            st.warning("Please enter both username and password.")
        elif role == "admin":
            if username == "admin" and password == "admin123":
                st.session_state.user = username
                st.session_state.role = role
                st.session_state.app_state = "admin"
                st.rerun()
            else:
                st.error("Invalid admin credentials.")
        elif role == "student":
            user = get_user(username, password)
            if user:
                st.session_state.user = user[1] # username
                st.session_state.role = role
                st.session_state.app_state = "student"
                st.rerun()
            else:
                st.error("Invalid student credentials.")
                
    st.markdown("</div>", unsafe_allow_html=True)


def signup_page():
    st.markdown('<div class="header">INNOMATICS RESEARCH LABS</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Student Sign Up")
    
    student_name = st.text_input("Full Name", placeholder="Enter your full name")
    student_email = st.text_input("Email", placeholder="Enter your email")
    student_password = st.text_input("Password", type="password", placeholder="Choose a password")

    if st.button("Sign Up"):
        if not student_name.strip() or not student_email.strip() or not student_password.strip():
            st.warning("Please fill out all fields.")
        elif "@" not in student_email:
            st.warning("Please enter a valid email address.")
        else:
            if create_user(student_name, student_email, student_password):
                st.session_state.user = student_name
                st.session_state.role = "student"
                st.session_state.app_state = "student"
                st.success(f"✅ Sign up successful! Welcome, {st.session_state.user}!")
                st.rerun()
            else:
                st.error("Username already exists. Please choose a different one.")
                
    st.markdown("</div>", unsafe_allow_html=True)


def student_page():
    st.markdown('<div class="header">THE VIRTUAL HR</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"### Welcome, **{st.session_state.user}** 👋")
    if st.sidebar.button("Logout"):
        st.session_state.user, st.session_state.role = None, None
        st.session_state.app_state = "main"
        st.rerun()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h3>Available Job Openings</h3>", unsafe_allow_html=True)

    conn = sqlite3.connect("outputs/resume_system.db")
    jds = pd.read_sql_query(
        "SELECT role, jd_file, created_at FROM jobs ORDER BY datetime(created_at) DESC",
        conn,
    )
    conn.close()

    if jds.empty:
        st.info("No Job Descriptions have been posted yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    jds = jds.drop_duplicates(subset=["role", "jd_file"]).reset_index(drop=True)
    
    roles = jds['role'].tolist()
    roles.insert(0, "Select a job opening...")
    
    selected_role = st.selectbox("Choose a job opening from the list below:", roles)

    if selected_role != "Select a job opening...":
        job_details = jds[jds['role'] == selected_role].iloc[0]
        role = str(job_details.role)
        jd_file = str(job_details.jd_file)
        created_at = str(job_details.created_at)
        uid = hashlib.md5(f"{role}|{jd_file}|{created_at}".encode()).hexdigest()[:10]

        st.markdown(f"### Details for: **{role}**")
        st.markdown(f"📄 **Job Description File:** `{jd_file}`")
        
        jd_path = os.path.join("data", "jds", jd_file)
        if os.path.exists(jd_path):
            with open(jd_path, "rb") as fh:
                st.download_button(
                    label="Download JD",
                    data=fh.read(),
                    file_name=jd_file,
                    mime="application/octet-stream",
                    key=f"dl_{uid}",
                )
        else:
            st.caption("JD file not found on server (ask admin to re-upload).")

        st.markdown("---")

        st.markdown("### Apply for this position")
        uploaded = st.file_uploader(
            f"Upload your resume:",
            type=["pdf", "docx", "txt"],
            key=f"file_{uid}",
        )

        if st.button(f"Submit Application", key=f"btn_{uid}"):
            if not uploaded:
                st.warning("Please upload a resume before submitting.")
            else:
                files = {"file": (uploaded.name, uploaded.getvalue())}
                data = {"student_name": st.session_state.user, "jd_file": jd_file}
                try:
                    with st.spinner("Analyzing your resume..."):
                        resp = requests.post(
                            f"{API_BASE}/upload_resume",
                            data=data,
                            files=files,
                            timeout=120,
                        )
                    
                    if resp.ok:
                        analysis_data = resp.json()
                        score = analysis_data['score']
                        missing = analysis_data['missing']

                        st.success(f"✅ Application submitted for **{role}**!")
                        if score >= 75:
                            st.balloons()
                        
                        st.markdown("---")
                        st.markdown(f"### Application Analysis for {role}")
                        
                        if score >= 75:
                            st.success("🎉 **Congratulations! You have been shortlisted!**")
                            st.markdown("Please check your email for further information.")
                        else:
                            st.error("😔 **Sorry, you were not selected for this position.**")
                            st.markdown("Please review the feedback below to improve your skills and qualifications.")
                        
                        st.markdown("---")
                        st.markdown("#### Missing Qualifications and Skills")
                        
                        if missing and missing.get('skills'):
                            st.markdown("**Skills:**")
                            for skill in missing['skills']:
                                st.markdown(f"- {skill.replace('_', ' ').title()}")
                        
                        if missing and missing.get('certifications'):
                            st.markdown("<br>**Certifications:**")
                            for cert in missing['certifications']:
                                st.markdown(f"- {cert.replace('_', ' ').title()}")

                        if missing and missing.get('projects'):
                            st.markdown("<br>**Projects:**")
                            for project in missing['projects']:
                                st.markdown(f"- {project.replace('_', ' ').title()}")
                        
                        if not any(missing.values()):
                             st.info("No missing skills, certifications, or projects were identified.")

                        st.markdown(f'<br>Interested in improving your skills? Check out <a href="https://www.innomatics.in/" target="_blank">Innomatics Research Labs</a>.', unsafe_allow_html=True)


                    else:
                        st.error(f"Submission failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


def admin_page():
    st.markdown('<div class="header">Admin Dashboard</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"### Welcome, **{st.session_state.user}** 👋")
    if st.sidebar.button("Logout"):
        st.session_state.user, st.session_state.role = None, None
        st.session_state.app_state = "main"
        st.rerun()

    if st.sidebar.button("Post New Job Description"):
        st.session_state.app_state = "post_jd"
        st.rerun()

    db_path = "outputs/resume_system.db"
    if not os.path.exists(db_path):
        st.error("Database file not found. Make sure the API is running.")
        return

    conn = sqlite3.connect(db_path)
    resumes_df = pd.read_sql_query(
        "SELECT student_name, file_path, relevance_score, verdict, created_at FROM resumes",
        conn,
    )
    jds_df = pd.read_sql_query(
        "SELECT jd_file, role, created_at FROM jobs",
        conn,
    )
    conn.close()

    if not resumes_df.empty:
        resumes_df["created_at"] = pd.to_datetime(resumes_df["created_at"], errors="coerce")
        resumes_df["relevance_score"] = pd.to_numeric(resumes_df["relevance_score"], errors="coerce")
    if not jds_df.empty:
        jds_df["created_at"] = pd.to_datetime(jds_df["created_at"], errors="coerce")

    today = date.today()
    jd_today = int((jds_df["created_at"].dt.date == today).sum()) if not jds_df.empty else 0
    jd_total = len(jds_df)

    resumes_today_df = resumes_df[resumes_df["created_at"].dt.date == today] if not resumes_df.empty else pd.DataFrame()
    resumes_today_count = len(resumes_today_df)
    resumes_total = len(resumes_df)

    avg_score_today = float(resumes_today_df["relevance_score"].mean()) if not resumes_today_df.empty else 0.0
    avg_score_total = float(resumes_df["relevance_score"].mean()) if not resumes_df.empty else 0.0

    st.markdown('<div class="card"><h3>Today\'s Activity</h3></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("JDs Uploaded Today", jd_today, delta=f"Total: {jd_total}")
    col2.metric("Resumes Submitted Today", resumes_today_count, delta=f"Total: {resumes_total}")
    col3.metric("Average Score Today", f"{avg_score_today:.2f}%", delta=f"Overall: {avg_score_total:.2f}%")

    if not resumes_df.empty:
        st.markdown('<div class="card"><h3>🏆 Top 5 Resumes by Score</h3></div>', unsafe_allow_html=True)
        top5 = resumes_df.nlargest(5, "relevance_score").copy()
        top5["Resume"] = top5["file_path"].apply(os.path.basename)

        fig = px.pie(
            top5,
            names="Resume",
            values="relevance_score",
            title="Score Distribution of Top 5 Candidates",
            hole=0.4,
        )
        fig.update_traces(
            textinfo="percent+label",
            pull=[0.05] + [0] * max(0, len(top5) - 1),
            marker=dict(line=dict(color="#ffffff", width=2)),
            hovertemplate="<b>%{label}</b><br>Score: %{value:.2f}%<extra></extra>",
        )
        fig.update_layout(
            legend_title_text="Resume Files",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e5e7eb",
            hoverlabel=dict(bgcolor="#1f2937", font_size=16, bordercolor="rgba(255,255,255,.2)"),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="card"><h3>📋 All Resume Applications (Top 20)</h3></div>', unsafe_allow_html=True)
        display = resumes_df.head(20).rename(
            columns={
                "student_name": "Student",
                "file_path": "Resume Path",
                "relevance_score": "Score",
                "verdict": "Verdict",
                "created_at": "Submitted At",
            }
        )
        st.dataframe(display, use_container_width=True)
    else:
        st.info("No applications found in the database yet.")


def post_jd_page():
    st.markdown('<div class="header">Post New Job Description</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"### Welcome, **{st.session_state.user}** 👋")
    if st.sidebar.button("Logout"):
        st.session_state.user, st.session_state.role = None, None
        st.session_state.app_state = "main"
        st.rerun()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Upload a new Job Description")
    
    job_role = st.text_input("Job Title", placeholder="e.g., Data Scientist")
    uploaded_file = st.file_uploader("Upload Job Description File (PDF, DOCX)", type=["pdf", "docx"])
    
    if st.button("Post Job"):
        if not job_role.strip() or not uploaded_file:
            st.warning("Please provide a job title and upload a file.")
        else:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            data = {"role": job_role, "jd_file": uploaded_file.name}
            try:
                with st.spinner("Uploading Job Description..."):
                    resp = requests.post(f"{API_BASE}/upload_jd", data=data, files=files, timeout=120)
                
                if resp.ok:
                    st.success(f"✅ Job Description for '{job_role}' has been posted!")
                else:
                    st.error(f"Error posting job: {resp.text}")
            except Exception as e:
                st.error(f"Error connecting to API: {e}")

    if st.button("Back to Dashboard"):
        st.session_state.app_state = "admin"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)



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
