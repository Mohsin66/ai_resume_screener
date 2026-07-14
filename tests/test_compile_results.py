"""
Unit tests for `compile_results` — the node with SIDE EFFECTS.

This node writes a CSV row and MOVES the resume file into shortlisted/ or
rejected/. We must never let a test touch the real project folders, so we
redirect every path into a throwaway temp directory.

Concepts taught here:
  - `tmp_path` — pytest's built-in fixture giving each test a unique temp dir
    (auto-cleaned afterwards), the standard way to test filesystem code
  - `monkeypatch.setattr(config, ...)` — point the code's config at the temp dir
  - asserting on SIDE EFFECTS (a file moved, a CSV's contents) rather than a
    return value
  - composing fixtures: our `sandbox` fixture builds on `tmp_path` + `monkeypatch`
"""

import csv

import pytest

import config
from agents.nodes import compile_results


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Isolate compile_results: temp output dirs + a fake resume to move."""
    reports = tmp_path / "reports"
    shortlisted = tmp_path / "shortlisted"
    rejected = tmp_path / "rejected"
    resumes = tmp_path / "resumes"
    for d in (reports, shortlisted, rejected, resumes):
        d.mkdir()

    report_file = reports / "screening_results.csv"

    # Redirect the module's configuration at the four paths compile_results reads.
    monkeypatch.setattr(config, "REPORTS_DIR", str(reports))
    monkeypatch.setattr(config, "REPORT_FILE", str(report_file))
    monkeypatch.setattr(config, "SHORTLIST_DIR", str(shortlisted))
    monkeypatch.setattr(config, "REJECTED_DIR", str(rejected))

    resume = resumes / "candidate.txt"
    resume.write_text("resume content")

    return {
        "report_file": report_file,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "resume": resume,
    }


def test_passing_candidate_is_filed_in_shortlisted(sandbox, make_state):
    state = make_state(
        resume_file_path=str(sandbox["resume"]),
        result="pass",
        candidate_score=80,
    )

    compile_results(state)

    # The file was MOVED: present in shortlisted/, gone from the source.
    assert (sandbox["shortlisted"] / "candidate.txt").exists()
    assert not sandbox["resume"].exists()


def test_failing_candidate_is_filed_in_rejected(sandbox, make_state):
    state = make_state(
        resume_file_path=str(sandbox["resume"]),
        result="fail",
        candidate_score=0,
    )

    compile_results(state)

    assert (sandbox["rejected"] / "candidate.txt").exists()
    assert not sandbox["resume"].exists()


def test_csv_writes_header_then_row(sandbox, make_state):
    state = make_state(
        resume_file_path=str(sandbox["resume"]),
        candidate_name="Jane Doe",
        candidate_email="jane@example.com",
        candidate_phone="+1 555 0100",
        candidate_score=80,
        result="pass",
    )

    compile_results(state)

    with open(sandbox["report_file"], newline="") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["candidate_name", "candidate_email", "candidate_phone", "candidate_score", "result"]
    assert rows[1] == ["Jane Doe", "jane@example.com", "+1 555 0100", "80", "pass"]


def test_second_write_appends_without_duplicating_header(sandbox, make_state):
    """Two candidates -> one header, two data rows (header only on first write)."""
    first = make_state(resume_file_path=str(sandbox["resume"]), result="pass", candidate_score=80)
    compile_results(first)

    # A second resume file for the second candidate.
    second_resume = sandbox["resume"].parent / "second.txt"
    second_resume.write_text("another resume")
    second = make_state(resume_file_path=str(second_resume), result="fail", candidate_score=10)
    compile_results(second)

    with open(sandbox["report_file"], newline="") as f:
        rows = list(csv.reader(f))

    assert len(rows) == 3            # 1 header + 2 data rows
    assert rows[0][0] == "candidate_name"
