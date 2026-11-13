
from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)



def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "13290")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        ssl_ca=os.getenv(
            "MYSQL_SSL_CA",
            "/etc/secrets/ca.pem"
        ),
        ssl_verify_cert=True
    )


@app.route("/")
def home():
    return jsonify({
        "message": "ResumeIQ Backend is running!"
    })


@app.route("/api/health")
def health():
    try:
        db = get_db_connection()
        db.close()

        return jsonify({
            "status": "success",
            "message": "Backend and MySQL are connected!"
        })

    except Exception as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


@app.route("/api/dashboard")
def dashboard():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get all candidates
        cursor.execute("""
            SELECT candidate_id, name, email, phone, resume_file
            FROM candidates
            ORDER BY candidate_id DESC
        """)
        candidates = cursor.fetchall()

        # Get all jobs
        cursor.execute("""
            SELECT job_id, job_title, job_description,
                   required_skills
            FROM jobs
            ORDER BY job_id DESC
        """)
        jobs = cursor.fetchall()

        # Get the latest saved score for each candidate-job pair
        cursor.execute("""
            SELECT ms.candidate_id, ms.job_id,
                   ms.similarity_score, ms.status
            FROM match_scores ms
            INNER JOIN (
                SELECT candidate_id, job_id,
                       MAX(score_id) AS latest_score_id
                FROM match_scores
                GROUP BY candidate_id, job_id
            ) latest
            ON ms.score_id = latest.latest_score_id
        """)
        scores = cursor.fetchall()

        # Store candidate skills
        candidate_skills = {}

        cursor.execute("""
            SELECT candidate_id, skill_name
            FROM skills
        """)

        for row in cursor.fetchall():
            candidate_id = row["candidate_id"]

            if candidate_id not in candidate_skills:
                candidate_skills[candidate_id] = []

            candidate_skills[candidate_id].append(
                row["skill_name"]
            )

        # Create lookup dictionaries
        candidate_lookup = {
            c["candidate_id"]: c for c in candidates
        }

        job_lookup = {
            j["job_id"]: j for j in jobs
        }

        results = []

        for score in scores:
            candidate_id = score["candidate_id"]
            job_id = score["job_id"]

            candidate = candidate_lookup.get(candidate_id)
            job = job_lookup.get(job_id)

            if candidate is None or job is None:
                continue

            skills = candidate_skills.get(candidate_id, [])

            required_text = job["required_skills"] or ""

            required_skills = [
                skill.strip()
                for skill in required_text.split(",")
                if skill.strip()
            ]

            candidate_lower = [
                skill.lower() for skill in skills
            ]

            matched = [
                skill for skill in required_skills
                if skill.lower() in candidate_lower
            ]

            missing = [
                skill for skill in required_skills
                if skill.lower() not in candidate_lower
            ]

            results.append({
                "candidate_id": candidate_id,
                "name": candidate["name"],
                "email": candidate["email"],
                "phone": candidate["phone"],
                "resume_file": candidate["resume_file"],
                "job_id": job_id,
                "job": job["job_title"],
                "matched": matched,
                "missing": missing,
                "score": float(score["similarity_score"] or 0),
                "status": score["status"]
            })

        average_match = 0

        if results:
            average_match = round(
                sum(item["score"] for item in results)
                / len(results),
                2
            )

        return jsonify({
            "total_candidates": len(candidates),
            "total_jobs": len(jobs),
            "average_match": average_match,
            "results": results,
            "jobs": jobs
        })

    except Exception as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
