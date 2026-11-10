---
summary: Verify the ALCF preset on first live use
status: blocked
owner: 
since: 
plan: 
depends: []
decisions: []
---
Goal: Confirm the ALCF preset works against live ALCF.
Scope: Check that alcf-tokens get-token inference prints only the bare token and that <base URL>/v1/models exists; if either differs, fix deploy's ALCF preset.
Done when: Both checks hold, or deploy's ALCF preset is fixed.
Notes: Blocked: needs live ALCF access. Until then the code fails loudly or falls back to typed model ids. Source: .supervisor/archive/working/plans/api-access-install.md.
