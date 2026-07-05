# Contributing

Thanks for your interest in CVision!

## Getting started

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Install dependencies:
   ```
   pip install -e ".[test]"
   ```
4. Install pre-commit hooks:
   ```
   pip install pre-commit && pre-commit install
   ```
5. Run the test suite to verify everything works:
   ```
   python -m pytest tests/ -v --cov=api --cov=auth --cov=models --cov=utils --cov=agents --cov=config
   ```

## Code quality

- **Ruff** is used for linting and formatting (`ruff check . && ruff format --check .`)
- **mypy** is used for static type checking (`mypy .`)
- **pre-commit** runs on every PR — run `pre-commit run --all-files` before pushing
- All new code must include tests (pytest with coverage)
- Coverage threshold is **60%** (module-level, enforced in CI)

## Pull request guidelines

- Keep PRs focused on a single concern
- Write a clear title and description explaining what and why
- Reference any related issues
- Ensure CI passes (lint, typecheck, test, audit, docker, container-scan)

## Project structure

```
├── api.py                 # FastAPI application
├── agents/                # LangGraph agents (cv_parser, cv_analyzer, etc.)
├── auth/                  # Authentication (fastapi-users)
├── models/                # Pydantic schemas + SQLAlchemy models
├── utils/                 # File handling, ingest, retriever
├── graph/                 # LangGraph workflow definition
├── frontend/              # React + Vite frontend
├── tests/                 # pytest test suite
└── .github/workflows/     # CI/CD definitions
```

## Questions?

Open a [GitHub Discussion](https://github.com/DEPI-GradProject/CVision/discussions) for questions or ideas.
