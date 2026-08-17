# Pre-commit Hooks

> **Purpose:** Catch errors before they reach CI using local git hooks.
> **Status:** Active configuration in `.pre-commit-config.yaml`

## Installation

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

3. (Optional) Run hooks on all files manually:
   ```bash
   pre-commit run --all-files
   ```

## Configured Hooks

### General Hooks (pre-commit/pre-commit-hooks)

| Hook ID | Purpose | Files Affected |
|---------|---------|----------------|
| `trailing-whitespace` | Removes trailing whitespace | All files |
| `end-of-file-fixer` | Ensures files end with a newline | All files |
| `check-yaml` | Validates YAML syntax | `.yaml`, `.yml` |
| `check-added-large-files` | Blocks large files (>500kb) | All files |

### Project-Specific Hooks

#### Terraform Validate
- **ID:** `terraform-validate`
- **Purpose:** Validates each Terraform directory that the commit touches
- **Trigger:** Changes to `.tf` or `.tfvars` files in `infra/`
- **Command:** `terraform init -backend=false` then `terraform validate -no-color`, per directory
- **Working Directory:** each changed file's own directory, deduplicated

`terraform validate` has no `-recursive` flag — that flag belongs to `terraform fmt`. Validation is
also per-directory by nature: it needs an initialized working directory, which is why the hook runs
`terraform init -backend=false` first. The hook therefore derives the directory list from the staged
files and validates each one once, rather than making a single recursive call.

Because `init` dominates the runtime, a commit spanning many modules is slow. That is the trade-off
for catching the errors `terraform fmt` cannot see: a wrong-but-valid value in a valid attribute.

#### Python Compile
- **ID:** `python-compile`
- **Purpose:** Syntax-checks all Python files
- **Trigger:** Changes to `.py` files
- **Command:** `python3 -m py_compile`

## Usage

### Running on Modified Files
Pre-commit automatically runs on `git commit`. To manually run on staged files:
```bash
pre-commit run
```

### Running on All Files
```bash
pre-commit run --all-files
```

### Updating Hooks
To update to the latest versions of the hooks:
```bash
pre-commit autoupdate
```

### Bypassing Hooks
To skip pre-commit checks for a single commit:
```bash
git commit --no-verify -m "your message"
```
*Note: Use sparingly. Hooks exist to prevent errors in CI.*

## Troubleshooting

### Hook Fails but Changes are Valid
If a hook fails unexpectedly, check:
1. File encoding (UTF-8 recommended)
2. Line endings (LF recommended, not CRLF)
3. Syntax errors in YAML or Terraform

### Slow Performance
Run specific hooks only:
```bash
pre-commit run trailing-whitespace --all-files
```

### Hook Not Running
Ensure:
1. Hooks are installed: `pre-commit install`
2. You're in the correct git repository
3. The file type matches the hook's `files` pattern

## CI Integration

The same checks that run locally also run in CI (via `.github/workflows/checks.yml`).
Pre-commit hooks help you catch issues before pushing.

## Configuration File

The hooks are defined in `.pre-commit-config.yaml` at the repository root.
Modifying this file requires running `pre-commit autoupdate` to pull new hook versions.
