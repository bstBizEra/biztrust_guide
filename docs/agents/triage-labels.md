# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Edit the right-hand column to match whatever vocabulary you actually use.

## Repo notes

- All five labels exist in the GitHub repo as of 2026-09-05: `wontfix` was a default, and the other four were created once under WP-045 with `gh label create`, because `/triage` does not create labels itself (mattpocock/skills issue 616).
- `ready-for-agent` is a triage verdict, not authority. Under `AGENTS.md`, an agent may start only when the issue is a Work Package with a human authority record; the `work-package` label marks that, and triage labels never substitute for it.
- The repo's other labels are not triage roles: the nine GitHub defaults, `work-package`, `state:in-progress` and the five `wayfinder:*` labels. Leave them alone.
