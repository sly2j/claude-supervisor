---
domain: code
summary: The pack is a stand-alone tool; entries here govern repo work only, so decide each rule's reach and write product behaviour into pack/ itself
affects: [pack/]
verified: 2026-10-22
source: user 2026-10-21
supersedes: .supervisor/archive/memory/conventions/2026-10-22-the-pack-is-standalone-behaviour-lives-in.md
---
User, verbatim: "That's always the case for this repo - it's a standalone tool that needs to function outside of its source dir, so external behavior has to be made explicit in the product (agents/skills/etc) itself".

User, verbatim, follow-up: "yes, decisions and rules stored here are specifically for work on this repo, but because of the nature of this repo things can be ambiguous and we need to check the desired reach for behavior."

Standing rule for this repo: the pack is deployed and run in other projects, where this repo's `.supervisor/memory/`, `docs/` and plans do not exist. Any behaviour a deployed agent or skill must show outside this repo has to be stated in the pack files themselves (`pack/agents/*.md`, `pack/skills/**`, templates, references). A decision entry, plan or roadmap line here is not enough on its own: write the rule into the pack file it governs. Record a memory entry here only for what that text does not carry: rationale, rejected alternatives, user preferences and facts not visible in the work. When nothing extra remains, record nothing. The same holds for rules written into `CLAUDE.md` or `docs/`. Example that prompted it: the curator's migrate exemption from the five-entry cap must be written into `pack/agents/curator.md` (it now says `migrate` has no cap), not live only in a decision entry.

Reach check: entries under this repo's `.supervisor/` govern work on this repo only. When a decision or rule is made here, determine its reach: (a) repo-work only (stays in `.supervisor/` or `CLAUDE.md`), or (b) product behaviour (must be written into the pack itself). When the reach is ambiguous, ask the user rather than guess.

Related, same principle at deploy run time: `.supervisor/memory/decisions/2026-10-22-deploy-install-model-rationale.md` (installs must not depend on the source checkout). Kept separate: that entry is about the `deploy` tool's installed instances, this one about where pack behaviour is specified.
