import fitz  # PyMuPDF
import docx2txt
import spacy
import random
from sentence_transformers import SentenceTransformer, util
from spacy.lang.en.stop_words import STOP_WORDS

nlp = spacy.load("en_core_web_sm")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text(file_path):
    ext = file_path.lower()
    try:
        if ext.endswith(".pdf"):
            doc = fitz.open(file_path)
            return "\n".join([page.get_text() for page in doc])
        elif ext.endswith(".docx"):
            return docx2txt.process(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        return f"[ERROR] Could not extract text from {file_path}: {e}"

def score_resume(resume_path, jd_path):
    resume_text = extract_text(resume_path)
    jd_text = extract_text(jd_path)

    # Token-based hard match
    jd_doc = nlp(jd_text.lower())
    resume_doc = nlp(resume_text.lower())

    jd_tokens = {token.text for token in jd_doc if token.is_alpha and token.text not in STOP_WORDS}
    resume_tokens = {token.text for token in resume_doc if token.is_alpha and token.text not in STOP_WORDS}

    common_tokens = jd_tokens.intersection(resume_tokens)
    # Increased hard score weight
    hard_score_weight = 0.4
    hard_score = len(common_tokens) / max(len(jd_tokens), 1) * 100 * hard_score_weight

    # Semantic match
    resume_emb = embed_model.encode(resume_text, convert_to_tensor=True)
    jd_emb = embed_model.encode(jd_text, convert_to_tensor=True)
    # Increased semantic score weight
    sem_score_weight = 0.5
    sem_score = float(util.cos_sim(resume_emb, jd_emb)[0][0]) * 100 * sem_score_weight

    # Content bonus based on matched skills, certifications, and projects
    all_skills = {
        "python", "sql", "machine learning", "data analysis", "nlp", "power bi", "excel", "tableau",
        "tensorflow", "keras", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
        "r", "sas", "spss", "statistics", "feature engineering", "data visualization",
        "big data", "hadoop", "spark", "apache kafka", "aws", "azure", "gcp",
        "docker", "kubernetes", "git", "ci/cd", "agile", "scrum",
        "deep learning", "computer vision", "time series analysis", "natural language processing"
    }
    all_certifications = {
        "aws certified", "pmp", "scrum master", "cisco", "azure fundamentals", "google data analytics"
    }
    all_projects = {
        "sentiment analysis", "predictive modeling", "churn prediction", "stock price forecasting", "image classification"
    }

    # Count matched content items
    matched_skills = resume_tokens.intersection(all_skills)
    matched_certifications = resume_tokens.intersection(all_certifications)
    matched_projects = resume_tokens.intersection(all_projects)
    
    # Calculate a bonus score for content matches
    content_bonus_weight = 0.3
    content_bonus = (len(matched_skills) / max(len(all_skills), 1) + len(matched_certifications) / max(len(all_certifications), 1) + len(matched_projects) / max(len(all_projects), 1)) / 3 * 100 * content_bonus_weight

    # Adjusted total score formula for a higher baseline
    total_score = min(hard_score + sem_score + content_bonus, 100.0)

    # Adjusted thresholds to be more lenient
    if total_score >= 30:
        verdict = "Strong Match"
    elif total_score >= 22:
        verdict = "Moderate Match"
    else:
        verdict = "Weak Match"

    # Compile the categorized missing items
    missing_keywords = jd_tokens - resume_tokens

    missing_skills = list(missing_keywords.intersection(all_skills))
    missing_certifications = list(missing_keywords.intersection(all_certifications))
    missing_projects = list(missing_keywords.intersection(all_projects))

    num_skills_to_show = min(max(5, len(missing_skills)), len(missing_skills))
    selected_skills = random.sample(missing_skills, num_skills_to_show)

    return total_score, verdict, {
        "skills": selected_skills,
        "certifications": missing_certifications,
        "projects": missing_projects
    }
