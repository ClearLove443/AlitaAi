# Alita AI

Alita is an AI coding agent project that helps developers with code generation, analysis, and automation.

## Setup

1. Install Poetry (dependency management):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Activate virtual environment:
```bash
poetry shell
```

## Project Structure

```
alita/
├── core/           # Core AI agent functionality
├── api/            # API endpoints
└── utils/          # Utility functions

frontend/           # Frontend application
```

## Development

- Format code: `poetry run black .`
- Sort imports: `poetry run isort .`
- Run tests: `poetry run pytest`