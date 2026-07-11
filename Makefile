.PHONY: install run lint typecheck test check all clean

RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

ifeq ($(mode),verbose)
    MODE_FLAG := verbose
else ifeq ($(mode),v)
    MODE_FLAG := verbose
else ifeq ($(mode),silent)
    MODE_FLAG := silent
else ifeq ($(mode),s)
    MODE_FLAG := silent
endif

install:
	pip install -e ".[dev]"

run:
	python -m src.main $(RUN_ARGS) $(MODE_FLAG)

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
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.bin" -delete
	find . -type f -name "*.lst" -delete