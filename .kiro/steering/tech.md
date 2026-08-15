# Technical Steering

- Python 3.11+ with a `src/` package, Pydantic v2, and pinned dependencies.
- Use Strands Agents supported APIs only; currently target `strands-agents==1.52.0`.
- Keep provider SDK details behind `LLMProvider`; use environment configuration and no hardcoded secrets.
- Prefer deterministic Python for routing, validation, review policy, and obvious cases.
- Public functions are typed; use small modules, concise docstrings, Ruff, mypy, and pytest.
- Do not add dependencies or abstractions without a demonstrated MVP need.
