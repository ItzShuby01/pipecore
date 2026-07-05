.PHONY: install run lint typecheck test check all clean

ARGS ?=

install:
	pip install -e ".[dev]"

run:
	python -m src.main $(ARGS)

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

check: lint typecheck test

all: run check

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +