---
domain: process
summary: writer lead runs on Fable like the planner; no Fable writer-worker override; writer-worker stays Opus; supervisor may dispatch writer on opus for short low-stakes prose
affects: [pack/agents/supervisor.md, pack/agents/writer.md, pack/agents/writer-worker.md, pack/skills/agent-authoring/SKILL.md, docs/architecture.md]
verified: 2026-10-24
source: user 2026-10-24 ("make writer fable lead"; "(unless supervisor can change the model but that may be too much scaffolding)")
supersedes:
---
The writer lead's model moves from Opus to Fable, like the planner. The "strongest drafter on request" override (a `writer-worker` with `model: fable`) is removed as moot; `writer-worker` stays Opus for source extraction and the rare parallel-drafter case. Two per-call model overrides remain: planner -> critic (fable) and supervisor -> writer (opus). The supervisor may pass `model: opus` on the `writer` dispatch for short, low-stakes prose (emails, notes, small edits of existing text), never for proposals, papers or external-facing text. No scaffolding is needed: the Agent tool's `model` parameter already overrides frontmatter.
Why: under `decisions/2026-10-24-uniform-single-unit-rule-for-all-leads.md` the lead drafts and revises itself, and the owner's writing is mostly high-stakes scientific prose, so drafting and critic-round judgment run on the strongest model. Rejected: an Opus lead with Fable on request (cheaper, but splits drafting between lead and worker depending on phrasing).
Unmeasured cost impact; the audit tool's lead-context metric and roadmap item 8 cover the re-check.

superseded by: .supervisor/memory/decisions/2026-10-24-the-writer-lead-runs-on-fable-like-the-p.md
