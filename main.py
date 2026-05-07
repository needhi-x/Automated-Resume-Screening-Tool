import os
import re
import pandas as pd
import pdfplumber
import docx
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -------------------------------
# TEXT CLEANING
# -------------------------------
def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# -------------------------------
# PDF TEXT EXTRACTION
# -------------------------------
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        print(f"❌ Error reading PDF: {file_path}")
    return text


# -------------------------------
# DOCX TEXT EXTRACTION
# -------------------------------
def extract_text_from_docx(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except:
        print(f"❌ Error reading DOCX: {file_path}")
    return text


# -------------------------------
# FILE HANDLER
# -------------------------------
def extract_resume_text(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    return ""


# -------------------------------
# MATCHED SKILLS
# -------------------------------
def get_top_keywords(job_desc, resume, top_n=5):
    job_words = set(job_desc.split())
    resume_words = set(resume.split())
    matched = job_words.intersection(resume_words)
    return list(matched)[:top_n]


# -------------------------------
# TF-IDF + SIMILARITY
# -------------------------------
def calculate_scores(job_desc, resumes):
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    all_text = [job_desc] + resumes
    vectors = vectorizer.fit_transform(all_text)
    return cosine_similarity(vectors[0:1], vectors[1:]).flatten()


# -------------------------------
# MAIN FUNCTION
# -------------------------------
def main():
    resume_folder = "resumes/"

    if not os.path.exists(resume_folder):
        print("❌ 'resumes' folder not found!")
        return

    files = [f for f in os.listdir(resume_folder) if f.endswith((".pdf", ".docx"))]

    if len(files) == 0:
        print("❌ No resumes found!")
        return

    # Load Job Description
    try:
        with open("data/job_description.txt", "r", encoding="utf-8") as f:
            job_desc = clean_text(f.read())
    except:
        print("❌ Job description file missing!")
        return

    resumes = []
    names = []

    # Read resumes
    for file in files:
        path = os.path.join(resume_folder, file)
        text = extract_resume_text(path)
        cleaned = clean_text(text)

        if cleaned == "":
            print(f"⚠️ Empty resume: {file}")

        resumes.append(cleaned)
        names.append(file)

    # Calculate similarity
    scores = calculate_scores(job_desc, resumes)

    # Matched skills
    keywords_list = [
        ", ".join(get_top_keywords(job_desc, r)) for r in resumes
    ]

    # DataFrame
    df = pd.DataFrame({
        "Resume": names,
        "Score": scores,
        "Matched Skills": keywords_list
    })

    # Sort
    df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

    # Rank
    df["Rank"] = df.index + 1

    # Convert to %
    df["Score (%)"] = (df["Score"] * 100).round(2)

    # Threshold (safe)
    threshold = 0.2
    df["Status"] = df["Score"].apply(
        lambda x: "Shortlisted" if x >= threshold else "Rejected"
    )

    print("\n📊 FINAL RESULTS:\n")
    print(df)

    # -------------------------------
    # OUTPUTS
    # -------------------------------
    os.makedirs("outputs", exist_ok=True)

    # Graph
    try:
        plt.figure()
        plt.bar(df["Resume"], df["Score"])
        plt.xlabel("Resumes")
        plt.ylabel("Similarity Score")
        plt.title("Resume Screening Scores")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("outputs/score_chart.png")
        plt.close()
    except:
        print("⚠️ Graph not generated")

    # Save all results
    df.to_csv("outputs/results.csv", index=False)

    # Shortlisted
    shortlisted = df[df["Status"] == "Shortlisted"]

    # 🔥 FIX: if none shortlisted → take top 3 anyway
    if shortlisted.empty:
        print("⚠️ No one met threshold → selecting Top 3 instead")
        shortlisted = df.head(3)

    shortlisted.to_csv("outputs/shortlisted.csv", index=False)

    # 🔥 GUARANTEED TOP CANDIDATES FILE
    top_n = min(3, len(df))  # even if <3 resumes
    top_candidates = df.head(top_n)

    if not top_candidates.empty:
        top_candidates.to_csv("outputs/top_candidates.csv", index=False)
        print("\n🏆 Top Candidates Saved!")
    else:
        print("❌ No candidates found!")

    print("\n✅ ALL FILES GENERATED SUCCESSFULLY!")


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    main()