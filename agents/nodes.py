import os
import csv
import shutil
import config
from workflows.state import Screening
from agents.models import ollama_text_model
from agents.schemas import Result_Structure, JobDescription_Structure, CandidateInfo_Structure
from langchain_core.messages import SystemMessage, HumanMessage


def load_job_description() -> dict:
    """
    Read and parse the job description ONCE per run (not a graph node).

    The job description is the same for every candidate, so we parse it a single
    time in the runner (main.py) and feed the result into each screening run,
    instead of re-reading the file and re-calling the model for every resume.

    Returns:
        dict: {"job_title": str, "job_description": str}
    """

    job_description_file = config.JOB_DESCRIPTION_FILE  # Job description file (from .env)
    if not os.path.exists(job_description_file):
        raise FileNotFoundError(f"The file '{job_description_file}' does not exist.")

    with open(job_description_file, 'r') as file:
        job_file_description = file.read()

    with open(config.JD_PROMPT_FILE, 'r') as file:
        prompt_job_description = file.read()

    structured_model = ollama_text_model.with_structured_output(JobDescription_Structure)
    data = structured_model.invoke([
        SystemMessage(content=prompt_job_description),
        HumanMessage(content=job_file_description),
    ])

    # Defensive defaults: a small model can occasionally omit a field.
    return {
        "job_title": data.get("job_title") or "Not Specified",
        "job_description": data.get("job_description") or "",
    }


def extract_resume_text(state: Screening):
    """
    Extract structured candidate information from the current resume file.

    Args:
        state (Screening): The current state of the screening process.
    """

    resume_file_path = state.get("resume_file_path")
    if not resume_file_path or not os.path.exists(resume_file_path):
        raise FileNotFoundError(f"The resume file '{resume_file_path}' does not exist.")

    with open(resume_file_path, 'r') as file:
        resume_text = file.read()

    with open(config.RESUME_PROMPT_FILE, 'r') as file:
        prompt_extract_resume_text = file.read()

    structured_model = ollama_text_model.with_structured_output(CandidateInfo_Structure)
    data = structured_model.invoke([
        SystemMessage(content=prompt_extract_resume_text),
        HumanMessage(content=resume_text),
    ])

    # Defensive defaults so a rough structured-output parse never crashes the node.
    return {
        "candidate_name": data.get("candidate_name") or "",
        "candidate_email": data.get("candidate_email") or "",
        "candidate_phone": data.get("candidate_phone") or "",
        "candidate_skills": data.get("candidate_skills") or [],
        "candidate_experience": data.get("candidate_experience") or [],
        "candidate_education": data.get("candidate_education") or [],
        "candidate_achievements": data.get("candidate_achievements") or [],
    }


def score_candidate(state: Screening):
    """
    Score the candidate against the job description and decide pass/fail.

    Args:
        state (Screening): The current state of the screening process.
    """

    candidate_info = {
        "candidate_name": state.get("candidate_name"),
        "candidate_email": state.get("candidate_email"),
        "candidate_phone": state.get("candidate_phone"),
        "candidate_skills": state.get("candidate_skills"),
        "candidate_experience": state.get("candidate_experience"),
        "candidate_education": state.get("candidate_education"),
        "candidate_achievements": state.get("candidate_achievements"),
    }

    job_description = {
        "job_title": state.get("job_title"),
        "job_description": state.get("job_description"),
    }

    with open(config.SCORE_PROMPT_FILE, 'r') as file:
        prompt_score_candidate = file.read()

    prompt = [
        SystemMessage(content=prompt_score_candidate),
        HumanMessage(content=f"Candidate Info:\n{candidate_info}\n\nJob Description:\n{job_description}"),
    ]

    structured_model = ollama_text_model.with_structured_output(Result_Structure)
    result_data = structured_model.invoke(prompt)

    # Coerce the score to a safe int (small models may return None or a string).
    try:
        candidate_score = int(result_data.get("candidate_score") or 0)
    except (TypeError, ValueError):
        candidate_score = 0
    candidate_score = max(0, min(100, candidate_score))  # clamp to 0..100

    # Decide pass/fail in Python from the score so the label always agrees with the
    # number (never trust the model to apply the threshold consistently).
    result = "pass" if candidate_score >= config.PASS_SCORE_THRESHOLD else "fail"

    return {
        "result": result,
        "candidate_score": candidate_score,
    }


def compile_results(state: Screening):
    """
    Persist the screening result to a CSV report and file the resume under
    the shortlisted/ or rejected/ directory.

    Args:
        state (Screening): The current state of the screening process.
    """

    # --- Append a row to the CSV report (with a header on first write). ---
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    write_header = (not os.path.exists(config.REPORT_FILE)) or os.path.getsize(config.REPORT_FILE) == 0
    with open(config.REPORT_FILE, "a", newline="") as report_file:
        writer = csv.writer(report_file)
        if write_header:
            writer.writerow(["candidate_name", "candidate_email", "candidate_phone",
                             "candidate_score", "result"])
        writer.writerow([
            state.get("candidate_name"),
            state.get("candidate_email"),
            state.get("candidate_phone"),
            state.get("candidate_score"),
            state.get("result"),
        ])

    # --- Move the resume into the shortlisted/ or rejected/ folder. ---
    src = state.get("resume_file_path")
    dest_dir = config.SHORTLIST_DIR if state.get("result") == "pass" else config.REJECTED_DIR
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(src))
    if os.path.exists(dest):
        os.remove(dest)  # overwrite a stale copy from a previous run
    shutil.move(src, dest)  # shutil.move works across filesystems; os.rename may not
