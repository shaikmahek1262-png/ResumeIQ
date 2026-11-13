


from pypdf import PdfReader
import mysql.connector
import re
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESUME_FOLDER = os.path.join(BASE_DIR, "resumes")


def extract_resume(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    email = re.findall(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

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
        if re.search(r'\b' + re.escape(skill) + r'\b',
                     text, re.IGNORECASE):
            found_skills.append(skill)

    name = text.strip().split("\n")[0].strip()
    name = name[:150] if name else os.path.basename(file_path)[:150]

    return {
        "name": name,
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "skills": found_skills
    }


def connect_database():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "13290")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        ssl_ca=os.path.abspath(os.getenv("MYSQL_SSL_CA")),
        ssl_verify_cert=True
    )


def main():

    resume_files = sorted(
        glob.glob(os.path.join(RESUME_FOLDER, "*.pdf"))
    )

    print("----- ResumeIQ Parser -----")
    print("Total resumes found:", len(resume_files))

    if not resume_files:
        print("No PDF resumes found!")
        return

    db = connect_database()
    cursor = db.cursor()

    successful = 0
    failed = 0

    try:

        for file_path in resume_files:

            filename = os.path.basename(file_path)

            print("\nProcessing:", filename)

            try:

                result = extract_resume(file_path)

                print("Name:", result["name"])
                print("Email:", result["email"])
                print("Phone:", result["phone"])
                print("Skills:", result["skills"])

                # First identify candidate using resume filename
                cursor.execute(
                    """
                    SELECT candidate_id
                    FROM candidates
                    WHERE resume_file = %s
                    """,
                    (filename,)
                )

                existing = cursor.fetchone()

                # If filename is new, check for an existing email
                if not existing and result["email"]:
                    cursor.execute(
                        """
                        SELECT candidate_id
                        FROM candidates
                        WHERE email = %s
                        LIMIT 1
                        """,
                        (result["email"],)
                    )
                    existing = cursor.fetchone()

                if existing:

                    candidate_id = existing[0]

                    cursor.execute(
                        """
                        UPDATE candidates
                        SET name = %s,
                            email = %s,
                            phone = %s,
                            resume_file = %s
                        WHERE candidate_id = %s
                        """,
                        (
                            result["name"],
                            result["email"],
                            result["phone"],
                            filename,
                            candidate_id
                        )
                    )

                    cursor.execute(
                        "DELETE FROM skills WHERE candidate_id = %s",
                        (candidate_id,)
                    )

                    print("Existing candidate updated.")

                else:

                    cursor.execute(
                        """
                        INSERT INTO candidates
                        (name, email, phone, resume_file)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            result["name"],
                            result["email"],
                            result["phone"],
                            filename
                        )
                    )

                    candidate_id = cursor.lastrowid

                    print("New candidate added.")

                # Save extracted skills
                for skill in result["skills"]:

                    cursor.execute(
                        """
                        INSERT INTO skills
                        (candidate_id, skill_name)
                        VALUES (%s, %s)
                        """,
                        (candidate_id, skill)
                    )

                db.commit()

                successful += 1

                print("Saved successfully!")
                print("Candidate ID:", candidate_id)

            except Exception as error:

                db.rollback()
                failed += 1

                print("Could not process:", filename)
                print("Error:", error)

        print("\n----- IMPORT SUMMARY -----")
        print("Total PDF files:", len(resume_files))
        print("Successfully processed:", successful)
        print("Failed:", failed)

        cursor.execute("SELECT COUNT(*) FROM candidates")
        total = cursor.fetchone()[0]

        print("Total candidates in Aiven:", total)

        cursor.execute("SELECT COUNT(*) FROM skills")
        print("Total skill records:", cursor.fetchone()[0])

    finally:

        cursor.close()
        db.close()

    print("\nResume processing completed!")


if __name__ == "__main__":
    main()
