import os

import config
from agents.nodes import load_job_description
from workflows.graph import app


def main():
    # Only plain-text resumes are supported (PDF/DOCX would need a parser).
    resumes = [
        f for f in os.listdir(config.RESUME_DIR)
        if os.path.isfile(os.path.join(config.RESUME_DIR, f)) and f.lower().endswith(".txt")
    ]
    if not resumes:
        print(f"No .txt resumes found in {config.RESUME_DIR!r}")
        return

    # Parse the job description ONCE and reuse it for every candidate.
    job = load_job_description()
    print(f"Screening {len(resumes)} resume(s) for: {job['job_title']}\n")

    for name in resumes:
        path = os.path.join(config.RESUME_DIR, name)
        try:
            final = app.invoke({"resume_file_path": path, **job})
            print(f"[ok]   {name}: {final.get('result')} (score {final.get('candidate_score')})")
        except Exception as e:  # one bad resume shouldn't kill the whole batch
            print(f"[skip] {name}: {e}")

    print(f"\nDone. Report: {config.REPORT_FILE}")


if __name__ == "__main__":
    main()
