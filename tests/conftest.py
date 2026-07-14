"""
Shared pytest fixtures.

`conftest.py` is special: pytest discovers it automatically, and any fixture
defined here is available to EVERY test file in this directory — no import needed.
This is the right place for setup that more than one test file reuses.
"""

import pytest


@pytest.fixture
def make_state():
    """
    A *factory* fixture: it returns a function that builds a screening-state dict
    with sensible defaults, which each test can override field-by-field.

    Why a factory (a fixture that returns a function) instead of a plain dict?
    Because each test needs a *slightly different* state ("what if the name is
    empty?", "what if the score is 150?"). The factory lets a test say exactly
    what it cares about and inherit everything else:

        state = make_state(candidate_name="", candidate_email="")

    The `Screening` type (workflows/state.py) is a TypedDict, which at runtime is
    just a plain dict — so we build a dict here.
    """
    def _make(**overrides):
        state = {
            "resume_file_path": "resumes/example.txt",
            "job_title": "Senior Backend Engineer",
            "job_description": "Python, FastAPI, PostgreSQL, AWS",
            "candidate_name": "Jane Doe",
            "candidate_email": "jane@example.com",
            "candidate_phone": "+1 555 0100",
            "candidate_skills": ["Python", "FastAPI"],
            "candidate_experience": ["Backend Engineer at Acme (2020 - Present)"],
            "candidate_education": ["BSc in Computer Science"],
            "candidate_achievements": [],
            "candidate_score": 0,
            "result": "fail",
        }
        state.update(overrides)
        return state

    return _make
