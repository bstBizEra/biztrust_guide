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

- As of 2026-09-05 only `wontfix` exists in the GitHub repo. `/triage` creates the other four on first use.
- `ready-for-agent` is a triage verdict, not authority. Under `AGENTS.md`, an agent may start only when the issue is a Work Package with a human authority record; the `work-package` label marks that, and triage labels never substitute for it.
- Existing repo labels `work-package` and `state:in-progress` are not triage roles. Leave them alone.
