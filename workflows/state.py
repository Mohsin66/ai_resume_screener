from typing import TypedDict, Literal


class Screening(TypedDict):
    # Input: absolute path of the resume being screened (set by main.py per run).
    resume_file_path: str

    # Job description (parsed once in main.py, passed into each run).
    job_title: str
    job_description: str

    # Extracted candidate information.
    candidate_name: str
    candidate_email: str
    candidate_phone: str
    candidate_skills: list[str]
    candidate_experience: list[str]
    candidate_education: list[str]
    candidate_achievements: list[str]

    # Scoring result.
    candidate_score: int
    result: Literal["pass", "fail"]
