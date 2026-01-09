# -------------------------------
# Config
# -------------------------------
VENV_NAME ?= server-runner

SRC := src
TESTS := tests

.DEFAULT_GOAL := help
.PHONY: help setup install dev lint format typecheck test check ci clean

# -------------------------------
# Help
# -------------------------------
help:
	@echo ""
	@echo "Targets:"
	@echo "  setup      Install Python + pyenv virtualenv"
	@echo "  install    Install runtime dependencies"
	@echo "  dev        Install dev dependencies + editable mode"
	@echo "  lint       Ruff + Black checks"
	@echo "  format     Auto-format code"
	@echo "  typecheck  Pyright"
	@echo "  test       Run pytest"
	@echo "  check      Lint + typecheck + test"
	@echo "  ci         Same as check"
	@echo "  clean      Remove pyenv virtualenv (optional)"
	@echo ""

# -------------------------------
# Ensure .python-version exists
# -------------------------------
check-python-version:
	@test -f .python-version || (echo "Error: .python-version file not found. Please create it with the Python version for pyenv." && exit 1)

# -------------------------------
# Setup pyenv environment
# -------------------------------
setup: check-python-version
	@PYTHON_VERSION=$$(cat .python-version-base 2>/dev/null || echo "3.12.11")
	@echo "Installing Python $$PYTHON_VERSION via pyenv..."
	@pyenv install -s $$PYTHON_VERSION
	@pyenv virtualenv -f $$PYTHON_VERSION $(VENV_NAME)
	@pyenv local $(VENV_NAME)
	@echo "Pyenv environment '$(VENV_NAME)' created."
	@echo "Python path: $$(pyenv which python)"
	@echo "Run 'make install' or 'make dev' next."


# -------------------------------
# Dependencies
# -------------------------------
install:
	@echo "Installing runtime dependencies..."
	@python -m pip install --upgrade pip
	@python -m pip install .
	@echo "Done."

dev: install
	@echo "Installing dev dependencies + editable mode..."
	@python -m pip install -e ".[dev]"
	@echo "Done."

# -------------------------------
# Quality Gates
# -------------------------------
lint:
	@ruff check $(SRC) $(TESTS)
	@black --check $(SRC) $(TESTS)

format:
	@ruff check --fix $(SRC) $(TESTS)
	@black $(SRC) $(TESTS)

typecheck:
	@pyright

test:
	@python -m pytest $(TESTS)

check: lint typecheck test
ci: check

# -------------------------------
# Cleanup
# -------------------------------
clean: clean-env
	@echo "Deleting all caches..." 
	@rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Caches deleted."

clean-env:
	@echo "Deleting pyenv virtualenv $(VENV_NAME)..."
	@pyenv virtualenv-delete -f $(VENV_NAME) || true
	@echo "Python environment deleted."
