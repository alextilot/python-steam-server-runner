# Python Virtual Environment Setup Guide

Setting up Python virtual environments is a best practice for isolating project dependencies and managing multiple Python versions. This guide covers using `pyenv`, `virtualenv`, and `pyenv-virtualenv` for any Python project.

## Quick Reference

| Command                         | Purpose                        |
| ------------------------------- | ------------------------------ |
| `pyenv install --list`          | List available Python versions |
| `pyenv install 3.13.7`          | Install Python version         |
| `pyenv global 3.13.7`           | Set global Python version      |
| `pyenv virtualenv 3.13.7 myenv` | Create virtual environment     |
| `pyenv local myenv`             | Set project environment        |
| `pyenv activate myenv`          | Manually activate environment  |
| `pyenv deactivate`              | Deactivate environment         |

## 1. Install Dependencies

### Update Homebrew

Ensure Homebrew is up to date:

```sh
brew update
```

### Install `pyenv`

`pyenv` lets you easily switch between multiple versions of Python.

**For new installations:**

```sh
brew install pyenv
```

**For existing installations:**

```sh
brew upgrade pyenv
```

### Install `pyenv-virtualenv`

`pyenv-virtualenv` integrates `pyenv` with `virtualenv` to manage isolated environments.

**For new installations:**

```sh
brew install pyenv-virtualenv
```

**For existing installations:**

```sh
brew upgrade pyenv-virtualenv
```

## 2. Configure Shell Profile

Add the following configuration to your shell profile:

**For Zsh users (`~/.zshrc`):** \
**For Bash users (`~/.bashrc`):**

```sh
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

### Apply Changes

Restart your terminal or reload your shell configuration:

```sh
# For Zsh
source ~/.zshrc

# For Bash
source ~/.bashrc
```

## 3. Python Version Management

### List Available Python Versions

See all available Python versions for installation:

```sh
pyenv install --list
```

### Install a Python Version

Install the latest stable version (e.g., 3.13.7):

```sh
pyenv install 3.13.7
```

### Set Global Python Version

Set the default Python version for your system:

```sh
pyenv global 3.13.7
```

---

## 4. Virtual Environment Management

### Create a Virtual Environment

Navigate to your project folder and create a new virtual environment:

```sh
pyenv virtualenv 3.13.7 <env-name>
```

**Example:**

```sh
pyenv virtualenv 3.13.7 myproject-env
```

> **Note:** Replace `<env-name>` with a descriptive name for your project environment.

### Set Project-Specific Environment

To automatically activate a virtual environment when entering a project folder:

```sh
pyenv local <env-name>
```

> This creates a `.python-version` file in the current directory.

### Manual Activation/Deactivation

**Activate the environment:**

```sh
pyenv activate <env-name>
```

**Deactivate the environment:**

```sh
pyenv deactivate
```

> **Tip:** Your shell prompt will show the environment name when active (e.g., `(myproject-env) $`).

---

## 5. Managing Dependencies

### Install Dependencies

**For main project dependencies:**

```sh
pip install -r requirements.txt
```

### Save Dependencies

Create a `requirements.txt` file with current dependencies:

```sh
pip freeze > requirements.txt
```

## Best Practices

- **Use descriptive names** for virtual environments (e.g., `project-name-env`)
- **Set local environments** for each project using `pyenv local`
- **Keep requirements files updated** when adding new dependencies
- **Use separate environments** for different projects to avoid conflicts

