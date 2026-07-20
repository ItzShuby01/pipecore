.PHONY: install compile-alg run-alg run-asm run-bin lint typecheck test check all clean

ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(ARGS):;@:)

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

compile-alg:
	python -m src.main compile-alg $(ARGS) $(if $(OUT),OUT=$(OUT))

run-alg:
	python -m src.main run-alg $(ARGS) $(MODE_FLAG)

run-asm:
	python -m src.main run-asm $(ARGS) $(MODE_FLAG)

run-bin:
	python -m src.main run-bin $(ARGS) $(MODE_FLAG)

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

check: lint typecheck test

all: check

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.bin" -delete
	find . -type f -name "*.lst" -delete