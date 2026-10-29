---
domain: process
summary: The writer lead runs on Fable like the planner; writer-worker stays Opus; the supervisor may dispatch writer on opus for short low-stakes prose
affects: [pack/agents/supervisor.md, pack/agents/writer.md, pack/agents/writer-worker.md, pack/skills/agent-authoring/SKILL.md, docs/architecture.md]
verified: 2026-10-29
source: user 2026-10-24 ("make writer fable lead"; "(unless supervisor can change the model but that may be too much scaffolding)")
supersedes: .supervisor/archive/memory/decisions/2026-10-24-writer-lead-runs-on-fable.md
---
The writer lead runs on Fable. There is no Fable `writer-worker` override; `writer-worker` stays Opus for source extraction and the rare parallel drafter. The supervisor may pass `model: opus` on a `writer` dispatch for short, low-stakes prose (emails, notes, small edits), never for proposals, papers or external-facing text; the Agent tool's `model` parameter already overrides frontmatter, so no scaffolding is needed.
Why: under `2026-10-24-every-lead-does-a-single-unit-itself-and.md` the lead drafts and revises itself, and the owner's writing is mostly high-stakes scientific prose, so drafting and critic-round judgment run on the strongest model.
Rejected: an Opus lead with Fable on request (cheaper, but splits drafting between lead and worker depending on phrasing).
Cost impact is unmeasured; re-check with the audit tool's lead-context metric.
