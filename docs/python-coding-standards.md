# Python Code Standards Tools - Best Practices Guide

A comprehensive guide for implementing code quality tools in Python projects using modern, fast, and effective tooling.

## 📁 Configuration Files

This guide references external configuration files for easy copying:

- **[config/pyproject.toml](./config/pyproject.toml)** - Complete Ruff and Pyright configuration
- **[config/.pre-commit-config.yaml](./config/.pre-commit-config.yaml)** - Complete pre-commit setup

> 💡 **Tip**: Click the file links above to view the complete, ready-to-use configuration files.

## Quick Reference

| Tool           | Purpose             | Configuration File        | Command                      |
| -------------- | ------------------- | ------------------------- | ---------------------------- |
| **Ruff**       | Linter + Formatter  | `pyproject.toml`          | `ruff check` / `ruff format` |
| **Pyright**    | Static Type Checker | `pyproject.toml` | `pyright .` |
| **pre-commit** | Git Hooks Manager   | `.pre-commit-config.yaml` | `pre-commit run --all-files` |

---

## Why Code Standards Tools Matter

### The Problem

Without standardized tooling, Python codebases suffer from:

- **Inconsistent formatting** across team members
- **Runtime errors** that could be caught statically
- **Code smells** and anti-patterns going unnoticed
- **Technical debt** accumulating over time
- **Reduced productivity** due to code review debates about style

### The Solution

Code standards tools provide:

- **Automated consistency** - No more debates about formatting
- **Early error detection** - Catch bugs before they reach production
- **Improved readability** - Clean, consistent code is easier to understand
- **Enhanced maintainability** - Well-structured code is easier to modify
- **Team productivity** - Focus on logic, not style discussions

### Core Principles

1. **Speed** - Tools should be fast enough for real-time feedback
2. **Consistency** - Enforce uniform standards across the entire codebase
3. **Automation** - Minimize manual intervention and decision fatigue
4. **Integration** - Work seamlessly with editors and CI/CD pipelines

---

## Our Toolchain Strategy

We'll implement a modern, high-performance toolchain:

### 1. **Ruff** - The All-in-One Solution

- **What**: Ultra-fast Python linter and formatter written in Rust
- **Why**: 10-100x faster than traditional tools (flake8, black, isort combined)
- **Replaces**: flake8, black, isort, bandit, and dozens of other tools

### 2. **Pyright/Pylance** - Modern Type Checking

- **What**: Microsoft's fast, modern static type checker for Python
- **Why**: Superior type inference and IDE integration, 10x faster than mypy
- **Benefit**: Real-time error detection and better developer experience

### 3. **pre-commit** - Automation Layer

- **What**: Git hooks framework
- **Why**: Ensures code standards are enforced before commits
- **Benefit**: Prevents bad code from entering the repository

---

## Implementation Guide

> **Prerequisite**: Ensure you have a Python virtual environment set up using our [Python Virtual Environment Setup Guide](./setting-up-python-virtual-environments.md).

### Step 1: Install the Tools

```bash
pip install ruff pyright pre-commit
```

### Step 2: Configure Ruff

📁 **Copy the complete configuration file**: [`config/pyproject.toml`](./config/pyproject.toml)

Create or update your `pyproject.toml` file:

```toml
[tool.ruff]
# Set the maximum line length to 88 (Black's default)
line-length = 88
fix = true
target-version = "py38"

[tool.ruff.lint]
# Enable comprehensive rule sets
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings  
    "F",    # pyflakes
    "I",    # isort
    # ... see full configuration in linked file above
]

[tool.ruff.format]
quote-style = "double"

[tool.ruff.lint.isort]
known-first-party = ["your_package_name"]
```

### Step 3: Configure Pyright (Modern Type Checking)

📁 **Copy the complete configuration file**: [`config/pyproject.toml`](./config/pyproject.toml)

Pyright configuration is included in your `pyproject.toml` file alongside Ruff:

```toml
[tool.pyright]
include = ["src", "tests"]
exclude = ["**/__pycache__", "**/.git", "**/.venv", ...]
typeCheckingMode = "strict"
pythonVersion = "3.11"
# ... see full configuration in linked file above
```

**Benefits of pyproject.toml approach:**
- **Single configuration file** for all tools
- **Version controlled** with your project  
- **Standard Python packaging** approach
- **Better tool integration** and discoverability

### Step 4: Set Up Pre-commit Hooks

📁 **Copy the complete configuration file**: [`config/.pre-commit-config.yaml`](./config/.pre-commit-config.yaml)

Create `.pre-commit-config.yaml` in your project root:

```yaml
repos:
  # Ruff linter and formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  
  # Type checking with Pyright  
  - repo: https://github.com/RobertCraigie/pyright-python
    rev: v1.1.338
    hooks:
      - id: pyright
      
  # ... see full configuration in linked file above
```

### Step 5: Install and Activate Pre-commit

```bash
# Install the git hooks
pre-commit install

# Run on all files initially
pre-commit run --all-files
```

---

## Daily Workflow

### During Development

**Manual checks:**
```bash
# Check for linting issues
ruff check .

# Auto-fix issues where possible
ruff check --fix .

# Format code
ruff format .

# Type checking
pyright .
```

**IDE Setup for Automatic Checks and Format-on-Save:**

> **Note**: Tools will automatically read their configuration from `pyproject.toml`, but editors need setup to know **when** to run them (on save, on type, etc.) and **which** tools to use for formatting.

#### VS Code
1. Install **Python extension** (includes Pylance for type checking)
2. Install **Ruff extension** by Astral Software
3. Configure in `settings.json`:

```json
{
  // Enable Ruff extension
  "ruff.enable": true,
  
  // Python/Pylance uses pyproject.toml automatically
  "python.analysis.typeCheckingMode": "strict",
  
  // Format on save with Ruff (uses pyproject.toml config)
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": "explicit",
    "source.organizeImports.ruff": "explicit"
  },
  
  // Set Ruff as default formatter
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

#### PyCharm/IntelliJ IDEA
1. **Install Ruff plugin** from marketplace
2. **Enable auto-actions**:
   - **Settings** → **Tools** → **Actions on Save**
   - Enable "Reformat code" and "Ruff"
   - Ruff will use your `pyproject.toml` configuration automatically

#### Neovim
Using `lazy.nvim` plugin manager:

```lua
-- Ruff LSP for linting and formatting
{
  "neovim/nvim-lspconfig",
  config = function()
    local lspconfig = require('lspconfig')
    
    -- Ruff LSP setup
    lspconfig.ruff_lsp.setup({
      init_options = {
        settings = {
          args = {"--fix-all"}
        }
      }
    })
    
    -- Pyright for type checking
    lspconfig.pyright.setup({
      settings = {
        python = {
          analysis = {
            typeCheckingMode = "strict",
          },
        },
      },
    })
  end,
}

-- Auto-format on save
{
  "stevearc/conform.nvim",
  config = function()
    require("conform").setup({
      formatters_by_ft = {
        python = { "ruff_format" },
      },
      format_on_save = {
        timeout_ms = 500,
        lsp_fallback = true,
      },
    })
  end,
}
```

#### Vim (with vim-lsp)
```vim
" In your .vimrc
if executable('ruff-lsp')
  au User lsp_setup call lsp#register_server({
    \ 'name': 'ruff-lsp',
    \ 'cmd': {server_info->['ruff-lsp']},
    \ 'allowlist': ['python'],
    \ })
endif

if executable('pyright-langserver')
  au User lsp_setup call lsp#register_server({
    \ 'name': 'pyright',
    \ 'cmd': {server_info->['pyright-langserver', '--stdio']},
    \ 'allowlist': ['python'],
    \ })
endif

" Auto-format on save
augroup AutoFormat
  autocmd!
  autocmd BufWritePre *.py call execute('LspDocumentFormat')
augroup END
```

#### Emacs (with lsp-mode)
```elisp
;; In your Emacs config
(use-package lsp-mode
  :hook ((python-mode . lsp))
  :config
  (lsp-register-client
   (make-lsp-client :new-connection (lsp-stdio-connection "ruff-lsp")
                    :major-modes '(python-mode)
                    :server-id 'ruff-lsp)))

(use-package lsp-pyright
  :ensure t
  :hook (python-mode . (lambda ()
                        (require 'lsp-pyright)
                        (lsp))))

;; Auto-format on save
(add-hook 'python-mode-hook
          (lambda ()
            (add-hook 'before-save-hook 'lsp-format-buffer nil t)
            (add-hook 'before-save-hook 'lsp-organize-imports nil t)))
```

**Benefits of IDE Integration:**
- **Real-time feedback** - See errors as you type
- **Automatic fixing** - Code formatting and import organization on save
- **Consistent experience** - Same tools across different editors
- **Productivity boost** - No manual formatting or linting commands needed

### Before Committing

Pre-commit hooks will automatically run, but you can also run manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff
pre-commit run pyright
```

### In CI/CD Pipeline

Add to your GitHub Actions, GitLab CI, or similar:

```yaml
- name: Run code quality checks
  run: |
    pip install ruff pyright
    ruff check .
    ruff format --check .
    pyright .
```

---

## Tool-Specific Benefits

### Ruff Advantages

- **Speed**: 10-100x faster than alternatives
- **Comprehensive**: Replaces multiple tools (flake8, black, isort, etc.)
- **Modern**: Written in Rust, actively maintained
- **Compatible**: Drop-in replacement for existing tools
- **Configurable**: Extensive rule customization options

### Pyright/Pylance Benefits

- **Speed**: 10x faster than mypy, built in Rust-like performance
- **Modern Python**: Excellent support for latest typing features (TypedDict, Literal, etc.)
- **Superior Inference**: Better at understanding types without explicit annotations
- **IDE Integration**: Best-in-class VS Code integration via Pylance
- **Real-time Feedback**: Instant type checking as you type
- **Better Error Messages**: More helpful and actionable error descriptions

### pre-commit Benefits

- **Automation**: No manual step to remember
- **Consistency**: Same checks for all team members
- **Fast Feedback**: Catch issues before they reach CI/CD
- **Extensible**: Easy to add new tools and checks
- **Git Integration**: Seamless workflow integration

---

## Best Practices

### Configuration Management

- **Centralize config** in `pyproject.toml` when possible
- **Version pin** your tools in `requirements-dev.txt`
- **Document exceptions** when ignoring specific rules
- **Keep rules strict** - be permissive only when necessary

### Team Adoption

- **Start gradually** - introduce one tool at a time
- **Provide training** on the tools and their benefits
- **Create documentation** specific to your project's needs
- **Address concerns** about productivity and learning curve

### Maintenance

- **Update regularly** - tools improve rapidly
- **Monitor performance** - ensure tools remain fast
- **Review rules** periodically to ensure they add value
- **Gather feedback** from the team on rule effectiveness

### Common Pitfalls to Avoid

- **Over-configuration** - start with defaults, customize only when needed
- **Ignoring too much** - defeats the purpose of having standards
- **Inconsistent enforcement** - make sure everyone uses the same setup
- **Neglecting updates** - newer versions often have better defaults

---

## Multi-Editor Setup Guide

### VS Code Setup

1. Install the **Python extension** (includes Pylance)
2. Configure settings in `settings.json`:

```json
{
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.inlayHints.functionReturnTypes": true
}
```

### PyCharm/IntelliJ Setup

**Option 1: Native Support (Recommended)**

1. Go to **Settings** → **Tools** → **Python Integrated Tools**
2. Set **Type checker** to **Pyright**
3. Enable **Type checking inspection**

**Option 2: LSP Plugin**

1. Install **LSP Support Plugin**
2. Configure Pyright LSP server path
3. Enable real-time type checking

### Neovim Setup

Using `nvim-lspconfig` with lazy.nvim:

```lua
-- In your Neovim config
{
  "neovim/nvim-lspconfig",
  config = function()
    local lspconfig = require('lspconfig')

    -- Pyright setup
    lspconfig.pyright.setup({
      settings = {
        python = {
          analysis = {
            typeCheckingMode = "strict",
            diagnosticMode = "workspace",
            inlayHints = {
              functionReturnTypes = true,
            },
          },
        },
      },
    })
  end,
}
```

### Universal LSP Setup (Other Editors)

1. Install Pyright globally: `npm install -g pyright`
2. Configure your editor's LSP client to use `pyright-langserver`
3. Point to your project's `pyrightconfig.json`

---

## Troubleshooting

### Common Issues

**Pyright not found in PyCharm:**

```bash
# Install Pyright globally for system access
npm install -g pyright

# Or use pip version
pip install pyright
```

**Neovim LSP not starting:**

```bash
# Check if Pyright is available
which pyright

# Install Node.js if missing (required for Pyright)
# macOS: brew install node
# Ubuntu: sudo apt install nodejs npm
```

**Different type checking results across editors:**

- Ensure all editors use the same `pyrightconfig.json`
- Check Python interpreter path is consistent
- Verify same virtual environment is being used

**Performance issues in large projects:**

```json
// In pyrightconfig.json
{
  "exclude": ["**/node_modules", "**/__pycache__", "build/**"],
  "useLibraryCodeForTypes": false,
  "reportGeneralTypeIssues": false
}
```

**Ruff conflicts with existing formatters:**

```bash
# Remove old formatters
pip uninstall black isort flake8

# Clean up old config files
rm setup.cfg .flake8 pyproject.toml
```

**Pyright errors in third-party libraries:**

```json
// In pyrightconfig.json
{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false,
  "reportUnknownMemberType": false
}
```

**Pre-commit hooks failing:**

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Clear cache if needed
pre-commit clean
```

### Performance Optimization

**For large codebases:**

```json
// In pyrightconfig.json
{
  "exclude": ["migrations/", "build/", "dist/", "**/node_modules"],
  "useLibraryCodeForTypes": false
}
```

---

## Migration from Legacy Tools

### From Black + flake8 + isort

```bash
# Remove old tools
pip uninstall black flake8 isort

# Install Ruff
pip install ruff

# Ruff handles all three use cases
ruff check .     # Replaces flake8
ruff format .    # Replaces black
# Import sorting is automatic with Ruff
```

### Update your CI/CD

```yaml
# Old
- run: black --check .
- run: flake8 .
- run: isort --check-only .

# New
- run: ruff check .
- run: ruff format --check .
```

---

## Conclusion

This toolchain provides:

- **Lightning-fast feedback** during development
- **Consistent code quality** across your entire project
- **Automated enforcement** of best practices
- **Modern, maintainable** Python code

By implementing these tools, your team will spend less time discussing code style and more time building features that matter.

**Next Steps:**

1. Set up the tools following this guide
2. Configure your editor for real-time feedback
3. Train your team on the new workflow
4. Monitor and adjust rules based on team feedback

