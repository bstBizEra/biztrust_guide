---
id: today
title: Today
order: 20
kind: execution
status: WAIT_FOR_AUTHORITY
owner: repository-administrator
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/29
summary: The time-bounded agenda and single primary action; it expires visibly at the next business day.
primary: true
primary_action: NS-001 — Enable GitHub Pages using GitHub Actions and retain the successful deployment evidence.
snapshot_at: 2026-09-03T19:00:00+07:00
refresh_by: 2026-09-04T00:00:00+07:00
---

## Primary outcome

Enable GitHub Pages from `Settings → Pages → GitHub Actions`, then retain the
successful push-triggered run and published URL. This action requires repository
administrator authority and cannot be completed by an engineering agent.

## Today queue

- [ ] **NS-001:** Repository administrator enables GitHub Pages.
- [ ] **NS-029:** Human reviewers assess the open pull requests against their final head SHAs.
- [ ] **NS-024:** Business, insurance, legal, finance and architecture reviewers begin the S01 authority profile.
- [x] **WP-018:** Markdown source contract and deterministic HTML approach defined.
- [x] **WP-018:** Shared files owned by other pull requests excluded from scope.

## End-of-day refresh rule

Before carrying this page into another day, verify open pull requests, merged
work, the active Work Package, primary action and all dated evidence. If that
verification does not happen, the HTML must display the snapshot as stale.
