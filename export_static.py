"""Build frontend/data/dashboard.json from the PDFs in resumes/ -- no MySQL needed.

The GitHub Pages site is static, so it cannot talk to MySQL. Run this script
whenever resumes or jobs change, then commit frontend/data/dashboard.json.
The JSON has the same shape as the Flask /api/dashboard response.
"""
import glob, json, os, re, datetime
from pypdf import PdfReader

HERE = os.path.dirname(os.path.abspath(__file__))

SKILLS = ["Java", "Python", "SQL", "MySQL", "HTML", "CSS", "JavaScript"]

JOBS = [  # keep in sync with Database/schema.sql
    (1, "Java Developer", "Build and maintain Java applications backed by relational databases.", "Java, SQL, MySQL, HTML, CSS"),
    (2, "Python Data Analyst", "Analyse data with Python and SQL and report insights.", "Python, SQL, MySQL"),
    (3, "Full Stack Developer", "Develop web front ends and Java back-end services.", "Java, JavaScript, HTML, CSS, SQL"),
]


def extract(path):
    text = "".join((p.extract_text() or "") for p in PdfReader(path).pages)
    email = re.findall(r"\S+@\S+", text)
    phone = re.findall(r"\b\d{10}\b", text)
    low = text.lower()
    skills = [s for s in SKILLS if s.lower() in low]
    lines = text.strip().split("\n")
    return {
        "name": lines[0].strip() if lines else "",
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "skills": skills,
    }


def main():
    files = sorted(glob.glob(os.path.join(HERE, "resumes", "*.pdf")))
    candidates = []
    for i, f in enumerate(files, 1):
        c = extract(f)
        c.update(candidate_id=i, resume_file=os.path.basename(f))
        candidates.append(c)

    jobs = [
        {"job_id": j, "job_title": t, "job_description": d, "required_skills": r}
        for j, t, d, r in JOBS
    ]

    results = []
    for c in candidates:
        have = [s.lower() for s in c["skills"]]
        for job in jobs:
            req = [s.strip() for s in job["required_skills"].split(",") if s.strip()]
            matched = [s for s in req if s.lower() in have]
            missing = [s for s in req if s.lower() not in have]
            score = round(len(matched) / len(req) * 100, 2) if req else 0
            results.append({
                "candidate_id": c["candidate_id"], "name": c["name"],
                "email": c["email"], "phone": c["phone"],
                "resume_file": c["resume_file"],
                "job_id": job["job_id"], "job": job["job_title"],
                "matched": matched, "missing": missing,
                "score": score, "status": "Calculated",
            })

    avg = round(sum(r["score"] for r in results) / len(results), 2) if results else 0
    out = {
        "total_candidates": len(candidates),
        "total_jobs": len(jobs),
        "average_match": avg,
        "results": results,
        "jobs": jobs,
        "generated_at": datetime.date.today().isoformat(),
    }
    dest = os.path.join(HERE, "frontend", "data", "dashboard.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"Wrote {dest}: {len(candidates)} candidates, {len(jobs)} jobs, avg {avg}%")


if __name__ == "__main__":
    main()
