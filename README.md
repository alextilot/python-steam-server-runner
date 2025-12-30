# ServerRunner

**ServerRunner** is a Python command-line tool for running and managing a Steam game server.
It provides a structured CLI for configuring server credentials, Steam paths, and game metadata, while supporting clean local development via `pyenv`, `make`, and modern Python tooling.

## Requirements

* **Python** `3.13`
* **pyenv** and **pyenv-virtualenv**
* **make**
* Linux or macOS (Windows may work with WSL)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/alextilot/python-steam-server-runner.git
cd python-steam-server-runner
```

---

### 2. Set up the Python environment

This will:

* Install Python `3.13` (if missing)
* Create a `pyenv` virtualenv
* Set the local Python version

```bash
make setup
```

---

### 3. Install dependencies

```bash
make install
```

---

## Usage

ServerRunner is invoked via the command line and requires Steam credentials and game metadata.

### CLI Arguments

| Flag              | Description                |
| ----------------  | -------------------------- |
| `--app-id`        | Steam App ID               |
| `--steam-path`    | Path to Steam installation |
| `--api-base-url`  | Steam game API base URL    |
| `--api-auth-type` | Steam game API username    |
| `--api-username`  | Steam game API username    |
| `--api-password`  | Steam game API password    |
| `--api-token`     | Steam game API username    |

### Additional Arguments

Any extra arguments passed after the known flags are forwarded directly to the game server process.

---

### Example

```bash
python -m server_runner \
  --api-auth-type basic \
  --api-username myuser \
  --api-password mypass \
  --api-base-url https://api.steampowered.com \
  --app-id 2394010 \
  --steam-path /opt/steam \
  -- -port=8211 -players=16
```

In this example:

* Everything after `--` is treated as **game arguments**
* These are collected into `game_args` and passed through untouched

---

## Development Commands

### Run all checks (default)

```bash
make
```

Equivalent to:

```bash
make install lint test
```

---

### Linting

```bash
make lint
```

Uses:

* `ruff`
* `black` (check mode)

---

### Formatting

```bash
make format
```

Automatically formats and fixes issues where possible.

---

### Testing

```bash
make test
```

Runs the full test suite via `pytest`.

---

### Cleanup

Remove the virtual environment and local Python version file:

```bash
make clean
```
