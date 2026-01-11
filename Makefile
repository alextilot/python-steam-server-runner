# -------------------------------
# Config
# -------------------------------
PYTHON_VERSION := $(shell cat .python-version)
VENV_DIR := .venv

SRC := src
TESTS := tests

.DEFAULT_GOAL := help
.PHONY: help setup install dev lint format typecheck test check ci clean clean-env

# -------------------------------
# Help
# -------------------------------
help:
	@echo ""
	@echo "Targets:"
	@echo "  setup      Ensure Python version + create venv"
	@echo "  install    Install runtime dependencies"
	@echo "  dev        Install dev dependencies (editable)"
	@echo "  lint       Ruff + Black checks"
	@echo "  format     Auto-format code"
	@echo "  typecheck  Pyright"
	@echo "  test       Run pytest"
	@echo "  check      Lint + typecheck + test"
	@echo "  ci         Same as check"
	@echo "  clean      Remove caches"
	@echo "  clean-env  Remove virtual environment"
	@echo ""

# -------------------------------
# Guards
# -------------------------------
check-python-version:
	@test -f .python-version || (echo "Error: .python-version not found" && exit 1)

check-python:
	@python --version | grep -q "$(PYTHON_VERSION)" || \
	(echo "Error: active Python is not $(PYTHON_VERSION)" && exit 1)

# -------------------------------
# Setup
# -------------------------------
setup: check-python-version
	@echo "Using Python $(PYTHON_VERSION)"
	@pyenv install -s $(PYTHON_VERSION)
	@pyenv local $(PYTHON_VERSION)
	@test -d $(VENV_DIR) || python -m venv $(VENV_DIR)
	@echo "Virtualenv created at $(VENV_DIR)"
	@echo "Activate with: source $(VENV_DIR)/bin/activate"

# -------------------------------
# Dependencies
# -------------------------------
install: check-python
	@$(VENV_DIR)/bin/python -m pip install --upgrade pip
	@$(VENV_DIR)/bin/python -m pip install .

dev: install
	@$(VENV_DIR)/bin/python -m pip install -e ".[dev]"

# -------------------------------
# Quality Gates
# -------------------------------
lint:
	@$(VENV_DIR)/bin/ruff check $(SRC) $(TESTS)
	@$(VENV_DIR)/bin/black --check $(SRC) $(TESTS)

format:
	@$(VENV_DIR)/bin/ruff check --fix $(SRC) $(TESTS)
	@$(VENV_DIR)/bin/black $(SRC) $(TESTS)

typecheck:
	@$(VENV_DIR)/bin/pyright

test:
	@$(VENV_DIR)/bin/python -m pytest $(TESTS)

check: lint typecheck test
ci: check

# -------------------------------
# Cleanup
# -------------------------------
clean:
	@rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} +

clean-env:
	@rm -rf $(VENV_DIR)
	@echo "Virtual environment removed"

