---
name: python-env
description: Procedure for creating, repairing, rebuilding, exporting, and validating Python environments (conda, uv, venv/pip) with minimal disruption. Use when a task needs packages installed, an environment fixed or rebuilt, or an environment spec exported.
---

# Python Environments

## Identify First

- Find the target environment and the goal before changing anything.
- Use the tool the project already uses:
  - `environment.yml` or an existing conda env: use conda
  - `uv.lock` or `[tool.uv]`: use uv
  - `requirements*.txt` with `.venv`: use venv and pip
  - `poetry.lock`: use poetry
- Never modify `base`, the system or global Python, unrelated environments, or shell startup files
  unless the user explicitly asks.

## Change Rules

- For existing environments, make the smallest targeted repair and avoid version churn.
- New or rebuilt environments start from the smallest correct spec. Pin versions only when
  reproducibility or compatibility requires it.
- Conda:
  - Prefer conda packages. Use pip only for packages conda lacks.
  - Run commands with `conda run -n <env> ...` instead of activating.
- Use pip only as `python -m pip` from the target interpreter. After any pip install, run
  `python -m pip check`.
- When you mix package managers, report the compatibility risk.
- If an environment is badly conflicted, explain whether a rebuild is safer than a repair before
  doing either.

## Validate Narrowly

Check in this order: the environment exists, the interpreter version, package metadata (`pip show`
or `conda list <pkg>`), an import test, then the task's own command. Report service, credential, or
network blockers separately from environment health.

## Report

The environment and the action taken, the files changed (specs or lockfiles), the exact commands
run, the validation results, and any remaining reproducibility risk.
