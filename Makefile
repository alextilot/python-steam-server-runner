PYTHON_VERSION ?= 3.13
VENV_NAME ?= server-runner

.DEFAULT_GOAL := all
.PHONY: all setup install test clean lint format

all: install lint test

setup:
	@echo "Setting up Python environment..."
	@pyenv install -s $(PYTHON_VERSION)
	@pyenv virtualenv -f $(PYTHON_VERSION) $(VENV_NAME)
	@pyenv local $(VENV_NAME)
	@echo "Python environment setup complete. Run 'make install' to install dependencies."

install: setup
	@echo "Installing dependencies..."
	@python -m pip install --upgrade pip
	@python -m pip install -r requirements.txt
	@python -m pip install -r requirements-dev.txt
	@echo "Dependencies installed."

# New target for editable/dev install
dev-install: install
	@echo "Installing package in editable mode..."
	@python -m pip install -e .
	@echo "Editable install complete. You can now run 'server-runner' from anywhere."

lint:
	@echo "Running linter..."
	@ruff check src tests
	@black --check src tests
	@echo "Linting complete."

format:
	@echo "Formatting code..."
	@black src tests
	@ruff --fix src tests
	@echo "Code formatted."

test:
	@echo "Running tests..."
	@python -m pytest tests
	@echo "Tests complete."

clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV_NAME)
	@pyenv virtualenv-delete $(VENV_NAME) || true
	@rm -f .python-version
	@echo "Cleanup complete."
