# Bitemporal modelling patterns on PostgreSQL

| Field | Value |
|---|---|
| Ticket | [#99 — Research: bitemporal modelling patterns on PostgreSQL](https://github.com/bstBizEra/biztrust_guide/issues/99) (parent #91, blocks #112) |
| Consumer | `ADR-015` — Effective Time, Record Time, Correction and Supersession (`docs/architecture/ADR_REGISTER.md`, `FLOWS.md` §10A) |
| Sources checked | 2026-09-05 |
| Status | Research only. No schema decision is made here; implementation authority is not granted. |

## Ticket

Issue [#99](https://github.com/bstBizEra/biztrust_guide/issues/99): ADR-015 must represent valid time, record time, correction, supersession and effective timezone for every dated insurance entity, because cover incepts on a stated date that is frequently not the record-creation moment (#15 finding 3).

## Question

From primary sources (SQL:2011 temporal features as implemented by vendors, PostgreSQL range types and exclusion constraints, Snodgrass and Fowler as pattern sources): what are the candidate representations; how does each answer "what did the record say last Tuesday"; how is a correction told from a supersession; what does the timezone question for effective dates look like; and what does it cost to retrofit each onto a table that started with one timestamp.

### Vocabulary used here

This file uses the repo's terms from `FLOWS.md` §10A, mapped to the literature's terms:

| Repo term (`FLOWS.md` §10A) | Snodgrass / Consensus Glossary | Fowler | SQL:2011 vendor term |
|---|---|---|---|
| effective time (`effective_from`, `effective_to`, `effective_timezone`) | valid time | actual time | application-time period / `BUSINESS_TIME` |
| record time (`recorded_at`) | transaction time | record time | system-time period / `SYSTEM_TIME` |
| correction / supersession (`supersedes_id`) | (no glossary term; both are transaction-time appends) | "retroactive change" vs "additive change" | UPDATE / `UPDATE ... FOR PORTION OF` |

Definitions, quoted from the Consensus Glossary (Snodgrass is a co-author; see Sources, S1):

- Valid time: "The valid time of a fact is the time when the fact is true in the modeled reality. [...] Valid times are usually supplied by the user." (§3.1, p. 370)
- Transaction time: "The transaction time of a database fact is the time when the fact is current in the database and may be retrieved. As a consequence, transaction times are generally not time instants, but have duration. [...] They cannot extend into the future. Also, as it is impossible to change the past, (past) transaction times cannot be changed. Transaction times may be implemented using transaction commit times, and are system-generated and -supplied." (§3.2, p. 371)
- Bitemporal relation: "a relation with exactly one system supported valid time and exactly one system-supported transaction time. [...] There are no restrictions as to how either of these temporal dimensions may be incorporated into the tuples." (§3.8, p. 373)

Fowler's framing (S2, S3): actual time is "the time something happened", record time is "the time we knew about it"; "Not just would a retroactive change to record-temporal information break the integrity of the record, there's no situation that requires a retroactive change"; "An additive change always goes onto the end of the record". He notes the terminology mapping himself: "What I call actual time he calls valid time, what I call record time he calls transaction time" (referring to Snodgrass). In "Bitemporal History" (2021) he states the need arises "when actions are based on a past state that's retroactively changed", and lists alternatives: prevent retroactive changes, record the inputs with the action, or apply the update before dependent actions run.

Two consequences follow for every candidate below and match `FLOWS.md` §10A: record time is append-only (a correction "creates a new assertion; it does not rewrite the original receipt or audit history"), and record time is a *period* per row version, not a single instant, if the question "what did the record say at T" is to be answerable by a range predicate.

## Candidate representations

Four storage shapes are distinguishable in the sources. They are not exclusive; C is commonly layered on A or B, and D is a different write model that can project into B.

### Candidate A — Append-only assertion log with `recorded_at` and `supersedes_id`

**Description.** The shape `FLOWS.md` §10A already sketches: every coverage-sensitive fact is an immutable row carrying `effective_from`, `effective_to`, `effective_timezone`, `source_created_at`, `source_received_at`, `recorded_at`, and `supersedes_id`. Nothing is ever updated; a later assertion points at the one it replaces. This is Fowler's Audit Log carried to the row level ("A simple log of changes, intended to be easily written and non-intrusive"; record "the actual and record dates. They are easy to produce and even though they may be the same 99% of the time, the 1% can save your bacon" — S4), with Effectivity on each row ("Add a time period to an object to show when it is effective" — S5).

**"What did the record say last Tuesday?"** Take assertions for the entity with `recorded_at <= T` and keep those that are *not* the target of any `supersedes_id` from an assertion whose `recorded_at <= T` (an anti-join), then filter by `effective_from <= D < effective_to` for the business date D. Record time here is only the *start* instant; the end of a row's record-time period is implicit in its successor. That is why the query needs the anti-join rather than a single range predicate. Fowler's Audit Log page states the trade-off: "Audit Log is easy to write but harder to read, especially as it grows large."

**Correction vs supersession.** Not derivable from timestamps. Both are new rows with a later `recorded_at` and a `supersedes_id`. The distinction must be an explicit column (for example `change_kind IN ('CORRECTION','SUPERSESSION')`) or a rule enforced by a CHECK/trigger: a correction keeps the superseded row's effective bounds (it says "the original statement was wrong"); a supersession changes them (it says "a new fact starts, the old one ends"). Fowler's "Bitemporal History" example makes the same split: HR's salary correction changes actual history retroactively; the March-15 notification is an additive record-time event.

**PostgreSQL mechanisms.** Plain columns; `timestamp with time zone` for `recorded_at`; `date` (or `timestamp`) plus a text `effective_timezone` for effective bounds; an ordinary B-tree on `(entity_id, recorded_at)`; a self-referencing foreign key for `supersedes_id`; optionally a trigger or `REVOKE UPDATE, DELETE` to make the table append-only. Overlap in effective time cannot be enforced declaratively because "current as of T" is not a column value. `CURRENT_TIMESTAMP` "return[s] the start time of the current transaction" and "their values do not change during the transaction" (S8 §9.9.5), so two assertions committed in one transaction share `recorded_at` and need a sequence or explicit ordering column to be totally ordered.

**Sourced by.** S2, S3, S4, S5, S8.

### Candidate B — Two-range bitemporal row (`effective` range + `recorded` range in one table)

**Description.** The textbook bitemporal relation (S1 §3.8) laid out as one row per version: `effective daterange` (or `tstzrange`) and `recorded tstzrange`. Writing a change closes the current version's `recorded` range at `now` (its only permitted mutation, and it is semantically an append in record time) and inserts the new version with `recorded = [now, infinity)`. Both ranges use PostgreSQL's closed-open canonical form: "The built-in range types int4range, int8range, and daterange all use a canonical form that includes the lower bound and excludes the upper bound; that is, [)" (S6 §8.17.7). An open end is an unbounded upper bound (`(,)`-style), for which `upper()` returns NULL and `upper_inf()` returns true (S7 Table 9.60); `'infinity'` is also accepted as a bound for `date` and `timestamp` (S9 Table 8.13).

**"What did the record say last Tuesday?"** One predicate: `WHERE recorded @> T::timestamptz AND effective @> D::date` (`anyrange @> anyelement`: "Does the range contain the element?" — S7 Table 9.58). No anti-join; both dimensions are first-class range columns, and "A GiST or SP-GiST index on ranges can accelerate queries involving these range operators: =, &&, <@, @>, <<, >>, -|-, &<, and &>" (S6 §8.17.9).

**Correction vs supersession.** Both close the old version's `recorded` range and insert. The shape makes the difference visible and enforceable: a correction inserts a row with the *same* `effective` range and different attributes; a supersession inserts a row with the old `effective` range shortened (`effective = daterange(old_from, new_from)`) and a second row for the new period. A `change_kind` column plus a CHECK/trigger that a `CORRECTION` reuses the predecessor's `effective` bounds turns the convention into an invariant. The repo's `supersedes_id` maps directly onto "the row whose `recorded` upper bound equals my `recorded` lower bound".

**PostgreSQL mechanisms.** `daterange`/`tstzrange`; exclusion constraint so that no two versions overlap in *both* dimensions for one entity: "You can use the btree_gist extension to define exclusion constraints on plain scalar data types, which can then be combined with range exclusions" (S6 §8.17.10; S21 documents the btree_gist operator classes) — `EXCLUDE USING GIST (entity_id WITH =, effective WITH &&, recorded WITH &&)`. "Adding an exclusion constraint will automatically create an index of the type specified in the constraint declaration" (S10 §5.5.6). From PostgreSQL 18 the *current* slice can also use the standard-flavoured syntax: `UNIQUE (id, valid_at WITHOUT OVERLAPS)` "behaves like EXCLUDE USING GIST (id WITH =, valid_at WITH &&)"; "The WITHOUT OVERLAPS column must have a range or multirange type. Empty ranges/multiranges are not permitted"; "By default, only range types are supported, but you can use other types by adding the btree_gist extension (which is the expected way to use this feature)" (S11). Note that `WITHOUT OVERLAPS` takes one range column, so it constrains one dimension; the two-dimensional rule still needs the explicit `EXCLUDE`. Multiranges (S6 §8.17) can hold non-contiguous effective periods in one row if ever needed.

**Sourced by.** S1, S6, S7, S9, S10, S11.

### Candidate C — SQL:2011 split: application-time period on the current table, system-versioned history table

**Description.** The standard's shape as vendors document it. The current table carries an application-time period (`PERIOD FOR validity (start_date, end_date)` in standard syntax) and system versioning archives every superseded row version into a separate history table with machine-maintained system-time columns. IBM's definitions (S12): "A system-period temporal table is a table that maintains historical versions of its rows"; "An application-period temporal table is a table that stores the in effect aspect of application data"; "A bitemporal table is a table that combines the historical tracking of a system-period temporal table with the time-specific data storage capabilities of an application-period temporal table." For application periods, "there is no separate history table. Past, present, and future effective dates and their associated business data are maintained in a single table." MariaDB (S13, S14): "Bitemporal tables are tables that use versioning both at the system and application-time period levels"; `FOR SYSTEM_TIME AS OF | BETWEEN ... AND | FROM ... TO | ALL`; `WITHOUT OVERLAPS` on unique keys since MariaDB 10.5.3; system versioning "store[s] the history of all changes, not only data which is currently applicable".

The `periods` extension README (S15) states the period rule precisely: "Defining a period constrains the two columns such that the start column's value must be strictly inferior to the end column's value, and that both columns be non-null. The period's value includes the start value but excludes the end value. A period is therefore very similar to PostgreSQL's range types, but a bit more restricted." For `SYSTEM_TIME`: "In the SQL standard, the start column is GENERATED ALWAYS AS ROW START and the end column is GENERATED ALWAYS AS ROW END. This extension uses triggers to set the start column to transaction_timestamp() and the end column is always 'infinity'." And: "It is generally unwise to use anything but timestamp with time zone because changes in the TimeZone configuration paramater or even just Daylight Savings Time changes can distort the history."

**"What did the record say last Tuesday?"** `SELECT ... FROM t FOR SYSTEM_TIME AS OF T` (standard; `t__as_of(T)` in `periods`), then filter the application period for D. Because system time is maintained by the engine, no anti-join is needed; the history table plus the current table together form Candidate B's two-range relation, split across two tables.

**Correction vs supersession.** A correction is an ordinary `UPDATE` of the row's attributes with the application period untouched; system versioning archives the previous version. A supersession is `UPDATE ... FOR PORTION OF validity FROM x TO y` (or `DELETE ... FOR PORTION OF`), where "Rows are inserted as needed for the portions not being updated or deleted. Yes, that means a simple DELETE statement can actually INSERT rows!" (S15). MariaDB documents the same splitting for `FOR PORTION OF` (rows fully containing the range are split into up to three) and notes `system_time` cannot be the target of `FOR PORTION OF` (S13, S14). The standard carries no "reason" column: whether an archived version was corrected or superseded is inferable only by comparing period bounds between the history row and its successor, so ADR-015 would still add an explicit `change_kind` and a `supersedes_id`-equivalent (the history row's own id) if the distinction must be queryable rather than reconstructed.

**PostgreSQL mechanisms.** In core, PostgreSQL 18 has the temporal *constraints* only: "Allow the specification of non-overlapping PRIMARY KEY, UNIQUE, and foreign key constraints (Paul A. Jungwirth) [...] specified by WITHOUT OVERLAPS for PRIMARY KEY and UNIQUE, and by PERIOD for foreign keys, all applied to the last specified column" (S16). For temporal foreign keys "the constraint is considered satisfied if the referenced table has matching records (based on the non-PERIOD parts of the key) whose combined PERIOD values completely cover the referencing record's" and "the referenced table must have a primary key or unique constraint declared with WITHOUT OVERLAPS" (S11). PostgreSQL 18 has **no** `PERIOD FOR` column pairs, no `GENERATED ALWAYS AS ROW START` (S11: the only generated-column syntax is `GENERATED ALWAYS AS ( generation_expr ) [ STORED | VIRTUAL ]`), no `FOR SYSTEM_TIME`, and no `FOR PORTION OF` (the UPDATE reference page contains neither "FOR PORTION OF" nor "period" — S17). Those pieces come from:

- `periods` (S15): implements periods, `WITHOUT OVERLAPS` unique keys, temporal foreign keys, `FOR PORTION OF` via an `INSTEAD OF` trigger view, `SYSTEM_TIME` and `SYSTEM VERSIONING` with a separate history table ("The history data is also read-only. In order to trim old data, SYSTEM VERSIONING must be suspended."), and `t__as_of/__from_to/__between/__between_symmetric` functions. README banner: "*compatible 9.5–15*"; `periods.control` has `requires = 'btree_gist'`. PostgreSQL License.
- `temporal_tables` (S18): "Currently, Temporal Tables Extension supports the system-period temporal tables only." Trigger `versioning(<system_period_column_name>, <history_table_name>, <adjust>)` on a `tstzrange` column; "The trigger generates this value by using a CURRENT_TIMESTAMP value which denotes the time when the first data change statement was executed in the current transaction"; "If a single transaction makes multiple updates to the same row, only one history row is generated"; the `adjust` flag resolves concurrent-update ordering by moving the start "to time T2 plus delta (a small interval of time, typically equals to 1 microsecond)"; `set_system_time()` overrides the clock for backfills. BSD 2-clause.

So on PostgreSQL, Candidate C is: core constraints for non-overlap and period-covering foreign keys (PG18), plus triggers (extension or hand-written) for system versioning and portion splitting.

**Sourced by.** S11, S12, S13, S14, S15, S16, S17, S18.

### Candidate D — Bitemporal event log with projections

**Description.** Fowler's second implementation route in "Bitemporal History" (S3): event sourcing where every event stores both an actual (effective) timestamp and a record timestamp, and current or as-of state is a projection over the events. Fits the repo's existing "immutable BizTrust assertion" language and the `source_received_at` / `recorded_at` split, since a received document is itself an event.

**"What did the record say last Tuesday?"** Replay events with `recorded_at <= T`, ordered by record time, and fold them into state along effective time; read the resulting entity as of D. In practice a projection table shaped like Candidate B (two ranges) is materialised so the read is a range predicate rather than a replay.

**Correction vs supersession.** Encoded as distinct event types: a `Corrected` event references the event it corrects (the `supersedes_id` role); a supersession is a new domain event (`CoverAmended`, `PolicyCancelled`) with its own `effective_from`. The distinction is explicit and durable because it lives in the event, not in a projection.

**PostgreSQL mechanisms.** An append-only events table (`recorded_at timestamptz`, `effective_at date` or range, `effective_timezone`, `kind`, `causes_event_id`) with a monotonic sequence for ordering inside one transaction (again because `CURRENT_TIMESTAMP` is per-transaction — S8). Declarative non-overlap is only available on the projection (as in Candidate B), not on the event log.

**Sourced by.** S3, S6, S8.

### Object-model patterns (not storage candidates)

Fowler's Temporal Property ("A property that changes over time"; accessor "that takes a Time Point as an argument: this allows you to ask 'what was Mr Fowler's address on 2 Feb 1998?'" — S19) and Temporal Object ("An object that changes over time", a continuity object with versions each carrying an Effectivity; use it "when business stakeholders explicitly need to reference versions or amendments" — S20) describe the API on top of any of A–D. Insurance endorsements are exactly the "versions or amendments" case, so Temporal Object is the likely domain-layer shape regardless of storage.

## The timezone question for effective dates

What PostgreSQL's `timestamp with time zone` does and does not store (S8, S9, S22):

- "In either case, the value is stored internally as UTC, and the originally stated or assumed time zone is not retained." (§8.5.1.3)
- "For timestamp with time zone values, an input string that includes an explicit time zone will be converted to UTC [...] using the appropriate offset for that time zone." "If no time zone is stated in the input string, then it is assumed to be in the time zone indicated by the system's TimeZone parameter, and is converted to UTC using the offset for the timezone zone." (§8.5.1.3)
- "When a timestamp with time zone value is output, it is always converted from UTC to the current timezone zone, and displayed as local time in that zone." (§8.5.1.3)
- "In a value that has been determined to be timestamp without time zone, PostgreSQL will silently ignore any time zone indication." (§8.5.1.3)
- `TimeZone` "Sets the time zone for displaying and interpreting time stamps. The built-in default is GMT, but that is typically overridden in postgresql.conf; initdb will install a setting there corresponding to its system environment." (S22)
- "abbreviations represent a specific offset from UTC, whereas many of the full names imply a local daylight-savings time rule, and so have two possible UTC offsets." "For times in the future, the assumption is that the latest known rules for a given time zone will continue to be observed indefinitely far into the future." (§8.5.3)
- `date` has 1-day resolution; `timestamp with time zone` has 1-microsecond resolution (Table 8.9).
- `timestamp without time zone AT TIME ZONE zone` "Converts a timestamp without time zone to timestamp with time zone, assuming the given value is in the named time zone"; the reverse form "Converts a timestamp with time zone to timestamp without time zone, as the time would appear in that zone." (S8 §9.9.4)

Consequences for `effective_from` / `effective_to` / `effective_timezone`:

1. A `timestamptz` alone cannot carry the *basis* an insurer or regulator stated ("cover from 00:00 on 1 October, local time"). The instant survives, the stated zone does not. `FLOWS.md` §10A's separate `effective_timezone` ("Timezone/basis used by the authoritative source") is therefore required in every candidate, not optional.
2. Effective bounds that the source states as dates should be stored as `date` / `daterange` in the source's basis, with `effective_timezone` as an IANA full name (`Asia/Vientiane` style, from `pg_timezone_names`), not an abbreviation, so a later conversion to an instant applies the right DST rules. Conversion to an instant happens at query time: `(effective_from::timestamp) AT TIME ZONE effective_timezone`.
3. If an effective *instant* is stored as `timestamptz` (for example a mid-day cancellation), the zone column still needs to be recorded next to it, because displaying it back "as the source wrote it" depends on the session `TimeZone`, which is server- or client-configured, not data.
4. Future-dated effective bounds converted to instants inherit PostgreSQL's assumption that current zone rules persist; a political change to zone rules can move the instant. Storing the date plus zone (and converting late) keeps the stated fact stable.
5. Record time is unambiguous: `recorded_at` is an instant and should be `timestamptz` (the `periods` README's warning applies: anything else "can distort the history").

## Retrofit cost of each candidate onto a single-timestamp table

Assume the starting table has one `created_at timestamptz` and is mutated in place. Mechanical facts from `ALTER TABLE` (S23):

- Adding a column with a NULL default or a non-volatile default is metadata-only: "In neither case is a rewrite of the table required."
- "Adding a column with a volatile DEFAULT (e.g., clock_timestamp()), a stored generated column, an identity column, or a column with a domain data type that has constraints will cause the entire table and its indexes to be rewritten."
- `ADD CONSTRAINT` "will cause a scan of the table to verify that all existing rows in the table satisfy the new constraint"; `NOT VALID` "is currently only allowed for foreign-key, CHECK, and not-null constraints" — so an exclusion or `WITHOUT OVERLAPS` constraint cannot be added lazily; existing overlaps must be cleaned first.
- Changing a column's type "will normally cause the entire table and its indexes to be rewritten", except when binary-coercible.

| Candidate | Schema change | Data backfill | Code change | Irrecoverable loss |
|---|---|---|---|---|
| A (assertion log) | Add `effective_from/to`, `effective_timezone`, `source_*`, `recorded_at`, `supersedes_id`, `change_kind` (all nullable or constant default; no rewrite). Self-FK on `supersedes_id`. Revoke UPDATE/DELETE. | `recorded_at := created_at` is honest. `effective_from` for existing rows is **unknown** unless a source document supplies it; defaulting it to `created_at` asserts a business fact BizTrust never learned, which §10A forbids. | Every UPDATE path becomes INSERT-with-`supersedes_id`; as-of reads need the anti-join. | Pre-retrofit history: rows were overwritten, so what the record said last Tuesday *before* the retrofit is gone. |
| B (two-range row) | Add `effective daterange`, `recorded tstzrange`, `change_kind`; `CREATE EXTENSION btree_gist`; `EXCLUDE USING GIST (entity_id WITH =, effective WITH &&, recorded WITH &&)` — full-table scan at creation, no `NOT VALID`. | `recorded := tstzrange(created_at, 'infinity')`; `effective` same problem as A. | Write path becomes close-then-insert; reads become two `@>` predicates. Simplest as-of query of the four. | Same as A. |
| C (SQL:2011 split) | Keep table as "current"; add period columns and `PRIMARY KEY (id, effective WITHOUT OVERLAPS)` (PG18) or the `EXCLUDE` equivalent; `ALTER TABLE ... ADD COLUMN sys_period tstzrange NOT NULL` plus history table (`CREATE TABLE ..._history (LIKE ...)`) and a versioning trigger, exactly as `temporal_tables` shows (S18). | `sys_period := [created_at, infinity)`; `effective` same problem as A. | Smallest: corrections stay plain UPDATEs; supersessions need a `FOR PORTION OF` emulation (application-side split, `periods` view if on PG ≤ 15, or a hand-written trigger). | Same as A; additionally, record-time granularity is transaction start (S8, S18), so intra-transaction ordering must be added if needed. |
| D (event log) | New events table and projection tables; existing rows become synthetic `Imported` events. | `recorded_at := created_at` on the import event; effective bounds carried as "unknown" on the import event rather than fabricated. | Largest: all writes become events; every read goes through a projection. | Same as A, but the import event records *that* the history is missing, which is the most honest of the four. |

The cost that dominates all four is not DDL; it is the semantic backfill. A table that started with one timestamp has conflated effective time with record time, and the effective half cannot be recovered from the database. It can only be re-sourced from documents (`source_created_at` / `source_received_at`) or marked unknown.

## Decision-relevant facts for ADR-015

1. **`timestamptz` stores an instant in UTC and discards the stated zone** ("the originally stated or assumed time zone is not retained" — S9 §8.5.1.3). Effective dates therefore need a `date`/`daterange` in the source's basis plus an IANA full-name `effective_timezone`, with conversion to instants deferred to query time; record time (`recorded_at`) should be `timestamptz`.
2. **PostgreSQL 18 core provides SQL:2011 temporal *constraints* but not temporal *DML or versioning*:** `WITHOUT OVERLAPS` on PRIMARY KEY/UNIQUE and `PERIOD` foreign keys over range/multirange columns (S11, S16), with `btree_gist` "the expected way to use this feature"; there is no `FOR PORTION OF`, no `FOR SYSTEM_TIME`, no `GENERATED ALWAYS AS ROW START` (S11, S17). History and portion splitting come from triggers: `periods` (README: "compatible 9.5–15", requires `btree_gist`) or `temporal_tables` (system period only), or hand-written.
3. **Record time is a period per row version, not an instant, and is append-only** (S1 §3.2: "transaction times are generally not time instants, but have duration [...] (past) transaction times cannot be changed"; S2: record-time changes are only additive). The one-instant `recorded_at` + `supersedes_id` shape in `FLOWS.md` §10A answers "last Tuesday" only through an anti-join; a `recorded tstzrange` (Candidate B) or an engine-maintained system period (Candidate C) answers it with one `@>` predicate.
4. **Correction and supersession are not distinguishable from timestamps in any candidate.** All four need an explicit kind and a pointer (`supersedes_id` or event causation). The two-range shape can make the rule an invariant: a correction reuses the predecessor's `effective` bounds; a supersession changes them. `CURRENT_TIMESTAMP` is constant within a transaction (S8), so a sequence or explicit ordering column is needed wherever several assertions can be committed together.
5. **Retrofit is cheap in DDL and expensive in truth.** Nullable/constant-default columns add without a rewrite; exclusion and `WITHOUT OVERLAPS` constraints scan the whole table and cannot be `NOT VALID` (S23); but `effective_from` for rows that predate the retrofit cannot be derived from `created_at` without asserting something BizTrust never knew — it must be re-sourced or recorded as unknown, and pre-retrofit record history is unrecoverable. Every candidate carries this cost equally, which argues for fixing the temporal shape before schema freeze, as `FLOWS.md` §10A already requires.

## Unverified items

- **ISO/IEC 9075-2:2011 text.** The ISO catalogue page (https://www.iso.org/standard/53682.html) returned HTTP 403 on 2026-09-05 and the standard's text is not freely available. Every SQL:2011 statement above is taken from vendor primary documentation (IBM Db2, MariaDB) and from the `periods` README's "-- Standard SQL" examples, not from the standard itself. UNVERIFIED that the vendor forms match the standard letter-for-letter.
- **WG2 N1536 "Temporal features in SQL standard" (Kulkarni, IBM).** Linked from the `temporal_tables` README at http://metadata-standards.org/Document-library/Documents-by-number/WG2-N1501-N1550/WG2_N1536_koa046-Temporal-features-in-SQL-standard.pdf; on 2026-09-05 that URL served an HTML page, not the PDF. Not consulted. UNVERIFIED.
- **Snodgrass, "Developing Time-Oriented Database Applications in SQL" (1999).** The author's free PDF (https://www2.cs.arizona.edu/~rts/tdbbook.pdf, 5 MB) downloaded but is a scanned image; `pdftotext` recovered only figure axis labels ("Valid time" / "Transaction time"). Definitions were therefore taken from the Consensus Glossary (S1), which Snodgrass co-authored and which is text-extractable. Any attribution of the closed-open `[)` convention or of the "current / sequenced / nonsequenced" query taxonomy to specific book pages is UNVERIFIED here; the closed-open convention is sourced instead from PostgreSQL (S6 §8.17.7) and the `periods` README (S15).
- **IBM Db2 `FOR PORTION OF BUSINESS_TIME` and `FOR BUSINESS_TIME AS OF` syntax detail.** Only the landing-page definitions and the sentences quoted under Candidate C were retrievable (S12); the querying and updating sub-pages resolved to a documentation index. The row-splitting semantics quoted are from MariaDB (S13) and `periods` (S15). UNVERIFIED for Db2 specifically.
- **`periods` on PostgreSQL 16+.** The README banner reads "compatible 9.5–15" on 2026-09-05; whether later releases or forks support 16–18 is UNVERIFIED.
- **Whether `btree_gist` is a trusted extension** (installable without superuser) on the target hosting. UNVERIFIED; not checked in the PostgreSQL docs for this ticket.
- **MariaDB version numbers** other than "WITHOUT OVERLAPS since 10.5.3" are UNVERIFIED (the fetched page summarised them).

## Sources

All URLs checked 2026-09-05.

- **S1** — Jensen, C. S., Dyreson, C. E. (eds.), Böhlen, Clifford, Elmasri, Gadia, Grandi, Hayes, Jajodia, Käfer, Kline, Lorentzos, Mitsopoulos, Montanari, Nonen, Peressi, Pernici, Roddick, Sarda, Scalas, Segev, **Snodgrass**, Soo, Tansel, Tiberio, Wiederhold. "The Consensus Glossary of Temporal Database Concepts — February 1998 Version", LNCS 1399, pp. 367–405. Author-hosted PDF: https://www2.cs.arizona.edu/~rts/pubs/LNCS1399.pdf (linked from https://www2.cs.arizona.edu/~rts/publications.html). §3.1 Valid Time (p. 370), §3.2 Transaction Time (p. 371), §3.8 Bitemporal Relation (p. 373).
- **S2** — Fowler, M. "Temporal Patterns" (Dimensions of Time; Audit Log, Effectivity, Temporal Property, Temporal Object, Snapshot). https://martinfowler.com/eaaDev/timeNarrative.html (page dated 16 February 2005).
- **S3** — Fowler, M. "Bitemporal History", 7 April 2021. https://martinfowler.com/articles/bitemporal-history.html
- **S4** — Fowler, M. "Audit Log". https://martinfowler.com/eaaDev/AuditLog.html
- **S5** — Fowler, M. "Effectivity". https://martinfowler.com/eaaDev/Effectivity.html
- **S6** — PostgreSQL 18 documentation, §8.17 "Range Types" (8.17.3 bounds, 8.17.4 infinite ranges, 8.17.7 discrete canonical form, 8.17.9 indexing, 8.17.10 constraints on ranges). https://www.postgresql.org/docs/current/rangetypes.html
- **S7** — PostgreSQL 18 documentation, §9.20 "Range/Multirange Functions and Operators" (Table 9.58 operators, Table 9.60 functions). https://www.postgresql.org/docs/current/functions-range.html
- **S8** — PostgreSQL 18 documentation, §9.9 "Date/Time Functions and Operators" (9.9.4 `AT TIME ZONE`, 9.9.5 Current Date/Time: `CURRENT_TIMESTAMP`/`transaction_timestamp()`, `statement_timestamp()`, `clock_timestamp()`). https://www.postgresql.org/docs/current/functions-datetime.html
- **S9** — PostgreSQL 18 documentation, §8.5 "Date/Time Types" (Table 8.9 storage/resolution, 8.5.1.3 Time Stamps, Table 8.13 special inputs, 8.5.3 Time Zones). https://www.postgresql.org/docs/current/datatype-datetime.html
- **S10** — PostgreSQL 18 documentation, §5.5.6 "Exclusion Constraints". https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION
- **S11** — PostgreSQL 18 documentation, `CREATE TABLE` reference (`UNIQUE`/`PRIMARY KEY ... WITHOUT OVERLAPS`, `FOREIGN KEY ... PERIOD`, `EXCLUDE`, generated columns). https://www.postgresql.org/docs/current/sql-createtable.html
- **S12** — IBM Db2 11.5 documentation, "Time Travel Query using temporal tables" and sub-pages "System-period temporal tables", "Application-period temporal tables". https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-time-travel-query-using-temporal ; https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-system-period-temporal ; https://www.ibm.com/docs/en/db2/11.5.x?topic=tables-application-period-temporal
- **S13** — MariaDB Server documentation, "Application-Time Periods". https://mariadb.com/kb/en/application-time-periods/ and https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/application-time-periods
- **S14** — MariaDB Server documentation, "System-Versioned Tables" and "Bitemporal Tables". https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables ; https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/bitemporal-tables
- **S15** — `periods` extension, README and `periods.control` from the project repository. https://github.com/xocolatl/periods (raw: https://raw.githubusercontent.com/xocolatl/periods/master/README.md , https://raw.githubusercontent.com/xocolatl/periods/master/periods.control). PostgreSQL License.
- **S16** — PostgreSQL 18.0 release notes, E.6.3.2.1 Constraints. https://www.postgresql.org/docs/release/18.0/
- **S17** — PostgreSQL 18 documentation, `UPDATE` reference (no `FOR PORTION OF`). https://www.postgresql.org/docs/current/sql-update.html
- **S18** — `temporal_tables` extension, README from the project repository. https://github.com/arkhipov/temporal_tables (raw: https://raw.githubusercontent.com/arkhipov/temporal_tables/master/README.md). BSD 2-clause.
- **S19** — Fowler, M. "Temporal Property". https://martinfowler.com/eaaDev/TemporalProperty.html
- **S20** — Fowler, M. "Temporal Object". https://martinfowler.com/eaaDev/TemporalObject.html
- **S21** — PostgreSQL 18 documentation, §F.8 `btree_gist`. https://www.postgresql.org/docs/current/btree-gist.html
- **S22** — PostgreSQL 18 documentation, §19.11.2 `TimeZone` parameter. https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-TIMEZONE
- **S23** — PostgreSQL 18 documentation, `ALTER TABLE` reference (`ADD COLUMN` rewrite rules, `ADD table_constraint [NOT VALID]`, `SET DATA TYPE`). https://www.postgresql.org/docs/current/sql-altertable.html
- Repo context (read-only): `docs/architecture/FLOWS.md` §10A "Effective time and record time"; `docs/architecture/ADR_REGISTER.md` row ADR-015.

<!-- agent: researcher (wayfinder research, 2026-09-05) -->
