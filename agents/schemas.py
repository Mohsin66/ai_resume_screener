
from typing import TypedDict, Literal


class Result_Structure(TypedDict):

    candidate_name: str
    candidate_email: str
    candidate_phone: str
    result: Literal["pass", "fail"]
    candidate_score: int

class JobDescription_Structure(TypedDict):

    job_title: str
    job_description: str

class CandidateInfo_Structure(TypedDict):

    candidate_name: str
    candidate_email: str
    candidate_phone: str
    candidate_skills: list[str]
    candidate_experience: list[str]
    candidate_education: list[str]
    candidate_achievements: list[str]