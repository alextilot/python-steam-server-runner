PYTHON_VERSION ?= 3.13
VENV_NAME ?= server-runner

.PHONY: all setup clean install test

all: install test

setup:
	@echo "Setting up Python environment..."
	@pyenv install $(PYTHON_VERSION) || true # Install if not already present
	@pyenv virtualenv $(PYTHON_VERSION) $(VENV_NAME) || true # Create virtualenv if not already present
	@pyenv local $(VENV_NAME)
	@echo "Python environment setup complete. Run 'make install' to install dependencies."

install: setup
	@echo "Installing dependencies..."
	@pip install --upgrade pip
	@pip install -r requirements.txt
	@pip install -r requirements-dev.txt
	@echo "Dependencies installed."

test:
	@echo "Running tests..."
	@pytest # Or your preferred testing command
	@echo "Tests complete."

clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV_NAME)
	@pyenv virtualenv-delete $(VENV_NAME) || true
	@rm -f .python-version
	@echo "Cleanup complete."