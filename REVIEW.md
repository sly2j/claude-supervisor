# Review Rules

Rules for reviewers of this repo: Anthropic Code Review and the pack's `critic`.

## Always check

- `deploy`: stdlib-only and Python 3.9 syntax (`/usr/bin/python3 -m py_compile deploy`); every
  error, WARN and FAIL message says what went wrong and names the next command as `./deploy ...`
  (`deploy` is not on PATH); validation (source, registry, launcher conflict, token file) runs
  before the first write; no traceback reaches the user; `migrate` and `uninstall` never leave
  a half-done state without saying so.
- `tests/`: every changed `deploy` branch has a test; tests run against a temp HOME with a
  whitelisted environment, never the real `~/.claude` or `~/.config/claude-supervisor`.
- `pack/`: `pack/skills/agent-authoring/SKILL.md` conventions; body word caps are not raised;
  `docs/architecture.md` matches each agent's frontmatter (name, model, effort, tools);
  cross-references to agents, skills, sections and lines resolve; a new rule cites an observed
  failure.
- `README.md` and `docs/deploy.md`: every command is copy-pasteable with flags that exist;
  stated behavior matches `deploy`; prerequisites and the next step are stated for a new user.
- Every change set on `main` bumps `VERSION` once (`CLAUDE.md`).

## Severity here

- BLOCKING (Important): data loss, a half-done install, uninstall or migrate state, a traceback,
  a message or doc step that leaves the user stuck, a failing test, a word-cap violation.
- SHOULD: a message without a next step, a doc that disagrees with the tool, a stale reference.
- Do not report: line length and word counts under the caps (linted), anything under
  `.supervisor/archive/`, style in test fixtures.
- Do not report these `deploy` hardenings (a full review rejected them) unless a failure was
  observed: quote escaping of launcher values (config dir, prefix, base URL, token path); a lock
  on the `installs.json` registry; rejecting an empty `--target ""` or `--prefix ""` instead of
  falling back to the default; UTF-8 BOM handling in frontmatter parsing.

## Evidence

- For a claim about `deploy` behavior, run the command against a temp HOME and quote the output.
