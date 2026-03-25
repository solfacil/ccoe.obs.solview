.PHONY: test lint typecheck

test-cov:
	uv run pytest -v --cov=src --cov-report=term-missing

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check solview/

format:
	uv run ruff format solview/ tests/

typecheck:
	uv run ty check solview/

pre-commit:
	uv run pre-commit run --all-files

quality: test-cov format lint typecheck pre-commit
