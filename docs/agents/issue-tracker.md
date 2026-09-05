# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues in `bstBizEra/biztrust_guide`. Use the `gh` CLI for all operations.

## Repo-specific conventions

These come from `AGENTS.md` and take precedence over the generic conventions below.

- **No ticket, no work.** Every material change references exactly one Work Package ID. Since WP-031 (issue #68) the practice is: the issue is titled `[BIZTRUST-GUIDE] <finding>` with acceptance criteria; the Work Package number is assigned by the branch name, the commit subject and `badf/current-state.json`, not by retitling the issue. The authority record lives in `badf/current-state.json` under `authority` and in the decision log, not on the issue.
- **Label `work-package`** was applied to WP-003 to WP-030 only (fourteen issues, none created through the issue form). Its absence on a later issue does not mean absence of authority, and its presence never substitutes for the state file's authority record.
- **One Work Package per branch, one PR per branch.** The PR body links the Work Package issue. `main` is not branch-protected; the pull-request gate is convention, so never push to `main` directly.
- **PR title and commit subject**: `[BIZTRUST-GUIDE-WP-NNN] <description> (#<issue>)`; the squash merge appends `(#<PR>)`, so `main` reads `(#89) (#90)`.
- Never put secrets, tokens, client information or regulated data in an issue: this repository is public.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v`; `gh` does this automatically when run inside a clone.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue titled `[BIZTRUST-GUIDE] <finding>` with acceptance criteria. It is worked as a Work Package when a branch, a commit subject and `badf/current-state.json` name its WP number and the state file records the authority.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (a file on a `research/<slug>` branch, or the ticket's resolution comment, plus its link) to the map's Decisions-so-far.
