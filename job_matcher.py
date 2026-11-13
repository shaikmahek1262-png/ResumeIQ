
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    override=True
)


# Connect to Aiven MySQL
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


# Calculate skill-based matching percentage
def calculate_match(candidate_skills, required_skills):

    candidate_set = {
        skill.strip().lower()
        for skill in candidate_skills
    }

    matched = [
        skill for skill in required_skills
        if skill.strip().lower() in candidate_set
    ]

    if not required_skills:
        return 0, []

    score = (len(matched) / len(required_skills)) * 100

    return score, matched


def main():

    db = connect_database()
    cursor = db.cursor()

    try:

        # Fetch ALL jobs
        cursor.execute("""
            SELECT job_id, job_title, required_skills
            FROM jobs
            ORDER BY job_id
        """)

        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found in database!")
            return

        # Fetch ALL candidates
        cursor.execute("""
            SELECT candidate_id, name
            FROM candidates
            ORDER BY candidate_id
        """)

        candidates = cursor.fetchall()

        print("\n----- ResumeIQ Matching Engine -----")
        print("Total candidates:", len(candidates))
        print("Total jobs:", len(jobs))
        print("Expected matching results:", len(candidates) * len(jobs))

        processed = 0

        # Process every candidate against every job
        for job in jobs:

            job_id = job[0]
            job_title = job[1]

            required_skills = [
                skill.strip()
                for skill in (job[2] or "").split(",")
                if skill.strip()
            ]

            print("\n================================")
            print("JOB:", job_title)
            print("Required Skills:", required_skills)
            print("================================")

            for candidate in candidates:

                candidate_id = candidate[0]
                candidate_name = candidate[1]

                # Fetch candidate skills
                cursor.execute("""
                    SELECT skill_name
                    FROM skills
                    WHERE candidate_id = %s
                """, (candidate_id,))

                candidate_skills = [
                    row[0] for row in cursor.fetchall()
                ]

                # Calculate match
                score, matched = calculate_match(
                    candidate_skills,
                    required_skills
                )

                missing = [
                    skill for skill in required_skills
                    if skill.lower() not in
                    [item.lower() for item in matched]
                ]

                print("\n------------------------------")
                print("Candidate:", candidate_name)
                print("Job:", job_title)
                print("Matched Skills:", matched)
                print("Missing Skills:", missing)
                print("Match Score:", round(score, 2), "%")

                # Check whether score already exists
                cursor.execute("""
                    SELECT score_id
                    FROM match_scores
                    WHERE candidate_id = %s
                    AND job_id = %s
                    ORDER BY score_id DESC
                    LIMIT 1
                """, (candidate_id, job_id))

                old_score = cursor.fetchone()

                if old_score:

                    cursor.execute("""
                        UPDATE match_scores
                        SET similarity_score = %s,
                            status = %s
                        WHERE score_id = %s
                    """, (
                        score,
                        "Calculated",
                        old_score[0]
                    ))

                else:

                    cursor.execute("""
                        INSERT INTO match_scores
                        (candidate_id, job_id,
                         similarity_score, status)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        candidate_id,
                        job_id,
                        score,
                        "Calculated"
                    ))

                processed += 1

        db.commit()

        print("\n================================")
        print("MATCHING SUMMARY")
        print("================================")
        print("Total candidates:", len(candidates))
        print("Total jobs:", len(jobs))
        print("Total matching results:", processed)
        print("Matching scores saved successfully!")

    except Exception as error:

        db.rollback()
        print("Matching error:", error)

    finally:

        cursor.close()
        db.close()

    print("\nResumeIQ matching completed!")


if __name__ == "__main__":
    main()
