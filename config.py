"""
Central configuration for the HR Recruiter project.

All tunable values (directory paths, file paths, model settings) are read here
from environment variables (loaded from the .env file). Nothing else in the code
base should hardcode a path or a model name — import the constants from this module
instead. Sensible defaults are provided so the project still runs if a variable is
missing from .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load key=value pairs from the .env file into the process environment (once).
load_dotenv()

# Absolute path to the project root (the folder that contains this file).
BASE_DIR = Path(__file__).resolve().parent


def _path(env_key: str, default: str) -> str:
    """
    Resolve a path from an environment variable.

    Relative paths are anchored to the project root so the app behaves the same
    no matter which directory it is launched from. Absolute paths are used as-is.
    """
    value = os.getenv(env_key, default).strip()
    p = Path(value)
    return str(p if p.is_absolute() else BASE_DIR / p)


# ---- Directories ----
RESUME_DIR = _path("RESUME_DIR", "resumes")
SHORTLIST_DIR = _path("SHORTLIST_DIR", "shortlisted")
REJECTED_DIR = _path("REJECTED_DIR", "rejected")
REPORTS_DIR = _path("REPORTS_DIR", "reports")
PROMPTS_DIR = _path("PROMPTS_DIR", "prompts")
DESCRIPTIONS_DIR = _path("DESCRIPTIONS_DIR", "descriptions")

# ---- Input / output files ----
JOB_DESCRIPTION_FILE = _path("JOB_DESCRIPTION_FILE", "descriptions/job_description.txt")
REPORT_FILE = _path("REPORT_FILE", "reports/screening_results.csv")

# ---- Prompt template files ----
JD_PROMPT_FILE = _path("JD_PROMPT_FILE", "prompts/read_job_description.txt")
RESUME_PROMPT_FILE = _path("RESUME_PROMPT_FILE", "prompts/extract_resume_data.txt")
SCORE_PROMPT_FILE = _path("SCORE_PROMPT_FILE", "prompts/score_candidate.txt")

# ---- LLM settings ----
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama").lower()

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3.2:3b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

# ---- Screening rules ----
# Minimum candidate_score (0-100) required to be shortlisted ("pass").
PASS_SCORE_THRESHOLD = int(os.getenv("PASS_SCORE_THRESHOLD", "60"))
