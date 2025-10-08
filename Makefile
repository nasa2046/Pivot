.PHONY: install lint format typecheck test check

install:
	python -m pip install --upgrade pip
	pip install -e .[dev]

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src

test:
	pytest

check: format lint typecheck test