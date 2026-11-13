import os
from pypdf import PdfReader
import re
import mysql.connector

# ---------- Resume Extraction ----------
def extract_resume(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    email = re.findall(r'\S+@\S+', text)
    phone = re.findall(r'\b\d{10}\b', text)

    skills_list = [
        "Java",
        "Python",
        "SQL",
        "MySQL",
        "HTML",
        "CSS",
        "JavaScript"
    ]

    found_skills = []

    for skill in skills_list:
        if skill.lower() in text.lower():
            found_skills.append(skill)

    return {
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "skills": found_skills
    }


# ---------- Extract Resume ----------
result = extract_resume("resumes/sample_resume.pdf")

print("Resume data extracted successfully!")
print("Email:", result["email"])
print("Phone:", result["phone"])
print("Skills:", result["skills"])


# ---------- MySQL Connection ----------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="resumeiq"
)

cursor = db.cursor()


# ---------- Insert Candidate ----------
sql = """
INSERT INTO candidates (name, email, phone, resume_file)
VALUES (%s, %s, %s, %s)
"""

values = (
    "Rahul Kumar",
    result["email"],
    result["phone"],
    "sample_resume.pdf"
)

cursor.execute(sql, values)

candidate_id = cursor.lastrowid


# ---------- Insert Skills ----------
for skill in result["skills"]:

    sql = """
    INSERT INTO skills (candidate_id, skill_name)
    VALUES (%s, %s)
    """

    cursor.execute(sql, (candidate_id, skill))


db.commit()

print("Candidate data inserted into MySQL successfully!")
print("Candidate ID:", candidate_id)

cursor.close()
db.close()