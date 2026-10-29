---
domain: code
summary: An installed instance must not depend on the source checkout; a run-time need for it is a defect
affects: [deploy, docs/deploy.md]
verified: 2026-10-29
source: .supervisor/archive/working/plans/plan-install-lifecycle.md; user 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-deploy-install-model-rationale.md
---
Any run-time need of the checkout is a defect unless the user names one (`update --from`); reading the recorded checkout is allowed only as an extra whose absence changes no result.
Why: the user wanted installs stand-alone "like any other program"; a checkout may move, change or be deleted.
