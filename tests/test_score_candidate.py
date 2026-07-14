"""
Unit tests for `score_candidate` — WITHOUT calling a real LLM.

`score_candidate` calls the model, but the *interesting logic we want to protect*
is pure Python: coercing the model's raw score to an int, clamping it to 0..100,
and deciding pass/fail from the threshold. We don't want a slow, non-deterministic
Ollama call in a unit test — so we **mock** the model.

Concepts taught here:
  - `monkeypatch` — temporarily replace an attribute (here, the module-level
    `text_model`) for the duration of ONE test, auto-restored afterwards
  - test doubles / fakes — a tiny stand-in object that mimics just enough of the
    real API (`.with_structured_output(...).invoke(...)`) to drive the code
  - pinning external config (`PASS_SCORE_THRESHOLD`) so tests don't depend on .env
"""

import pytest

import config
import agents.nodes as nodes
from agents.nodes import score_candidate


# --- The fake LLM: mimics the two-call chain the real model exposes. ---
# Real usage in nodes.py:  text_model.with_structured_output(Schema).invoke(prompt)
class _FakeStructuredModel:
    def __init__(self, response):
        self._response = response

    def invoke(self, _prompt):
        return self._response  # canned answer — no network, no randomness


class _FakeModel:
    def __init__(self, response):
        self._response = response

    def with_structured_output(self, _schema):
        return _FakeStructuredModel(self._response)


@pytest.fixture
def fake_llm(monkeypatch):
    """Return a helper that swaps in a fake model returning `response`.

    Also pins PASS_SCORE_THRESHOLD to 60 so the test is independent of whatever
    is in the developer's .env file.
    """
    def _install(response):
        monkeypatch.setattr(nodes, "text_model", _FakeModel(response))
        monkeypatch.setattr(config, "PASS_SCORE_THRESHOLD", 60)

    return _install


@pytest.mark.parametrize(
    "raw_score, expected_score, expected_result",
    [
        (80,   80,  "pass"),   # normal pass
        (60,   60,  "pass"),   # exactly at the threshold -> pass (>= 60)
        (59,   59,  "fail"),   # just below the threshold
        (150, 100,  "pass"),   # clamp: above 100 becomes 100
        (-20,   0,  "fail"),   # clamp: below 0 becomes 0
        ("75", 75,  "pass"),   # a string score is coerced to int
        (None,  0,  "fail"),   # a missing/None score becomes 0
    ],
)
def test_score_is_clamped_and_thresholded(make_state, fake_llm, raw_score, expected_score, expected_result):
    # The model's own "result" is intentionally wrong ("banana") to prove that
    # Python — not the model — decides pass/fail from the clamped score.
    fake_llm({"candidate_score": raw_score, "result": "banana"})

    update = score_candidate(make_state())

    assert update["candidate_score"] == expected_score
    assert update["result"] == expected_result
