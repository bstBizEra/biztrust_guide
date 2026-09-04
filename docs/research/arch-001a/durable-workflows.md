# Durable workflow runtime options for insurance operations

| Field | Value |
|---|---|
| Ticket | [#98 — [ARCH-001A] Research: durable workflow runtime options for insurance operations](https://github.com/bstBizEra/biztrust_guide/issues/98) |
| Feeds | ADR-010 (`DRAFT_REQUIRED` in `docs/architecture/ADR_REGISTER.md`) |
| Framing document | `docs/architecture/FLOWS.md` sections 9, 12, 13 (plus 4, 7, 10, 15, 16 where they name the same operations) |
| Sources | Primary only: Temporal docs and licence, DBOS docs and licence, PostgreSQL docs and licence. Every URL checked 2026-09-05. |
| Status | Research note. It decides nothing; ADR-010 does. |

## Ticket

Issue #98 asks, for ADR-010, which long-running operations need durable workflows and which runtime shape suits them. It names three shapes to compare from official documentation only: Temporal (self-hosted and cloud), a PostgreSQL-backed durable-execution library (DBOS as the example), and a transactional outbox plus job queue built on PostgreSQL. For each: replay and versioning of in-flight workflows, idempotency guarantees, operational footprint, licensing, and the exit path.

## Question

Which runtime shape can carry BizTrust's four long-running operations — placement, binding with insurer confirmation, payment-to-policy, and renewal — while honouring the FLOWS.md rules that the workflow coordinates modules but cannot mutate their tables, that duplicate callbacks must be idempotent, that conflicting insurer messages go to review rather than last-write-wins, and that a workflow code upgrade must not break in-flight cases?

## The four operations and what each needs (from FLOWS.md)

FLOWS.md is a draft contract (`0.1-draft`, `DRAFT FOR CONTRACT FREEZE`). The needs below are read off its state machines and rules, not invented here.

### Placement (section 7)

- Multi-step, human-paced: `DRAFT → MARKET_OPEN → AWAITING_QUOTES → QUOTES_RECEIVED → MARKET_CLOSED → RECOMMENDATION_READY`, with a loop `QUOTES_RECEIVED → AWAITING_QUOTES` to seek more quotes.
- "A placement can involve multiple market requests. Insurer-specific states belong to each market request; the placement summarizes the broker process." So the workflow fans out to N market requests and aggregates.
- `AWAITING_QUOTES → EXPIRED` is a time-based exit: the runtime needs a durable timer that outlives any process.
- Transitions are driven by external facts (a quote arrives) over days or weeks, so the runtime needs a durable "wait for external input" primitive.

### Binding with insurer confirmation (section 9)

- `SENT_TO_AUTHORITY → PENDING_CONFIRMATION → CONFIRMED` waits on an authority holder; `PENDING_CONFIRMATION → EXPIRED` when "confirmation window ends"; `PENDING_CONFIRMATION → FAILED_REVIEW` when "evidence inconsistent".
- Safety rules that bind the runtime choice:
  - "Duplicate confirmation callbacks must be idempotent."
  - "Conflicting confirmations enter manual review; the latest message does not silently win."
  - `CONFIRMED` requires evidence, source identity, effective period and recorded time — the workflow must retain or reference evidence, not just flip a state.
- Needs: durable wait for a callback, a confirmation-window timer, deduplication of the callback by identity, and an escalation path that parks the case for a human rather than resolving it automatically.

### Payment-to-policy (sections 12 and 13)

- Section 13 shows the Payment module verifying signature and deduplicating the provider event before emitting `PaymentConfirmed`; the binding workflow then queries binding state, and either waits/retries/escalates or drives policy registration and an approved journal posting.
- "The workflow coordinates modules but cannot mutate their tables. If payment succeeds and binding fails, an approved compensation policy determines hold, void or refund; the workflow does not invent a financial outcome."
- Section 12 keeps provider state, operational state, allocation state and ledger state "separately attributable"; section 12A adds client-money dimensions.
- Section 16 fixes the failure responses: provider timeout → "Retry with bounded policy; preserve pending state"; duplicate callback → "Return prior idempotent result"; ledger imbalance → "Reject the posting atomically".
- Needs: bounded retries against modules that expose idempotent commands (ADR-012 owns the key scope), compensation as an explicit step, and no cross-module transaction — each module commits its own state.

### Renewal (sections 4 and 10; ADR-020)

- Section 4 gives the Renewal module `StartRenewal`, `CompleteRenewal`, `GetRenewal`, `RenewalStarted`, `RenewalCompleted`. Section 10 tracks `RENEWAL_PENDING` as a servicing dimension owned by the "Policy workflow".
- Renewal starts on a calendar (ahead of `effective_to`) and then runs a placement-like cycle, so it is both scheduled and long-lived — the case most likely to straddle a code deployment.
- Section 16 names the constraint directly: "Workflow code upgrade | Version workflow behavior and test replay | Break in-flight cases". ADR-020 owns the historical-transaction modelling; ADR-015 owns the temporal fields.
- Needs: a scheduler with catch-up semantics after downtime, and an explicit versioning story for in-flight cases.

### Common to all four

FLOWS.md section 15 already proposes an outbox/inbox for events and says: "The outbox/inbox pattern is a `PROPOSED_DECISION`, not a guarantee of exactly-once execution. Business idempotency and reconciliation remain mandatory." Whatever runtime is chosen, module-level idempotency (ADR-012) and reconciliation stay in place; the runtime only reduces how often they are exercised.

## Comparison table

Source keys refer to the Sources section. "Home-built" means the official sources describe the building block, not the behaviour; the behaviour would be BizTrust's own code and its own tests.

| Shape | Replay and versioning of in-flight workflows | Idempotency guarantees | Operational footprint | Licensing | Exit path |
|---|---|---|---|---|---|
| **Temporal, self-hosted** | State is "an append-only log of Events" that is "durably persisted by the Temporal service"; recovery is by replay, so "Workflow code must be deterministic to support replay" [T1][T2]. Changing code without a patch makes the run "fail with a nondeterminism error" [T3]. Two versioning tools: the Patching API ("A Patch defines a logical branch in a Workflow for a specific change, similar to a feature flag") with a three-step removal process [T3], and Worker Versioning, where "A Pinned Workflow is guaranteed to complete on a single Worker Deployment Version" and old versions drain [T4][T5]. History is capped at "51,200 Events or 50 MB"; Continue-As-New resets it [T6][T7]. | "Temporal guarantees that there can be at most one Workflow Execution with a given ID running at any point in time"; Reuse Policy and Conflict Policy govern re-starts, default conflict is `Fail` [T8]. Activities are at-least-once: "Because Activities may be retried, these functions may be executed more than once", "You should always make your business logic Activities idempotent" [T9]. Signal-With-Start signals a running execution or starts one [T10]. Timers "are persisted" and resolve after Worker or Service downtime [T11]. | Four server services (Frontend, History, Matching, Worker); "For live (production) environments, we recommend that each service runs independently" [T12]. Persistence: Cassandra, MySQL, PostgreSQL (13.18–16.6 tested); SQLite is "not production usage" [T13]. Visibility: "we recommend using Elasticsearch" for production; advanced visibility also on PostgreSQL 12+ [T13]. Shard count is fixed "at build time and can't adjust it later"; "Server upgrades can negatively affect self-hosted Temporal Service availability"; "You must create and maintain the infrastructure" [T14]. Workers in the application stack; SDKs for .NET, Go, Java, PHP, Python, Ruby, Rust, TypeScript [T15]. | Server: MIT (Temporal Technologies 2025; Uber 2020) [T16]. SDKs checked (PHP, TypeScript): MIT [T17]. | Workflow definitions are SDK code; the event history is Temporal's own format. Exit means re-implementing the coordination logic and draining or migrating in-flight cases. Continue-As-New chains and Workflow Ids are the only portable anchors [T7][T8]. Module state stays in BizTrust's own tables by FLOWS.md rule, which limits the blast radius. |
| **Temporal Cloud** | Same programming model and versioning tools as self-hosted [T1]–[T7]. | Same as self-hosted [T8]–[T11]. | "a fully managed durable execution platform" handling "persistence, replication, upgrades, and availability"; "You run Workers ... deployed anywhere"; "Your code runs in your environment. Temporal Cloud never sees your application logic or sensitive data" [T18]. Priced per Action: "Actions pricing starts at $50 per million Actions ($0.00005 per Action)"; storage at $0.042/GBh active and $0.00105/GBh retained; Essentials "Greater of $100/mo or 5% of Usage Spend", Business "Greater of $500/mo or 10% of Usage Spend"; Enterprise/Mission Critical on annual contract [T19]. | Cloud is a commercial service under Temporal's terms; the SDKs the Workers use remain MIT [T17]. Contract terms not read for this note (see Unverified). | Same code exit as self-hosted, plus a service exit: the server is MIT, so moving from Cloud to self-hosted is a migration of namespaces and history, not a rewrite [T16]. Data-residency and export terms not read (see Unverified). |
| **DBOS (PostgreSQL-backed durable-execution library)** | "There's no separate orchestration server and no infrastructure required besides Postgres"; "DBOS checkpoints those workflows and steps to a Postgres database" and recovers "from their last completed step" [D1]. Workflows "must be deterministic" [D2]. Versioning: "application version is automatically computed from a hash of workflow source code"; "it only recovers workflows whose version matches the current application version"; `DBOS.patch()` for compatible changes; blue-green drain for breaking ones ("retain some processes running your old code version") [D3]. Fork from a step is a management operation [D4]. | "An assigned workflow ID acts as an idempotency key: if a workflow is called multiple times with the same ID, it executes only once" [D2]. Steps "are tried at least once but are never re-executed after they complete" [D2]. Messaging: "If you're sending a message from a workflow, DBOS guarantees exactly-once delivery"; from outside, use a workflow ID as idempotency key [D5]. Queues: "only one workflow with a specific deduplication ID can be enqueued" [D6]. Scheduled workflows: "executed by exactly one worker process" via a constructed idempotency key, with `backfill` for missed runs [D7]. Sleep is durable [D2]. | Library inside the app; a `system database` in Postgres with `workflow_status`, `operation_outputs`, `notifications`, `workflow_events` tables [D8]. "compatible with any Postgres database"; "Do not use a connection pooler in transaction mode" because it uses LISTEN/NOTIFY; "1000 actions ... per second ... requires 4 Postgres vCPUs" [D9]. Recovery: single process restarts recover "all PENDING workflows"; multi-process needs executor IDs and "only recovers pending workflows assigned to that executor ID"; automatic reassignment after a crash is documented only with Conductor: "When Conductor detects that an executor is unhealthy, it automatically signals another executor to recover its workflows" [D10][D11]. Conductor is "entirely out-of-band"; if disconnected "your applications will continue operating normally" [D9][D11]. SDKs: Python, TypeScript, Go, Java [D12]; no PHP SDK found in the `dbos-inc` org [D13]. Console/Conductor plans: Pro $99/mo, Teams $499/mo, Enterprise with "Option to self-host DBOS Conductor" [D14]. | Libraries checked (Python, TypeScript, Go): MIT [D15]. Conductor and Console are commercial (plans above) [D14]. | All checkpoint state is in documented Postgres tables in BizTrust's own database [D8]. Exit is a rewrite of the annotated workflow functions plus a drain of `PENDING` rows; no external history format to migrate. Losing Conductor loses cross-executor crash recovery and the console, not execution [D9][D11]. |
| **Transactional outbox + job queue on PostgreSQL** | No replay: the "workflow" is a state row per case plus a job table; recovery is a job being re-claimed. Versioning of in-flight cases is home-built: the state schema and the handler code must be migrated together, and FLOWS.md section 16 ("Version workflow behavior and test replay") becomes a BizTrust test obligation with no runtime help. | Building blocks are documented, guarantees are home-built. Consumer claim: `SKIP LOCKED` "can be used to avoid lock contention with multiple consumers accessing a queue-like table" but "provides an inconsistent view of the data" [P1]; row locks "block only writers and lockers to the same row" [P2]. Dedup: the inbox table FLOWS.md section 15 already proposes, keyed on event identity (BizTrust code). Wake-up: `NOTIFY` events "are not delivered until and unless the transaction is committed"; payload "shorter than 8000 bytes"; identical payloads in one transaction coalesce; only "the sessions currently listening" are notified, so a poller is still required [P3][P4]. Change capture: a logical slot "will emit each change just once in normal operation", persists across crashes, and retains WAL while unconsumed [P5]. Timers, retries with backoff, and scheduling are all BizTrust code. | PostgreSQL only — the database BizTrust already assumes (ADR-004). Extra operational items: a poller/worker process, slot monitoring if logical decoding is used ("neither required WAL nor required rows from the system catalogs can be removed by VACUUM as long as they are required by a replication slot") [P5], notification-queue monitoring ("8GB in a standard installation ... no cleanup can take place if a session executes LISTEN and then enters a transaction for a very long time") [P3], and home-built visibility (there is no console). | PostgreSQL License, "a liberal Open Source license, similar to the BSD or MIT licenses" [P6]. | None needed: this shape is the substrate the other two would sit beside. The cost is the reverse — everything the other shapes provide (replay, patching, timers, console, drain) is BizTrust code to maintain, and the outbox/inbox is still required under either runtime per FLOWS.md section 15. |

## Findings per option

### Temporal (self-hosted)

Temporal's model matches the four operations' shape directly. A placement or binding is a Workflow Execution that awaits Signals ("You can send Signals from any Temporal Client, the Temporal CLI, or you can Signal one Workflow to another") and persisted Timers, so the `AWAITING_QUOTES → EXPIRED` and `PENDING_CONFIRMATION → EXPIRED` transitions are a Timer racing a Signal [T10][T11]. Signal-With-Start handles the "callback arrives before the case exists" race [T10]. Renewal maps onto Schedules, which have a Catchup Window and Backfill for downtime [T20].

The cost is determinism. The service recovers a Workflow by replaying its Event History against the code, so "Workflow code must be deterministic to support replay", and a code change that alters the command sequence makes the run "fail with a nondeterminism error" [T2][T3]. Temporal gives two answers: the Patching API, where a marker is recorded in history and old branches are removed in three steps after "all the Workflow Executions prior to version 1 have left retention" [T3]; and Worker Versioning, where a Pinned Workflow "is guaranteed to complete on a single Worker Deployment Version" while other versions "continue polling to allow pinned Workflows to finish executing or in case you need to roll back" [T4][T5]. The docs say Worker Versioning "should be the default recommendation for deploying Workflow code changes in production" [T5]; its GA status was not found on the pages read (see Unverified). Either way, FLOWS.md section 16's "test replay" obligation becomes a concrete test: the SDK replays recorded histories against new code.

On idempotency, Temporal gives at most one open execution per Workflow Id [T8], which is a natural fit for "one binding workflow per bind order". It does not make Activities exactly-once: "Because Activities may be retried, these functions may be executed more than once", so every module command the workflow calls must be idempotent by ADR-012 — exactly what FLOWS.md already requires [T9]. The 51,200-event / 50 MB history cap is unlikely to bite a placement but is a real limit for anything that loops for months; Continue-As-New is the documented reset [T6][T7].

The footprint is the largest of the three shapes: four server services that Temporal recommends running independently in production, a persistence store (PostgreSQL is a tested option), a Visibility store (Elasticsearch recommended for production, PostgreSQL 12+ acceptable for advanced visibility), and a shard count fixed at build time [T12][T13][T14]. Temporal's own checklist says self-hosting "can be expensive" and recommends "trained, experienced administrators" [T14]. The server and the SDKs checked are MIT [T16][T17]. PHP is a first-class SDK [T15].

### Temporal Cloud

The same programming model with the service run by Temporal: "It handles the complexity of running Temporal at scale—persistence, replication, upgrades, and availability", while "You run Workers that execute your Workflow and Activity code" and "Temporal Cloud never sees your application logic or sensitive data" [T18]. That last sentence covers code, not payloads: Workflow inputs, Signal payloads and Activity results are part of the Event History the service persists, so what is placed in them is a data-classification decision under ADR-019.

Pricing is consumption-based: $50 per million Actions to start, storage per GB-hour, and a plan floor of $100/month (Essentials) or $500/month (Business), with Enterprise and Mission Critical on annual contract [T19]. Because the server is MIT, the exit from Cloud to self-hosted is a migration rather than a rewrite [T16]. Contract, residency and export terms were not read for this note.

### DBOS

DBOS is a library, not a server: "There's no separate orchestration server and no infrastructure required besides Postgres" [D1]. It checkpoints each workflow and step into a system database in Postgres and recovers "from their last completed step" [D1][D8]. The primitives the four operations need are present: durable sleep, `send`/`recv` messaging with per-topic queues and timeouts, `set_event`/`get_event` for exposing state, queues with deduplication IDs, and scheduled workflows with backfill [D2][D5][D6][D7].

Its idempotency story is stronger at the workflow boundary than Temporal's default: "An assigned workflow ID acts as an idempotency key: if a workflow is called multiple times with the same ID, it executes only once" [D2]; messages sent from inside a workflow are exactly-once [D5]. Steps are the same as Temporal Activities — at least once, never re-run after completion — so module commands must still be idempotent [D2].

Versioning is by source hash: "it only recovers workflows whose version matches the current application version", with `DBOS.patch()` for compatible changes and a blue-green drain for breaking ones [D3]. That is simpler to reason about than event-history replay but has an operational consequence: after a breaking deploy, old-version processes must keep running until their `PENDING` workflows finish, or those workflows are forked or resumed by hand [D3][D4]. The `workflow_status` table records the `application_version` and `executor_id` per workflow, so drain progress is a SQL query [D8].

The main gap for BizTrust is crash recovery across processes. A single process recovers all `PENDING` workflows on restart; in a multi-process deployment each executor "only recovers pending workflows assigned to that executor ID" [D10]. Automatic reassignment when an executor dies is documented only with Conductor: "When Conductor detects that an executor is unhealthy, it automatically signals another executor to recover its workflows" [D11]. Conductor is out-of-band (its unavailability "does not affect the availability of your applications") [D9], but it is a commercial control plane: registration and an API key, plans from $99/month, with self-hosted Conductor an Enterprise option [D11][D14]. Whether a self-hosted deployment can reassign a dead executor's workflows without Conductor (for example, by fixing executor IDs to stable pod names) is not stated on the pages read and is a spike question.

Two further constraints: DBOS uses LISTEN/NOTIFY, so "Do not use a connection pooler in transaction mode" [D9]; and the SDKs are Python, TypeScript, Go and Java, with no PHP SDK in the `dbos-inc` organisation [D12][D13]. If ADR-001's modular monolith is PHP, DBOS would have to run as a separate service in one of those languages, which erodes its "no extra infrastructure" advantage. The libraries are MIT [D15].

### Transactional outbox + job queue on PostgreSQL

This is not a runtime; it is the set of primitives FLOWS.md section 15 already proposes for events, extended with a job table. PostgreSQL documents the pieces well. `SELECT ... FOR UPDATE SKIP LOCKED` is the documented multi-consumer claim: the docs say it "can be used to avoid lock contention with multiple consumers accessing a queue-like table" while warning that it "provides an inconsistent view of the data, so this is not suitable for general purpose work" [P1]. `NOTIFY` is transactional ("not delivered until and unless the transaction is committed") and coalesces identical payloads in one transaction, but it only reaches "the sessions currently listening" and has an 8000-byte payload limit, so it is a wake-up hint over a poller, not a queue [P3][P4]. The notification queue is 8 GB and cannot be cleaned while a listening session sits in a long transaction [P3]. Logical decoding gives a change stream where a slot "will emit each change just once in normal operation", but a slot "will prevent removal of required resources even when there is no connection using them", so an abandoned consumer fills the disk [P5].

What PostgreSQL does not document, because it does not provide it: durable timers, retry policies, per-case state with a "wait for signal" primitive, replay testing, or a console. For the four operations that means BizTrust writes and tests the `EXPIRED` timers, the confirmation-window race, the bounded-retry loop in section 13, the renewal scheduler with catch-up, and the "version workflow behavior and test replay" obligation in section 16 — with no runtime to lean on. The idempotency of module commands is unchanged (it is ADR-012's job under every shape), but the "at most one workflow per case" guarantee the other shapes give for free becomes a unique index and a claim protocol that the team owns.

The advantages are equally concrete: nothing new to operate beyond the database ADR-004 already assumes, no data leaves BizTrust's tables, the licence is the PostgreSQL License [P6], and there is no exit because there is nothing to exit. And this shape is not an alternative to the other two so much as their floor: the outbox/inbox stays under Temporal or DBOS, because FLOWS.md section 15 makes business idempotency and reconciliation mandatory regardless.

## Decision-relevant facts for ADR-010

1. **All three shapes leave module-command idempotency to BizTrust.** Temporal Activities "may be executed more than once" [T9]; DBOS steps "are tried at least once" [D2]; the outbox pattern "is not a guarantee of exactly-once execution" (FLOWS.md section 15). ADR-012 is a prerequisite of ADR-010 under every option, not a consequence of it.
2. **Versioning of in-flight cases is a first-class, documented feature in Temporal and DBOS and a home-built obligation in the outbox shape.** Temporal: Patching API plus Worker Versioning with pinned executions [T3][T4][T5]. DBOS: source-hash application version, `patch()`, and blue-green drain [D3]. Outbox: FLOWS.md section 16's "Version workflow behavior and test replay" has no runtime support.
3. **Operational footprint differs by an order of magnitude.** Temporal self-hosted is four services plus persistence plus visibility, with shards fixed at build time and upgrade risk to availability [T12][T13][T14]; Temporal Cloud is a paid service with a $100–$500/month plan floor and $50 per million Actions [T19]; DBOS is a library plus system tables in the existing Postgres [D1][D8]; the outbox shape is the existing Postgres alone.
4. **DBOS's cross-process crash recovery is documented only through Conductor, a commercial control plane.** Self-hosted executors recover only their own executor ID's `PENDING` workflows on restart [D10]; automatic reassignment after an executor dies is described for Conductor [D11]. Whether a self-hosted deployment can reach the same outcome without Conductor is a spike question, not a documented fact.
5. **Language coverage constrains the choice before any other criterion.** Temporal documents SDKs for .NET, Go, Java, PHP, Python, Ruby, Rust and TypeScript [T15]; DBOS documents Python, TypeScript, Go and Java with no PHP SDK found [D12][D13]. ADR-001's stack decision therefore either keeps DBOS in play or removes it. All server and library code checked is MIT; PostgreSQL is under the PostgreSQL License [T16][T17][D15][P6].

## Spike criteria a build-versus-adopt decision would need

ADR-010's register row asks for a "Workflow replay/versioning and operational spike". The following criteria would make that spike decidable. Each is phrased so that the same test can be run against every shape.

1. **Replay after a breaking change.** Start a binding workflow, leave it in `PENDING_CONFIRMATION`, deploy a code change that reorders or adds a step, then deliver the confirmation. Pass: the in-flight case completes on the old logic or the new logic by explicit choice (Temporal patch or pinned version; DBOS patch or drain; outbox migration), with no case failed or duplicated. Record the drain time and the operator steps.
2. **Duplicate and conflicting callbacks.** Deliver the same insurer confirmation twice and then a conflicting one. Pass: one `CONFIRMED` transition, the duplicate returns the prior result (FLOWS.md section 16), and the conflict lands in `FAILED_REVIEW` with both messages retained — under process kill between receipt and commit.
3. **Timer survival.** Set a confirmation window of N minutes, kill every worker process for longer than N, restart. Pass: `PENDING_CONFIRMATION → EXPIRED` fires once, at or after the deadline, with no manual intervention. For the outbox shape, this measures the poller design; for DBOS, it measures self-hosted recovery without Conductor (fact 4).
4. **Executor loss in a multi-process deployment.** Run two workers, kill one mid-workflow with a `PENDING` case assigned to it. Pass: the surviving worker (or a replacement) completes the case within a stated bound, without Conductor or Temporal Cloud if the self-hosted variant is under test.
5. **Payment-to-policy compensation.** Run section 13 with policy registration forced to fail after payment capture. Pass: the workflow invokes the compensation policy as a named step, mutates no module table directly, and the ledger sees either a balanced posting or no posting.
6. **Renewal scheduling with downtime.** Schedule renewals, take the scheduler down across two fire times, restart. Pass: exactly the configured catch-up behaviour (Temporal Catchup Window/Backfill [T20]; DBOS `backfill_schedule`/`automatic_backfill` [D7]; outbox: whatever the team built) and no double-start for the same policy period.
7. **Operational cost sheet.** For each shape: components deployed, upgrade procedure and its documented availability impact, monitoring signals required (Temporal service/persistence metrics [T14]; DBOS system tables and Conductor [D8][D11]; PostgreSQL slot and notification-queue health [P3][P5]), and the monthly price at a stated volume (Temporal Cloud Actions [T19]; DBOS plans [D14]).
8. **Data classification of payloads.** List every field that would enter workflow inputs, signals or step results for the four operations and classify it under ADR-019. Pass: nothing in a class that may not leave BizTrust's database is in a Temporal Cloud history.
9. **Exit rehearsal.** Export or drain all in-flight cases from the candidate and re-create them under the outbox shape. Record the effort; that is the price of being wrong.

## Unverified items

Marked UNVERIFIED because they were not found in a first-party source on 2026-09-05, or were inferred rather than read.

- UNVERIFIED: the general-availability status of Temporal Worker Versioning. The pages read recommend it for production but do not state a status label [T4][T5].
- UNVERIFIED: whether self-hosted DBOS can reassign a dead executor's `PENDING` workflows to another executor without Conductor. The recovery page documents per-executor recovery on restart and automatic reassignment with Conductor only [D10][D11].
- UNVERIFIED: whether DBOS Conductor is hosted by DBOS, Inc. by default. Inferred from the Enterprise plan's "Option to self-host DBOS Conductor" and the Console registration flow [D11][D14]; not stated as a sentence on the pages read.
- UNVERIFIED: the minimum PostgreSQL version DBOS supports. The checklist says "any Postgres database" without a version [D9].
- UNVERIFIED: Temporal Cloud contract terms, data residency, retention and export mechanics, and whether the Actions price list read applies to the current pay-as-you-go model without a contract.
- UNVERIFIED: Temporal's `MaxCallbacksPerWorkflow` and payload-size limits — the limits page read gives the history cap and the 2,000-per-type incomplete-operation default but not those values [T6].
- UNVERIFIED: BizTrust's application language. `BIZTRUST-ARCH-001.md` does not name one; fact 5 above is conditional on ADR-001.
- Not a source claim, but a scoping note: the ticket's "PostgreSQL-backed durable-execution library" was read as DBOS only, per the ticket's own example. Other libraries in that shape were not surveyed.

## Sources

All URLs checked 2026-09-05. Quotations in this note are taken from these pages as read on that date.

### Temporal

- [T1] Workflow Definition — https://docs.temporal.io/workflow-definition
- [T2] Event History — https://docs.temporal.io/workflow-execution/event
- [T3] Versioning (Go SDK developer guide; Patching API and deprecation steps) — https://docs.temporal.io/develop/go/versioning
- [T4] Worker Versioning (concepts; pinned and auto-upgrade behavior, draining) — https://docs.temporal.io/worker-versioning
- [T5] Worker Versioning (production deployment) — https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning
- [T6] Workflow Execution limits — https://docs.temporal.io/workflow-execution/limits
- [T7] Continue-As-New — https://docs.temporal.io/workflow-execution/continue-as-new
- [T8] Workflow Id and Run Id (uniqueness, Reuse Policy, Conflict Policy) — https://docs.temporal.io/workflow-execution/workflowid-runid
- [T9] Activity Definition (idempotency, retries, heartbeats) — https://docs.temporal.io/activity-definition
- [T10] Sending messages (Signals, Updates, Queries, Signal-With-Start) — https://docs.temporal.io/sending-messages
- [T11] Timers and delays — https://docs.temporal.io/workflow-execution/timers-delays
- [T12] Temporal Server services — https://docs.temporal.io/temporal-service/temporal-server (and https://docs.temporal.io/temporal-service)
- [T13] Persistence (supported databases, Visibility) — https://docs.temporal.io/temporal-service/persistence
- [T14] Self-hosted production checklist — https://docs.temporal.io/self-hosted-guide/production-checklist (index: https://docs.temporal.io/self-hosted-guide)
- [T15] SDK developer guides index — https://docs.temporal.io/develop
- [T16] Temporal server licence (MIT) — https://github.com/temporalio/temporal/blob/main/LICENSE
- [T17] SDK licences (MIT): PHP — https://github.com/temporalio/sdk-php/blob/master/LICENSE.md ; TypeScript — https://github.com/temporalio/sdk-typescript/blob/main/LICENSE (SPDX identifiers confirmed via the GitHub repository licence API)
- [T18] Temporal Cloud overview — https://docs.temporal.io/cloud/overview
- [T19] Temporal Cloud pricing — https://docs.temporal.io/cloud/pricing
- [T20] Schedules — https://docs.temporal.io/schedule

### DBOS

- [D1] Architecture — https://docs.dbos.dev/architecture
- [D2] Workflows tutorial (Python; determinism, workflow IDs, durable sleep, step guarantees) — https://docs.dbos.dev/python/tutorials/workflow-tutorial
- [D3] Upgrading workflow code (application version, patch, blue-green) — https://docs.dbos.dev/python/tutorials/upgrading-workflows
- [D4] Workflow management (cancel, resume, fork) — https://docs.dbos.dev/production/workflow-management
- [D5] Workflow communication (send/recv, events) — https://docs.dbos.dev/python/tutorials/workflow-communication
- [D6] Queues (concurrency, rate limits, deduplication) — https://docs.dbos.dev/python/tutorials/queue-tutorial
- [D7] Scheduled workflows — https://docs.dbos.dev/python/tutorials/scheduled-workflows
- [D8] System tables — https://docs.dbos.dev/explanations/system-tables
- [D9] Production checklist (Postgres compatibility, pooler note, scalability, Conductor out-of-band) — https://docs.dbos.dev/production/checklist
- [D10] Workflow recovery (executor IDs) — https://docs.dbos.dev/production/workflow-recovery
- [D11] Conductor — https://docs.dbos.dev/production/conductor
- [D12] Documentation home (language list) — https://docs.dbos.dev/
- [D13] GitHub organisation search for a PHP repository under `dbos-inc` returned zero results (GitHub search API, 2026-09-05)
- [D14] Pricing — https://www.dbos.dev/pricing
- [D15] Library licences (MIT): Python — https://github.com/dbos-inc/dbos-transact-py/blob/main/LICENSE ; TypeScript — https://github.com/dbos-inc/dbos-transact-ts/blob/main/LICENSE ; Go — https://github.com/dbos-inc/dbos-transact-golang/blob/main/LICENSE (SPDX identifiers confirmed via the GitHub repository licence API)

### PostgreSQL

- [P1] SELECT, "The Locking Clause" (FOR UPDATE, NOWAIT, SKIP LOCKED) — https://www.postgresql.org/docs/current/sql-select.html
- [P2] Explicit locking, row-level locks — https://www.postgresql.org/docs/current/explicit-locking.html
- [P3] NOTIFY — https://www.postgresql.org/docs/current/sql-notify.html
- [P4] LISTEN — https://www.postgresql.org/docs/current/sql-listen.html
- [P5] Logical decoding concepts (replication slots, output plugins, exported snapshots) — https://www.postgresql.org/docs/current/logicaldecoding-explanation.html
- [P6] PostgreSQL License — https://www.postgresql.org/about/licence/

### Repository

- `docs/architecture/FLOWS.md` sections 4, 7, 9, 10, 12, 12A, 13, 15, 16 (read at `origin/main`, commit `e1b20d1`)
- `docs/architecture/ADR_REGISTER.md` row ADR-010
- `docs/architecture/BIZTRUST-ARCH-001.md` (workflow runtime marked `IMPLEMENTATION_CANDIDATE`; INV-013, INV-020)
