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

### Lint (astral-sh/ruff-pre-commit)

| Hook ID | Purpose | Files Affected |
|---------|---------|----------------|
| `ruff-check` | Lints against the rule set in `pyproject.toml` | `.py` |

Pinned to `v0.16.4`, which is the version the `lint` job in `.github/workflows/checks.yml`
installs. **These two pins are one decision.** A hook running a different ruff than CI gives a
contributor a clean commit and a red pipeline, which is worse than having no hook at all — it
teaches them the hook cannot be trusted. Raise both together, run `ruff check .` on the new
version first, and fix what it finds in the same change.

`ruff format` is not enabled, here or in CI. It would rewrite most of the repository's Python
files in one commit, and this is a repository whose Python exists to be read. `E501` at
line-length 100 already holds the one formatting property that matters for reading two files
side by side.

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

**Not for `ruff-check`.** `autoupdate` moves every `rev` to the newest tag, which silently breaks
the pin agreement with the `lint` job in CI. If it has already moved the ruff entry, either revert
it or raise `checks.yml` to match in the same commit.

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

The same checks that run locally also run in CI (via `.github/workflows/checks.yml`), but the
local set is a subset: the hooks lint, syntax-check, and validate the directories you touched,
while CI additionally runs the write-boundary suites, the handler tests, the package builds, the
link check, `tflint`, `checkov`, and a gitleaks scan over the full history. CI is the authority.
`git commit --no-verify` skips every hook here, which is the other reason nothing in this file is
a gate.

`tflint` and `checkov` are deliberately CI-only. Both sweep the whole `infra/` tree rather than
the files in your commit — tflint because a module's `required_providers` block is a property of
the directory and not of the line you edited, checkov because its findings are cross-resource. A
hook that re-scans thirty modules to check a one-line comment change is a hook people disable.
Run them by hand when you touch `infra/`; CONTRIBUTING.md carries both commands.

## Configuration File

The hooks are defined in `.pre-commit-config.yaml` at the repository root.
Modifying this file requires running `pre-commit autoupdate` to pull new hook versions.
