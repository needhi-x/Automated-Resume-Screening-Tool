import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber

# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# -----------------------------
# READ PDF
# -----------------------------
def read_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print("Error reading:", file_path, "|", e)
    return text

# -----------------------------
# SKILLS
# -----------------------------
core_skills = ["python", "machine learning", "sql"]
tools = ["excel", "power bi", "tableau"]
libraries = ["pandas", "numpy", "matplotlib", "seaborn", "scikit learn", "tensorflow", "keras"]

all_skills = core_skills + tools + libraries

# -----------------------------
# EXTRACT SKILLS
# -----------------------------
def extract_skills(text):
    return [skill for skill in all_skills if skill in text]

# -----------------------------
# EXPERIENCE BONUS
# -----------------------------
def experience_score(text):
    keywords = ["experience", "years", "worked", "internship", "project"]
    return sum(1 for word in keywords if word in text)

# -----------------------------
# PATHS
# -----------------------------
resume_folder = r"C:\Users\neha\OneDrive\Desktop\Python\Automated-Resume-Screening-Tool\data\sample_resumes"
output_folder = r"C:\Users\neha\OneDrive\Desktop\Python\Automated-Resume-Screening-Tool\sample_outputs"

os.makedirs(output_folder, exist_ok=True)

# -----------------------------
# PROCESS FILES
# -----------------------------
results = []
files = os.listdir(resume_folder)

print("Files found:", files)

for file in files:
    file_path = os.path.join(resume_folder, file)
    print("Processing:", file)

    text = ""

    if file.endswith(".pdf"):
        text = read_pdf(file_path)
    elif file.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        continue

    text = clean_text(text)

    if len(text) == 0:
        print("Empty content:", file)
        continue

    matched = extract_skills(text)

    # -----------------------------
    # SCORING
    # -----------------------------
    score = 0
    for skill in matched:
        if skill in core_skills:
            score += 3
        elif skill in tools:
            score += 2
        elif skill in libraries:
            score += 1

    score += experience_score(text)

    match_percent = round((len(matched) / len(all_skills)) * 100, 2)

    results.append({
        "Resume": file,
        "Score": score,
        "Match_Percent": match_percent,
        "Skills": ", ".join(matched)
    })

# -----------------------------
# CHECK
# -----------------------------
if len(results) == 0:
    print("No resumes processed")
    exit()

df = pd.DataFrame(results)

# -----------------------------
# SORT + RANK
# -----------------------------
df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# -----------------------------
# STATUS (FIXED LOGIC)
# -----------------------------
df["Status"] = "Rejected"

n = len(df)

selected_count = max(1, int(n * 0.2))
shortlisted_count = max(1, int(n * 0.5))

df.loc[:selected_count-1, "Status"] = "Selected"

end_shortlist = min(n, selected_count + shortlisted_count)
df.loc[selected_count:end_shortlist-1, "Status"] = "Shortlisted"

# -----------------------------
# FILTER FILES
# -----------------------------
selected_df = df[df["Status"] == "Selected"]
shortlisted_df = df[df["Status"] == "Shortlisted"]

# -----------------------------
# TOP CANDIDATES
# -----------------------------
top_candidates_df = df.head(2)

# -----------------------------
# SAVE FILES
# -----------------------------
df.to_csv(os.path.join(output_folder, "all_results.csv"), index=False)
selected_df.to_csv(os.path.join(output_folder, "selected.csv"), index=False)
shortlisted_df.to_csv(os.path.join(output_folder, "shortlisted.csv"), index=False)
top_candidates_df.to_csv(os.path.join(output_folder, "top_candidates.csv"), index=False)

# -----------------------------
# GRAPH
# -----------------------------
plt.figure()
plt.bar(df["Resume"], df["Score"])
plt.xticks(rotation=45)
plt.title("Resume Score Comparison")
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "score_chart.png"))

# -----------------------------
# DONE
# -----------------------------
print("\nATS SYSTEM COMPLETED SUCCESSFULLY")
print("Outputs saved in:", output_folder)
print("all_results.csv")
print("selected.csv")
print("shortlisted.csv")
print("top_candidates.csv")
print("score_chart.png")