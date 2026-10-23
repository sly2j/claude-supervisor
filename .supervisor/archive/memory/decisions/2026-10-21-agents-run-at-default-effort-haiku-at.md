---
domain: pack
summary: Opus, Fable and Sonnet agents run at default effort (no effort line); only Haiku agents set effort xhigh
affects: [pack/agents, pack/skills/agent-authoring/SKILL.md, docs/architecture.md]
verified: 2026-10-21
source: user 2026-10-21
supersedes:
superseded by: pack/skills/agent-authoring/SKILL.md
---
The owner said: "use models (Opus/Fable/Sonnet) everywhere at default level, only make Haiku run
at xhigh". Since 2.11 no Opus, Fable or Sonnet agent sets `effort:` in its frontmatter, so it runs
at the default effort; `clerk`, `git-ops` and `scout` keep `effort: xhigh`. This replaces the
earlier per-agent high/xhigh levels, including planner at xhigh, and settles the question of
whether the critic needs an explicit effort (it does not).

Reach: product; written into the agent frontmatter and the Tiers table in the agent-authoring skill.
