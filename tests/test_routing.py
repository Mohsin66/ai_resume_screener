"""
Unit tests for the conditional-routing logic you added to the graph.

These are the *ideal* first unit tests because the functions under test are
**pure**: they take a state dict and return a value, with no LLM call, no file
I/O, and no randomness. That means the tests are fast and 100% deterministic.

Concepts taught here:
  - basic test structure (a `test_*` function with an `assert`)
  - `@pytest.mark.parametrize` — run the SAME test body over many inputs
  - using the `make_state` fixture from conftest.py
"""

import pytest

from agents.nodes import check_identity_validation, auto_reject_candidate


# ---------------------------------------------------------------------------
# check_identity_validation: the router. It must return "valid" / "invalid".
# ---------------------------------------------------------------------------

# One test body, many cases. Each tuple becomes a separate test in the output,
# so a failure tells you EXACTLY which input broke — far better than a loop.
@pytest.mark.parametrize(
    "name, email, expected",
    [
        ("Jane Doe", "jane@example.com", "valid"),    # both present -> valid
        ("Jane Doe", "",                 "invalid"),   # email missing
        ("",         "jane@example.com", "invalid"),   # name missing
        ("",         "",                 "invalid"),   # nothing (blank_resume case)
        ("   ",      "jane@example.com", "invalid"),   # whitespace-only name
        ("Jane Doe", "   ",              "invalid"),   # whitespace-only email
        (None,       None,               "invalid"),   # model returned None
    ],
)
def test_identity_routing_truth_table(make_state, name, email, expected):
    state = make_state(candidate_name=name, candidate_email=email)
    assert check_identity_validation(state) == expected


def test_phone_alone_is_not_enough(make_state):
    """The 'anonymous_candidate' scenario: a phone but no name/email -> invalid.

    This is the real case we saw in the end-to-end run: a strong resume that has
    a phone number but no identity still routes to auto-reject.
    """
    state = make_state(candidate_name="", candidate_email="", candidate_phone="+44 7700 900123")
    assert check_identity_validation(state) == "invalid"


def test_router_does_not_mutate_state(make_state):
    """A routing function must ONLY read state and return a label — never change it.

    This locks in the core LangGraph lesson: routers decide, nodes mutate.
    """
    state = make_state(candidate_name="", candidate_email="")
    snapshot = dict(state)
    check_identity_validation(state)
    assert state == snapshot  # unchanged


# ---------------------------------------------------------------------------
# auto_reject_candidate: the node the "invalid" branch routes to.
# A node returns a dict of state UPDATES (here: force a failing verdict).
# ---------------------------------------------------------------------------

def test_auto_reject_returns_failing_verdict(make_state):
    update = auto_reject_candidate(make_state())
    assert update == {"candidate_score": 0, "result": "fail"}
