# Testing Guide

A learning-oriented test suite for this project. It's here to teach you the
testing skills a software engineer uses every day — using *your own* code as the
example. Read this top to bottom once; after that it's a reference.

---

## Why test at all?

Right now, the only way to know your screening pipeline works is to run
`python main.py` and eyeball the output — which is slow (a real Ollama run took
~4 minutes), non-deterministic (the LLM can answer differently each time), and
can't tell you *which* piece broke. Automated tests fix all three:

- **Fast** — the whole suite runs in ~1.5 seconds.
- **Deterministic** — same result every time, so a failure is a real bug.
- **Precise** — a failing test names the exact function and input that broke.
- **A safety net** — refactor with confidence; if you break behavior, a test goes red.

## The testing pyramid (the mental model)

```
        ▲  fewer, slower, broader
        │        ┌─────────────┐
        │        │  End-to-end │   run main.py on real files + real LLM
        │      ┌─┴─────────────┴─┐
        │      │  Integration    │   run the whole graph with a FAKE llm
        │   ┌──┴─────────────────┴──┐
        │   │      Unit tests       │   one pure function at a time  ← we live here
        ▼   └───────────────────────┘
             many, fast, focused
```

Most of your tests should be **unit tests** at the bottom: cheap, fast, and they
pinpoint bugs. You add a few integration/e2e tests on top for confidence that the
pieces fit together. This suite is all unit tests; see "What to learn next" for
how you'd add the layers above.

---

## What's in here

| File | What it tests | Concepts it teaches |
|------|---------------|---------------------|
| `conftest.py` | (no tests) shared fixtures | `conftest.py`, factory fixtures |
| `test_routing.py` | `check_identity_validation`, `auto_reject_candidate` | `assert`, `@parametrize`, read-only routers |
| `test_score_candidate.py` | score clamping + pass/fail threshold | **mocking** an LLM with `monkeypatch`, pinning config |
| `test_compile_results.py` | CSV writing + file routing | `tmp_path`, testing **side effects** |

Start by reading `test_routing.py` — it's the simplest and it tests the exact
feature you just built (the conditional edge).

---

## Core pytest concepts (glossary)

**Test discovery.** pytest finds tests by convention (configured in `pytest.ini`):
files named `test_*.py`, functions named `test_*`. No registration needed.

**`assert`.** pytest uses plain Python `assert`. On failure it shows both sides of
the comparison automatically — no special assert methods to memorize.

**`@pytest.mark.parametrize`.** Runs one test body over many input rows. Each row
becomes its own reported test, so you get a truth-table of cases and a failure
tells you exactly which row broke. See the routing truth-table.

**Fixtures.** A fixture is reusable setup a test asks for by naming it as a
parameter. `make_state` (ours) builds a state dict; `tmp_path` and `monkeypatch`
are built into pytest. Fixtures in `conftest.py` are shared across all test files.

**`tmp_path`.** A built-in fixture giving each test a fresh temporary directory,
auto-deleted afterwards. The correct way to test code that touches the filesystem
— never write to real project folders in a test.

**`monkeypatch`.** A built-in fixture that temporarily replaces an attribute,
env var, or function, and restores it automatically when the test ends. We use it
two ways: to swap the real LLM for a fake, and to point `config` paths at a temp dir.

**Mocking / test doubles.** A "fake" is a tiny object that mimics just enough of a
real dependency's API to drive your code. `test_score_candidate.py` fakes the
`model.with_structured_output(...).invoke(...)` chain so no real Ollama call
happens — that's how you unit-test code that talks to an external service.

---

## Running the tests

All commands use the project's virtualenv (`env/`):

```bash
# Run everything
./env/bin/python -m pytest

# Run one file
./env/bin/python -m pytest tests/test_routing.py

# Run one test, or one parametrized case
./env/bin/python -m pytest tests/test_routing.py::test_phone_alone_is_not_enough
./env/bin/python -m pytest -k "clamp"          # any test whose name matches "clamp"

# Stop at the first failure, and show local variables on failure
./env/bin/python -m pytest -x -l

# Coverage: how much of the code did the tests exercise?
./env/bin/python -m pytest --cov=agents --cov=workflows --cov=config --cov-report=term-missing
```

Install the test tools first (once):

```bash
./env/bin/python -m pip install -r requirements-dev.txt
```

---

## Reading a coverage report

```
Name              Stmts   Miss  Cover   Missing
agents/nodes.py      68     23    66%   53-70, 84-101, ...
workflows/graph.py   14     14     0%   1-27
```

- **Cover** = % of statements a test ran.
- **Missing** = line numbers never executed by any test.

Notice `nodes.py`'s missing lines are the **LLM-calling functions**
(`load_job_description`, `extract_resume_text`) and `graph.py` is 0%. That's not a
failure — it's *honest*: we chose not to unit-test code whose behavior depends on
a live model. Coverage is a **map of what's untested**, not a grade to maximize.
Chasing 100% by testing trivial lines is a common beginner trap.

---

## What is intentionally NOT tested here (and why)

- **The real LLM calls** (`extract_resume_text`, `load_job_description`). Their
  output depends on the model, so asserting exact values would be flaky. You
  verify these with an occasional **end-to-end run** (`python main.py`), not a
  unit test.
- **The compiled graph** (`workflows/graph.py`). Wiring is better checked by an
  **integration test** (below) than by unit tests.

---

## What to learn next (a roadmap for you as an engineer)

1. **An integration test for the graph.** Import `app` from `workflows.graph`,
   monkeypatch the model with a fake, `app.invoke({...})` a fake resume, and
   assert it routes correctly end-to-end. This covers the 0% in `graph.py` and
   proves the conditional edge is wired right — the natural complement to the unit
   tests here.
2. **Fixture scope & `autouse`.** Learn `@pytest.fixture(scope="module")` and
   `autouse=True` to share expensive setup.
3. **Markers.** Tag slow/integration tests (`@pytest.mark.slow`) and select them
   with `-m`, so the fast suite stays fast.
4. **`unittest.mock`.** `MagicMock` / `patch` are the stdlib alternative to hand-
   written fakes — worth knowing since you'll see them everywhere.
5. **Continuous Integration (CI).** Add a GitHub Actions workflow that runs
   `pytest` on every push. This is what turns tests from "nice to have" into a
   real safety net for a team.
6. **Test-Driven Development (TDD).** Try writing the test *first* for your next
   feature (e.g. the retry loop), watch it fail, then make it pass.
7. **Property-based testing** (`hypothesis`). Instead of hand-picking cases,
   generate hundreds automatically — great for logic like score clamping.
