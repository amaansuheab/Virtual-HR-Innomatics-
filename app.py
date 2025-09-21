import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_conn
from scoring import score_resume
from pathlib import Path
import shutil
import sqlite3

app = FastAPI()
init_db()

# --- CORRECTED THIS SECTION ---
# Allow all origins for development/hackathon purposes
origins = ["*"] # Use a wildcard for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# -----------------------------

Path("data/resumes").mkdir(parents=True, exist_ok=True)
Path("data/jds").mkdir(parents=True, exist_ok=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload_jd")
def upload_jd(role: str = Form(...), file: UploadFile = File(...)):
    save_path = f"data/jds/{file.filename}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs(role, jd_file) VALUES(?, ?)", (role, file.filename))
    conn.commit()
    conn.close()
    return {"message": "JD uploaded", "role": role, "jd_file": file.filename}

@app.get("/jds")
def get_all_jds():
    conn = get_conn()
    jds = conn.execute("SELECT role, jd_file, created_at FROM jobs ORDER BY datetime(created_at) DESC").fetchall()
    conn.close()
    
    # Format the data into a list of dictionaries
    jds_list = [
        {"role": row[0], "jd_file": row[1], "created_at": row[2]}
        for row in jds
    ]
    return {"job_descriptions": jds_list}


@app.post("/upload_resume")
def upload_resume(student_name: str = Form(...), jd_file: str = Form(...), file: UploadFile = File(...)):
    save_path = f"data/resumes/{file.filename}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    jd_path = f"data/jds/{jd_file}"
    score, verdict, missing = score_resume(save_path, jd_path)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO resumes(student_name,file_path,jd_file,relevance_score,verdict) VALUES(?,?,?,?,?)",
                 (student_name, save_path, jd_file, score, verdict))
    conn.commit()
    conn.close()

    return {"score": score, "verdict": verdict, "missing": missing}
