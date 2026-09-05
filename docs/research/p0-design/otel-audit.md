# OpenTelemetry conventions for reconstructing one request, and audit versus logs

| Field | Value |
|---|---|
| Research date | `2026-09-05` (every URL below was checked on this date) |
| Ticket | [Issue #135](https://github.com/bstBizEra/biztrust_guide/issues/135), parent [#128](https://github.com/bstBizEra/biztrust_guide/issues/128) |
| Repository baseline reviewed | `e5398c9` (`origin/main`) |
| Repository vocabulary | `docs/architecture/BIZTRUST-ARCH-001.md` section 15 (audit and observability), read only |
| Research status | `COMPLETE FOR P0.10 / P0.11 DESIGN INPUT; ISO/IEC 27001 CONTROL TEXT UNVERIFIED` |
| Implementation authority | `NOT GRANTED` |

Source discipline: only the OpenTelemetry specification and semantic conventions, the W3C Trace Context Recommendation, the OpenTelemetry Collector documentation, NIST SP 800-92 and NIST SP 800-53 Rev. 5 (from NIST's own OSCAL catalog), PostgreSQL's own logging documentation and the pgAudit README are cited as evidence. Anything that could not be read from an official source is listed under "Unverified items" and is not relied on.

## 1. Ticket

[#135 "[P0-DESIGN] Research: OpenTelemetry conventions for reconstructing one request, and audit versus logs"](https://github.com/bstBizEra/biztrust_guide/issues/135). It blocks #143 and #146.

## 2. Question

P0.10 needs attributable audit evidence and P0.11 needs one request reconstructed through logs, metrics and traces. What do OpenTelemetry's specification and semantic conventions, and the W3C Trace Context Recommendation, say about trace-context propagation, HTTP and database span attributes, log-trace correlation, the Collector's role, and sensitive data in attributes? Separately, what do citable standards require of an audit record (attributability, integrity, retention) that a log line does not provide, so that the P0.10 audit design does not become "logs with a different name"?

`BIZTRUST-ARCH-001` section 15 already lists what a material action must be reconstructable from: tenant and legal entity; actor or service principal; operation and resource; previous and resulting business state; timestamp, request ID and trace ID; authorization decision and authority reference; workflow, correlation and causation IDs; source system and external reference; approved source revision and contract version. It also states that logs and traces must not expose secrets, raw credentials, unnecessary personal data or cross-tenant information, and that audit records require separate retention, access and mutation controls. This note maps those requirements to what the cited sources actually define.

## 3. Trace context propagation (sourced)

Source: W3C Trace Context, W3C Recommendation 23 November 2021 [S1]; OpenTelemetry Propagators API [S2]; OpenTelemetry Tracing API [S3].

- `traceparent` is one header with four dash-separated fields: `version` (2 hex digits, currently `00`), `trace-id` (32 hex digits, 16 bytes), `parent-id` (16 hex digits, 8 bytes) and `trace-flags` (2 hex digits). All-zero `trace-id` or `parent-id` is invalid. Example from the Recommendation: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`. [S1]
- A receiver that gets a valid `traceparent` MUST propagate it (and `tracestate`) on outgoing requests; the only permitted `traceparent` mutations are setting `parent-id` to the ID of the current operation, updating the `sampled` flag when doing so, or restarting the trace. If `trace-id` or `parent-id` is invalid the vendor MUST ignore the header. [S1]
- `tracestate` carries vendor-specific key/value pairs (at most 32 list members); vendors SHOULD propagate at least 512 characters of the combined header and, when truncating, drop entries longer than 128 characters first. [S1]
- Privacy: "Tracing vendors MUST NOT use `traceparent` and `tracestate` fields for any personally identifiable or otherwise sensitive information", and random ID generators "MUST NOT rely on any information that can potentially be user-identifiable". Security: a public API that naively continues any incoming trace with `sampled` set can be used to overwhelm the service with tracing overhead, so the Recommendation tells vendors to keep "checks and balances" against callers who deny or abuse monitoring. [S1, sections 6 and 7]
- OpenTelemetry's `SpanContext` mirrors the header: a valid `TraceId` is a 16-byte array with at least one non-zero byte, a valid `SpanId` an 8-byte array with at least one non-zero byte, plus `TraceFlags` (sampled, random-trace-id), `TraceState`, and `IsRemote`, which MUST be `true` for a context extracted through the Propagators API. [S3]
- The Propagators API defines `TextMapPropagator` with `Inject` (write context into a carrier such as HTTP headers) and `Extract` (read it back). On parse failure `Extract` "MUST NOT throw an exception and MUST NOT store a new value in the Context". The specification requires W3C TraceContext, W3C Baggage and B3 propagators to be maintained as core packages, and requires a composite propagator facility. The global propagator is a no-op until configured. [S2]
- Span kinds that P0.11 reconstruction relies on: `SERVER` (incoming request), `CLIENT` (outgoing request awaiting a response), `PRODUCER`/`CONSUMER` (deferred, for messaging or workflow hops) and `INTERNAL` (the default). Span status is `Unset`, `Ok` or `Error`, and setting `Ok` overrides any prior or later `Error`. [S3]

Consequence for BizTrust: the request ID in ARCH-001 section 15 and the W3C `trace-id` are different things. `trace-id` is the only identifier the specification guarantees to cross process boundaries by default; a business request ID or correlation ID must be carried as a span attribute, a log attribute or (with care, see section 6) Baggage.

## 4. HTTP and database semantic conventions the request needs (sourced)

Source: OpenTelemetry semantic conventions, HTTP spans (Stable) [S4], HTTP metrics (Stable) [S5], database client spans (Stable, with two Development attributes) [S6], attribute requirement levels [S7], service and deployment resource attributes [S8, S9].

Requirement-level vocabulary used below: `Required` means "All instrumentations MUST populate the attribute"; `Conditionally Required` means MUST when the stated condition holds; `Recommended` means SHOULD by default when readily available; `Opt-In` means populate "if and only if the user configures the instrumentation to do so", because such attributes "might pose a security or privacy risk" or are expensive. [S7]

### 4.1 HTTP server span (`SpanKind = SERVER`, name `{method} {http.route}`) [S4]

| Attribute | Level | Note from the convention |
|---|---|---|
| `http.request.method` | Required | HTTP method |
| `url.path` | Required | URI path; "Sensitive content provided in `url.path` SHOULD be scrubbed when instrumentations can identify it" |
| `url.scheme` | Required | `http` or `https` |
| `http.response.status_code` | Conditionally Required (if a status was sent) | 4xx is not an error for a SERVER span; 5xx SHOULD set status `Error` |
| `http.route` | Conditionally Required (if available) | Route template, MUST be low cardinality; not the raw path |
| `error.type` | Conditionally Required (if the request ended in error) | Low-cardinality error class |
| `url.query` | Conditionally Required (if present) | Same redaction rules as `url.full`; redacted values keep the key |
| `http.request.method_original` | Conditionally Required | Only if it differs from the normalized method |
| `server.port` | Conditionally Required | If `server.address` is set |
| `network.protocol.name` | Conditionally Required | If not `http` |
| `client.address` | Recommended | Original client behind proxies when known (`Forwarded`, `X-Forwarded-For`), else the peer |
| `server.address` | Recommended | Local server name |
| `user_agent.original` | Recommended | Raw `User-Agent` |
| `network.peer.address`, `network.peer.port`, `network.protocol.version` | Recommended | Connection-level facts |
| `http.request.header.<key>`, `http.response.header.<key>` | Opt-In | "Requires explicit configuration"; "including all headers poses a security risk" |
| `http.request.body.size`, `http.response.body.size`, `http.request.size`, `http.response.size` | Opt-In | Sizes only; bodies are never an attribute |
| `client.port`, `network.local.address`, `network.local.port`, `network.transport`, `user_agent.synthetic.type` | Opt-In | |

### 4.2 HTTP server metric `http.server.request.duration` [S5]

Histogram, unit `s`, Stable, recommended explicit buckets `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]`. Attributes: `http.request.method` and `url.scheme` (Required); `error.type`, `http.response.status_code`, `http.route`, `network.protocol.name` (Conditionally Required); `network.protocol.version` (Recommended); `server.address`, `server.port`, `user_agent.synthetic.type` (Opt-In). This is the metric a P0.11 reconstruction joins to the trace through exemplars (section 5).

### 4.3 Database client span (`SpanKind = CLIENT`; name `{db.query.summary}`, else `{db.operation.name} {target}`) [S6]

| Attribute | Level | Note from the convention |
|---|---|---|
| `db.system.name` | Required | e.g. the DBMS product identifier |
| `db.namespace` | Conditionally Required (if available) | Database name |
| `db.collection.name` | Conditionally Required (if the operation targets one) | Table name |
| `db.operation.name` | Conditionally Required | Command, e.g. `SELECT`, `INSERT` |
| `db.response.status_code` | Conditionally Required (on failure, if available) | Database-reported status code |
| `error.type` | Conditionally Required (on failure) | |
| `server.port` | Conditionally Required (non-default port and `server.address` set) | |
| `db.query.text` | Recommended | Non-parameterized text "SHOULD be collected by default only if there is sanitization that excludes sensitive information" (literals replaced with `?`); parameterized query text "SHOULD NOT be sanitized" because the parameters travel separately |
| `db.query.summary` | Recommended | Low-cardinality grouping key |
| `db.operation.batch.size` | Recommended | |
| `server.address` | Recommended | |
| `db.query.parameter.<key>` | Opt-In (Development) | "SHOULD NOT be captured by default since values may contain PII or sensitive details" |
| `db.response.returned_rows` | Opt-In (Development) | |

### 4.4 Resource attributes that every span, metric and log record carries [S8, S9, S10]

A Resource is "an immutable representation of the observed entity for which telemetry is being produced", and all spans, metrics and logs from a provider MUST be associated with it [S10]. Service entity: `service.name` (Required, Stable), `service.namespace` (Required), `service.instance.id` (Required, unique per instance, UUID recommended), `service.version` (Recommended) [S8]; `deployment.environment.name` (Recommended, Stable; well-known values `development`, `staging`, `production`, `test`) [S9]. These are what tie a reconstructed request to the "approved source revision" in ARCH-001 section 15: `service.version` is the convention's slot for a build or commit identifier.

## 5. Log-trace correlation and the collector's role (sourced)

Source: OpenTelemetry Logs overview [S11], Logs data model [S12], general log attributes [S13], metrics data model (exemplars) [S14], Collector overview, configuration and architecture [S15, S16, S17].

### 5.1 How a log line joins a trace

- The Logs overview states the intent directly: "If the recorded logs contained trace context identifiers (such as trace and span IDs or user-defined baggage) it would result in much richer correlation between logs and traces", and it puts the Resource into every LogRecord so that logs, metrics and traces share the same origin attribution. [S11]
- The LogRecord data model fields are: `Timestamp` (when the event occurred at the source), `ObservedTimestamp` (when OpenTelemetry observed it), `TraceId` (W3C trace ID), `SpanId`, `TraceFlags`, `SeverityText`, `SeverityNumber` (normalized 1-24), `Body`, `Resource`, `InstrumentationScope`, `Attributes`, `EventName`. The rule is "If SpanId is present TraceId SHOULD be also present". [S12]
- Two mechanisms are specified for populating those fields: a Logs Bridge API with log appenders that enrich records from an existing logging library without changing it, or, for legacy applications, collecting log files with the Collector's `filelog` receiver and parsing the identifiers out of the text. The Logs overview recommends the bridge or direct OTLP delivery when the application can be changed. [S11]
- `log.record.uid` (Opt-In, Development) is the convention's slot for a per-record unique identifier used to detect duplicates; the recommended format is a ULID, with UUIDs acceptable, and two distinguishable records MUST have different values. `log.record.original` (Opt-In) preserves the complete original text when the Body is transformed. [S13]

### 5.2 How a metric joins a trace

An exemplar is "a recorded value that associates OpenTelemetry context to a metric event within a Metric"; it carries optional `trace_id` and `span_id`, `time_unix_nano`, the value, and `filtered_attributes`. Its stated purpose is to let users "link Trace signals w/ Metrics". For histograms and sums the exemplar's value is already included in the aggregate. [S14]

### 5.3 The Collector

- The Collector is "a vendor-agnostic way to receive, process and export telemetry data". Its components are receivers, processors, exporters, connectors and extensions, wired into one pipeline per signal (traces, metrics, logs). Direct export from the SDK is acceptable for getting started, but for production the Collector "can take care of additional handling like retries, batching, encryption or even sensitive data filtering". [S15]
- Processors are optional but some are recommended, and "The order of the processors in a pipeline determines the order of the processing operations that the Collector applies to the signal". Processors named in the configuration guide include `attributes` (insert, delete, hash), `resource`, `filter`, `memory_limiter`, `probabilistic_sampler` and `span`. [S16]
- Architecturally, the same receiver may feed several pipelines through a fan-out consumer, and "Each exporter gets a copy of each data element". A processor "might also drop the data if it's sampling or filtering". The docs describe two roles: an agent running as a daemon beside the application, and a gateway that receives from one or more agents and routes onward. [S17]

Consequence for BizTrust: the Collector is where a single redaction and routing policy can be applied to all three signals before anything leaves the trust boundary, and the fan-out means one pipeline can send the same records to an observability backend and to a separate, access-controlled audit sink. That fan-out does not by itself make the copy an audit record; section 7 explains what more is needed.

## 6. What the specification says about sensitive data in attributes (sourced)

The OpenTelemetry specification has no single "sensitive data" chapter; the guidance is distributed across the requirement-level definitions, individual conventions, the Baggage API, the W3C Recommendation and the Collector security guidance. What each says:

- Requirement levels: `Opt-In` exists precisely for attributes that "might pose a security or privacy risk"; they are not collected unless configured. [S7]
- URL attributes: `url.full` "MUST NOT contain credentials passed via URL"; userinfo SHOULD be redacted to `https://REDACTED:REDACTED@...`. The query keys `X-Amz-Signature`, `X-Amz-Credential`, `X-Amz-Security-Token`, `sig` and `X-Goog-Signature` SHOULD be redacted by default, keeping the key and replacing the value with `REDACTED`; "Sensitive content provided in `url.path` SHOULD be scrubbed when instrumentations can identify it". [S18, S4]
- HTTP headers: `http.request.header.<key>` and `http.response.header.<key>` are Opt-In and require explicit per-header configuration because capturing all headers "poses a security risk". Request and response bodies are not attributes at all; only their sizes are. [S4]
- Database: `db.query.text` is sanitized by default for non-parameterized queries (literals become `?`); `db.query.parameter.<key>` is Opt-In because values "may contain PII or sensitive details". [S6]
- End-user identity: `enduser.id` (Development) is documented as containing sensitive PII, and `enduser.pseudo.id` (Development) as a random identifier "intentionally disconnected from actual user identity" that is nonetheless linkable PII; `enduser.role` and `enduser.scope` are deprecated. The `user.*` registry offers `user.hash`, "Useful if `user.id` or `user.name` contain confidential information and cannot be used". [S19, S20]
- Baggage: application-defined key/value pairs propagated with the request; the API "MUST provide a way to remove all baggage entries from a context" specifically "To avoid sending any name/value pairs to an untrusted process". [S21]
- Propagation headers: the W3C Recommendation forbids PII or other sensitive information in `traceparent` and `tracestate`. [S1]
- Attribute limits: the SDK default is 128 attributes per record and no value-length limit; exceeding a configured limit truncates the value or discards the attribute. [S22]
- Collector: the security best practices say the `redaction` processor "deletes span, log, and metric datapoint attributes that don't match a list of allowed attributes" and masks values matching blocked patterns; the Collector should bind to specific interfaces rather than `0.0.0.0`, use TLS and authentication, and carry only needed components. [S23] The redaction processor supports `allowed_keys`, `ignored_keys`, `blocked_values` (regular expressions) and a `hash_function` (`md5`, `sha1`, `sha3`, `hmac-sha256`, `hmac-sha512`); stability is Beta for traces and Alpha for logs and metrics. [S24]

Consequence for BizTrust: the specification's default posture already excludes bodies, headers, query parameters and raw URL credentials; what it does not do is know which BizTrust attributes are cross-tenant or personal. Tenant ID, actor ID and business identifiers are application attributes, so their handling (hashing, allow-listing at the Collector, or keeping them out of telemetry and in the audit record only) is a BizTrust decision, not something the conventions settle.

## 7. Audit record versus log line

What the cited standards require of an audit record, and what a log line as defined by the OpenTelemetry data model does not provide by itself.

### 7.1 What the sources define

- NIST SP 800-92 defines a log as "a record of the events occurring within an organization's systems and networks" made of log entries, each about "a specific event". Audit records are one kind of log content: they "contain security event information such as successful and failed authentication attempts, file accesses, security policy changes, account changes ... and use of privileges". It states that SP 800-53 "describes several controls related to log management, including the generation, review, protection, and retention of audit records". [S25, Executive Summary, sections 2 and 2.1.2]
- NIST SP 800-53 Rev. 5, AU-3 (Content of Audit Records): audit records must establish (a) what type of event occurred, (b) when, (c) where, (d) the source of the event, (e) the outcome, and (f) "Identity of any individuals, subjects, or objects/entities associated with the event". The discussion adds "success or fail indications" and warns that audit trails can reveal personal information, "especially if the trail records inputs". [S26]
- AU-8 (Time Stamps): use internal system clocks and record time stamps at an organization-defined granularity in UTC, or with a fixed or recorded offset from UTC. [S26]
- AU-9 (Protection of Audit Information): "Protect audit information and audit logging tools from unauthorized access, modification, and deletion", and alert on detected unauthorized access, modification or deletion. [S26]
- AU-10 (Non-repudiation): "Provide irrefutable evidence that an individual (or process acting on behalf of an individual) has performed" organization-defined actions, obtained through "digital signatures and digital message receipts" and similar mechanisms. [S26]
- AU-11 (Audit Record Retention): retain audit records for an organization-defined period "to provide support for after-the-fact investigations of incidents and to meet regulatory and organizational information retention requirements". [S26]
- AU-12 (Audit Record Generation): the system must generate records for the AU-2 event types with the AU-3 content, and must allow designated personnel to select which event types are logged per component. [S26]
- SP 800-92 on integrity and access: "Ensuring that the original logs are not altered supports their use for evidentiary purposes" (footnote 23); log file integrity checking means "calculating a message digest for each file and storing the message digest securely to ensure that changes to archived logs are detected", with the digests protected by FIPS-approved cryptography or read-only media; users "should have append-only privileges and no read access if possible" and must not be able to rename or delete log files; logging should be configured to "Avoid recording unneeded sensitive data" such as passwords; and clocks should be kept consistent with NTP because inaccurate timestamps make cross-host analysis unreliable. It distinguishes log retention (routine archival) from log preservation (keeping records that would otherwise be discarded because they concern an investigation). [S25, sections 3.1, 5.1.3, footnotes 23 and 24]
- PostgreSQL's own logging (`log_statement = none | ddl | mod | all`) writes to the server log through `log_line_prefix`, whose escapes include `%u` user, `%d` database, `%a` application name, `%h` remote host, `%p` PID, `%m` timestamp, `%c` session ID, `%v`/`%x` transaction IDs, `%e` SQLSTATE and `%Q` query ID; statements with syntax errors are not captured by `log_statement` at all. [S27] pgAudit exists because "basic statement logging" shows what the user asked for, whereas "pgAudit focuses on the details of what happened while the database was satisfying the request"; it emits a structured `AUDIT:` entry with `AUDIT_TYPE`, `STATEMENT_ID`, `SUBSTATEMENT_ID`, `CLASS`, `COMMAND`, `OBJECT_TYPE`, `OBJECT_NAME`, `STATEMENT` and `PARAMETER`. Its own README records two limits that matter here: audit logging "is best-effort and not transactional", so entries can be lost if the server crashes before the log is flushed, and "It is not possible to reliably audit superusers with pgAudit". Its output still goes into the ordinary PostgreSQL server log. [S28]

### 7.2 What a log line lacks

Measured against AU-3, AU-8, AU-9, AU-10 and AU-11, an OpenTelemetry LogRecord [S12] is a data model, not an evidentiary control:

| Audit requirement (source) | What the LogRecord model gives | What is missing |
|---|---|---|
| Attributability: identity of the subject and objects (AU-3 f) | Free-form `Attributes`; `enduser.*` and `user.*` are Development-stability and flagged as PII [S19, S20] | No required actor field; no binding of the actor to an authenticated principal or to the authorization decision |
| Outcome (AU-3 e) | `SeverityNumber`, span status, `error.type` | Span status `Unset` is the default for successful 2xx and 4xx server spans [S4]; success is inferred, not asserted |
| Time (AU-8) | `Timestamp` and `ObservedTimestamp` in nanoseconds [S12] | No clock-source or synchronization guarantee; SP 800-92 treats inconsistent clocks as a first-order analysis problem [S25] |
| Integrity and protection (AU-9; SP 800-92 5.1.3) | None. Processors "might also drop the data" [S17]; sampling is a normal pipeline operation; attributes are truncated or discarded at limits [S22]; the redaction processor rewrites values [S24] | No hash chain, signature, append-only storage or alerting on modification; a pipeline that can legitimately sample, redact and drop cannot by construction promise completeness |
| Non-repudiation (AU-10) | None | No signature or receipt; `TraceId` is a random identifier, not a proof of who acted |
| Retention (AU-11; SP 800-92 retention versus preservation) | None in the model; retention is a backend property | No separate retention class, legal-hold or preservation semantics |
| Completeness of the audited event set (AU-2, AU-12) | Instrumentation decides what is emitted; Opt-In attributes are absent by default [S7] | No record that a selected event type was not emitted; pgAudit is explicit that its own output is best-effort [S28] |

The consequence is the one the ticket anticipated: a trace or a log stream, however well correlated, is an observability artefact whose design goals (sampling, redaction, cardinality control, bounded attributes) are in direct tension with the audit controls (completeness, immutability, attributability, retention). An audit record must be written by the application at the point of the state change, on the same transaction as the business write where the store allows it, with the actor, authority reference and before/after state that ARCH-001 section 15 lists, and it must carry the `trace-id` so that the observability artefacts can be found from it, not the other way round.

## 8. The field list a reconstructable request needs

One table. "Signal" says where the field lives; "Source" says who defines it. Fields marked "BizTrust" are application attributes that no convention defines; they exist to satisfy ARCH-001 section 15 and AU-3.

| # | Field | Signal | Convention name or slot | Source | Purpose in reconstruction |
|---|---|---|---|---|---|
| 1 | Trace ID | trace, log, metric exemplar | `SpanContext.TraceId` / `traceparent` trace-id / LogRecord `TraceId` / exemplar `trace_id` | [S1, S3, S12, S14] | The one identifier that joins all three signals and crosses process boundaries |
| 2 | Span ID and parent span ID | trace, log | `SpanContext.SpanId`, parent; LogRecord `SpanId` | [S3, S12] | Orders hops inside the request |
| 3 | Trace flags (sampled) | trace, log | `TraceFlags` | [S1, S12] | Tells the reader whether the trace was kept; an unsampled request has logs and audit only |
| 4 | Span kind | trace | `SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`, `INTERNAL` | [S3] | Distinguishes the inbound call from downstream calls and workflow hops |
| 5 | Timestamps | all | span start/end; LogRecord `Timestamp`, `ObservedTimestamp`; exemplar `time_unix_nano` | [S3, S12, S14] | AU-8; ARCH-001 "timestamp" |
| 6 | Service identity and version | resource on all | `service.name`, `service.namespace`, `service.instance.id`, `service.version`, `deployment.environment.name` | [S8, S9] | ARCH-001 "approved source revision"; which build handled the request |
| 7 | HTTP method, route, scheme, path | trace, metric | `http.request.method`, `http.route`, `url.scheme`, `url.path` | [S4, S5] | ARCH-001 "operation and resource" at the transport level |
| 8 | HTTP outcome | trace, metric | `http.response.status_code`, `error.type`, span status | [S4, S5] | AU-3 outcome at the transport level |
| 9 | Caller network facts | trace | `client.address`, `client.port` (Opt-In), `user_agent.original`, `network.peer.*` | [S4] | AU-3 "source of the event" at the network level |
| 10 | Database operation | trace | `db.system.name`, `db.namespace`, `db.collection.name`, `db.operation.name`, `db.query.summary`, `db.query.text` (sanitized), `db.response.status_code` | [S6] | Which tables the request touched and whether the write succeeded |
| 11 | Database-side identity | PostgreSQL log / pgAudit | `%u`, `%d`, `%a`, `%c`, `%x`, `%Q`; pgAudit `STATEMENT_ID`, `CLASS`, `COMMAND`, `OBJECT_NAME` | [S27, S28] | Independent confirmation from the store; `%a` (`application_name`) is the only conventional slot for carrying an application-side identifier into the server log |
| 12 | Request duration | metric | `http.server.request.duration` with exemplar | [S5, S14] | Joins the aggregate view to the single trace |
| 13 | Log record identity and severity | log | `log.record.uid`, `SeverityNumber`, `SeverityText`, `EventName`, `Body` | [S12, S13] | De-duplication and ordering of log lines within the trace |
| 14 | Tenant and legal entity | span/log attribute and audit record | BizTrust attribute (no convention) | ARCH-001 s.15 | Cross-tenant isolation of evidence; must not leak across tenants |
| 15 | Actor or service principal | audit record (attribute only if hashed or pseudonymous) | BizTrust attribute; convention offers only `enduser.id`/`enduser.pseudo.id` (Development, PII) and `user.hash` | [S19, S20]; ARCH-001 s.15; AU-3 f | Attributability |
| 16 | Authorization decision and authority reference | audit record | BizTrust attribute (no convention) | ARCH-001 s.15; AU-10 | Under which authority the action was permitted |
| 17 | Request ID, correlation ID, causation ID, workflow ID | span/log attribute, audit record | BizTrust attributes (no convention); Baggage only if cleared before untrusted hops | [S21]; ARCH-001 s.15 | Business-level joining across retries, workflows and asynchronous hops that a single trace may not span |
| 18 | Idempotency key and external reference | span/log attribute, audit record | BizTrust attribute (no convention) | ARCH-001 s.15 | Ties retried or externally-originated requests to one business action |
| 19 | Previous and resulting business state | audit record only | BizTrust (no convention; never a telemetry attribute) | ARCH-001 s.15; AU-3 e ("system ... posture after the event") | Reconstruction of the state change; contains business data, so stays out of telemetry |
| 20 | Contract version | span/log attribute, audit record | BizTrust attribute (no convention) | ARCH-001 s.15 | Which API contract the request was validated against |
| 21 | Integrity evidence | audit record only | Message digest or signature per record or per batch, protected separately | [S25 s.3.1, s.5.1.3]; AU-9, AU-10 | Tamper evidence; not provided by any telemetry signal |
| 22 | Retention class | audit record only | Retention versus preservation / legal hold marker | [S25]; AU-11 | Separate retention from telemetry |

## 9. Decision-relevant facts for P0.10 and P0.11

1. The W3C `trace-id` is the only identifier the specifications guarantee to propagate across process boundaries, and both the W3C Recommendation and the Propagators API forbid putting personal or sensitive data in `traceparent`/`tracestate`. BizTrust's request, correlation, causation and tenant identifiers are therefore application attributes that P0.11 must add on every span and log record itself; the conventions leave no slot for them. [S1, S2]
2. An audit record is defined by content and controls, not by format: AU-3 requires event type, time, location, source, outcome and the identity of subjects and objects; AU-9 requires protection from unauthorized modification and deletion with alerting; AU-10 requires irrefutable evidence of who acted; AU-11 requires a defined retention period. None of these is provided by the OpenTelemetry LogRecord, whose pipeline may legitimately sample, redact, truncate and drop. P0.10 must write audit records from the application at the state change, carrying the `trace-id`, and store them under separate access, integrity and retention controls, exactly as ARCH-001 section 15 already demands. [S12, S17, S22, S26]
3. The stable HTTP and database conventions already exclude the dangerous data by default: bodies are never attributes, headers and `db.query.parameter.*` are Opt-In, `url.full`/`url.query` credentials and signatures are redacted with `REDACTED`, and non-parameterized `db.query.text` is sanitized to `?`. P0.11's remaining privacy decisions are about BizTrust's own attributes (tenant, actor, business IDs); the convention's only offered mechanisms for identity are `user.hash` and `enduser.pseudo.id`, both at Development stability. [S4, S6, S18, S19, S20]
4. The Collector is the single enforcement point: processors run in the configured order, the `redaction` processor allow-lists attribute keys and masks or hashes matching values, and fan-out delivers a copy of each record to every exporter. That makes one redaction policy for logs, traces and metrics feasible before data leaves the boundary, but the redaction processor is Beta for traces and Alpha for logs and metrics, so P0.11 should treat it as defence in depth behind application-side scrubbing, not as the only control. [S16, S17, S23, S24]
5. Database-side evidence is independent but not sufficient: PostgreSQL's `log_line_prefix` and pgAudit give user, database, transaction, session and object-level facts the application cannot forge, but pgAudit is "best-effort and not transactional", cannot reliably audit superusers, and writes into the ordinary server log. It corroborates a P0.10 audit record; it cannot replace one. [S27, S28]

## 10. Unverified items

- ISO/IEC 27001:2022 Annex A control text (A.8.15 Logging, A.8.16 Monitoring activities, A.8.17 Clock synchronization). `https://www.iso.org/standard/27001` and `https://www.iso.org/standard/82875.html` both returned HTTP 403 on 2026-09-05 and the standard's text is paywalled. Nothing in this note relies on ISO wording; if P0.10 needs to cite ISO, a licensed copy must be read by a human. UNVERIFIED.
- NIST SP 800-92 Rev. 1, "Cybersecurity Log Management Planning Guide", is an Initial Public Draft dated 2023-10-11 (`https://csrc.nist.gov/pubs/sp/800/92/r1/ipd`). It is a draft and is not cited as authority here; the 2006 final SP 800-92 is used. Whether Rev. 1 has since been finalized was not verified.
- The OpenTelemetry Collector "deployment patterns" pages (`/docs/collector/deployment/`, `/agent/`, `/gateway/`) returned HTTP 404 on 2026-09-05. Agent and gateway roles are cited from the Collector overview and architecture pages instead. Statements about tail-based sampling as a gateway motive are therefore NOT made here. UNVERIFIED as a separate page.
- NIST SP 800-53 Rev. 5 control text was read from NIST's own OSCAL catalog (release 5.2.0, last modified 2026-05-11) rather than the PDF. The PDF at `https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf` was not opened; any difference between the 2020 PDF and the 5.2.0 catalog wording is unverified.
- The SP 800-92 PDF was read by text extraction; section numbers quoted (3.1, 5.1.3, footnotes 23 and 24) are as they appear in the extracted text and were not checked against a rendered page.
- Any mapping of BizTrust field names (columns 14 to 22 of section 8) to a schema is a design proposal for #143 and #146, not a sourced fact.

## 11. Sources

All checked 2026-09-05.

| Ref | Source | URL |
|---|---|---|
| S1 | W3C, Trace Context, W3C Recommendation 23 November 2021 | https://www.w3.org/TR/trace-context/ |
| S2 | OpenTelemetry specification, Propagators API | https://opentelemetry.io/docs/specs/otel/context/api-propagators/ |
| S3 | OpenTelemetry specification, Tracing API (SpanContext, SpanKind, Status) | https://opentelemetry.io/docs/specs/otel/trace/api/ |
| S4 | OpenTelemetry semantic conventions, Semantic conventions for HTTP spans | https://opentelemetry.io/docs/specs/semconv/http/http-spans/ |
| S5 | OpenTelemetry semantic conventions, Semantic conventions for HTTP metrics | https://opentelemetry.io/docs/specs/semconv/http/http-metrics/ |
| S6 | OpenTelemetry semantic conventions, Semantic conventions for database client spans | https://opentelemetry.io/docs/specs/semconv/database/database-spans/ |
| S7 | OpenTelemetry semantic conventions, Attribute requirement levels | https://opentelemetry.io/docs/specs/semconv/general/attribute-requirement-level/ |
| S8 | OpenTelemetry semantic conventions, Service entity | https://opentelemetry.io/docs/specs/semconv/registry/entities/service/ |
| S9 | OpenTelemetry semantic conventions, Deployment entity | https://opentelemetry.io/docs/specs/semconv/registry/entities/deployment/ |
| S10 | OpenTelemetry specification, Resource SDK | https://opentelemetry.io/docs/specs/otel/resource/sdk/ |
| S11 | OpenTelemetry specification, Logs overview | https://opentelemetry.io/docs/specs/otel/logs/ |
| S12 | OpenTelemetry specification, Logs data model | https://opentelemetry.io/docs/specs/otel/logs/data-model/ |
| S13 | OpenTelemetry semantic conventions, General logs attributes | https://opentelemetry.io/docs/specs/semconv/general/logs/ |
| S14 | OpenTelemetry specification, Metrics data model (Exemplars) | https://opentelemetry.io/docs/specs/otel/metrics/data-model/ |
| S15 | OpenTelemetry Collector overview | https://opentelemetry.io/docs/collector/ |
| S16 | OpenTelemetry Collector configuration | https://opentelemetry.io/docs/collector/configuration/ |
| S17 | OpenTelemetry Collector architecture | https://opentelemetry.io/docs/collector/architecture/ |
| S18 | OpenTelemetry semantic conventions, URL attributes registry (sensitive information notes) | https://opentelemetry.io/docs/specs/semconv/registry/attributes/url/ |
| S19 | OpenTelemetry semantic conventions, End user attributes registry | https://opentelemetry.io/docs/specs/semconv/registry/attributes/enduser/ |
| S20 | OpenTelemetry semantic conventions, User attributes registry | https://opentelemetry.io/docs/specs/semconv/registry/attributes/user/ |
| S21 | OpenTelemetry specification, Baggage API | https://opentelemetry.io/docs/specs/otel/baggage/api/ |
| S22 | OpenTelemetry specification, Common (Attribute, attribute limits) | https://opentelemetry.io/docs/specs/otel/common/ |
| S23 | OpenTelemetry, Collector configuration security best practices | https://opentelemetry.io/docs/security/config-best-practices/ |
| S24 | OpenTelemetry Collector Contrib, Redaction processor README | https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/redactionprocessor/README.md |
| S25 | NIST SP 800-92, Guide to Computer Security Log Management (September 2006) | https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf (landing page https://csrc.nist.gov/pubs/sp/800/92/final) |
| S26 | NIST SP 800-53 Rev. 5, Security and Privacy Controls for Information Systems and Organizations, controls AU-2, AU-3, AU-8, AU-9, AU-10, AU-11, AU-12, read from NIST's OSCAL catalog release 5.2.0 | https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final ; https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json |
| S27 | PostgreSQL documentation, Error Reporting and Logging (`log_destination`, `log_line_prefix`, `log_statement`) | https://www.postgresql.org/docs/current/runtime-config-logging.html |
| S28 | pgAudit, PostgreSQL Audit Extension README | https://github.com/pgaudit/pgaudit/blob/main/README.md |
| Repo | BizTrust `BIZTRUST-ARCH-001.md` section 15, Audit and observability (read only) | `docs/architecture/BIZTRUST-ARCH-001.md` |
