---
summary: Support scientific workflows with stamped artefacts directories
status: blocked
owner: 
since: 
plan: 
depends: []
decisions: []
---
Goal: Support scientific workflows, the third use the supervisor targets beside coding and writing.
Scope: Artefacts live under artefacts/ in date- or time-stamped subdirectories, each with a README (goal, what was learned) beside the figures and data. Likely needs a new skill.
Done when: A scientific run leaves a stamped artefacts/ subdirectory whose README states the goal and what was learned, outputs beside it; the suite passes.
Notes: Blocked: deferred by the owner to a future release. Left to the planner: is artefacts/ at the repo root an accepted exception to .supervisor/ as the one root; stamp format; which agent writes artefacts and README; what feeds long-term memory and who distills it; large data files. Pointer: .supervisor/archive/working/research/research-memory.md section 8 item 7.
