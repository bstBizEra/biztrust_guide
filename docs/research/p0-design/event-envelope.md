# CloudEvents and AsyncAPI 3 for the event envelope

| Field | Value |
|---|---|
| Ticket | [#134](https://github.com/bstBizEra/biztrust_guide/issues/134) (child of #128, blocks #145) |
| Work package | `BIZTRUST-GUIDE-WP-ARCH-001A` |
| Date checked | `2026-09-05` |
| Sources | Primary only: `github.com/cloudevents/spec` (`main`, marked `1.0.3-wip`; latest tag `ce@v1.0.2`), `cloudevents.io`, `asyncapi.com` specification and tooling pages, `github.com/asyncapi/{parser-js,cli,bindings,studio}`, `docs.nats.io`. Anything else is marked UNVERIFIED. |
| Status | Research only. Nothing here freezes a decision; P0.9 owns the choice. |

## Ticket

Issue [#134](https://github.com/bstBizEra/biztrust_guide/issues/134), "Research: CloudEvents and AsyncAPI 3 for the event envelope". Repository vocabulary comes from `docs/architecture/BIZTRUST-ARCH-001.md` section 12 (event and workflow contract: the minimum event metadata list, at-least-once delivery, consumer deduplication by stable event identity) and `docs/architecture/FLOWS.md` section 15 (transactional outbox, consumer inbox, "not a guarantee of exactly-once execution").

## Question

P0.9 requires a linted AsyncAPI document and a CloudEvents-compatible envelope. From the CloudEvents specification (core, JSON format, HTTP and Kafka bindings, documented extensions) and the AsyncAPI 3 specification with its official tooling: which envelope attributes are required and optional; how `tenant_id`, `authority_reference` and provenance could ride as extension attributes; what the official linters actually check; which brokers have first-party bindings; and what AsyncAPI 3 changed from 2.

## CloudEvents attribute table

Core specification, `cloudevents/spec.md` on `main` (S1). The current released version is `ce@v1.0.2` (S9); `main` carries `1.0.3-wip`. Producers "MUST use a value of `1.0`" for `specversion` when referring to this version of the specification (S1).

| Attribute | Required or optional | Type | Constraint (quoted or paraphrased from S1) | Source |
|---|---|---|---|---|
| `id` | REQUIRED | String | "MUST be a non-empty string"; "MUST be unique within the scope of the producer" (producer + `source`) | S1 |
| `source` | REQUIRED | URI-reference | "MUST be a non-empty URI-reference"; "An absolute URI is RECOMMENDED" | S1 |
| `specversion` | REQUIRED | String | "MUST be a non-empty string"; value `1.0` for this version | S1 |
| `type` | REQUIRED | String | "MUST be a non-empty string"; "SHOULD be prefixed with a reverse-DNS name" | S1 |
| `datacontenttype` | OPTIONAL | String (RFC 2046) | "If present, MUST adhere to the format specified in RFC 2046"; in JSON format, absence implies `data` is JSON conforming to `application/json` | S1, S2 |
| `dataschema` | OPTIONAL | URI | "If present, MUST be a non-empty URI" | S1 |
| `subject` | OPTIONAL | String | "If present, MUST be a non-empty string"; intended for "a simple and efficient string-suffix filter" when middleware cannot read `data` | S1 |
| `time` | OPTIONAL | Timestamp | "If present, MUST adhere to the format specified in RFC 3339"; "Timestamp of when the occurrence happened"; if unknown, "all producers for the same `source` MUST be consistent" | S1 |
| `data` | OPTIONAL (not a context attribute) | any, per `datacontenttype` | The name `data` is reserved and "MUST NOT" be used as an attribute name; in JSON format `data` and `data_base64` are "mutually exclusive" | S1, S2 |

Rules that apply to every attribute name, core or extension (S1):

- "MUST consist of lower-case letters [a-z] or digits [0-9] from the ASCII character set";
- "SHOULD start with a letter";
- "MUST be at least one character in length, and SHOULD NOT exceed 20 characters";
- "SHOULD be descriptive and terse";
- the name `data` is reserved.

Underscores are therefore not permitted. Every ARCH-001 field name (`event_id`, `tenant_id`, `correlation_id`, `authority_reference`) has to be renamed at the envelope boundary.

Type system (S1): Boolean, Integer (32-bit signed range), String, Binary, URI, URI-reference, Timestamp. The JSON format maps these to JSON boolean, number, string, Base64 string, string, string, RFC 3339 string; "OPTIONAL not omitted attributes MAY be represented as a `null` JSON value" (S2). Size (S1): "Intermediaries MUST forward events of a size of 64 KiB or less"; "Consumers SHOULD accept events of a size of at least 64 KiB". The primer adds that binary-mode HTTP servers reject large header blocks, "with limits as low as 8 KiB" (S8).

## How tenant, authority and provenance could ride as extension attributes

### What the specification allows and forbids

From the core specification's "Extension Context Attributes" section (S1):

- A CloudEvent MAY carry any number of extension attributes; they "MUST follow the same naming convention and use the same type system as standard attributes".
- Extensions "have no defined meaning in this specification"; they let external systems attach metadata, "much like HTTP custom headers".
- Extensions "are always serialized according to binding rules like standard attributes". An extension MAY also copy its value elsewhere in a message for non-CloudEvents systems, but then "SHOULD specify how receivers are to interpret messages if the copied values differ".
- JSON format: "Extensions MUST be serialized as a top-level JSON property" (S2). HTTP binary mode: every attribute, extensions included, becomes a `ce-` header (S3). Kafka binary mode: `ce_` header (S4). NATS: `ce-` header (S14). AMQP: `cloudEvents_` or `cloudEvents:` application property (S15). MQTT 5: user property with the attribute name unchanged (S16).
- Privacy (S1): "Sensitive information SHOULD NOT be carried or represented in context attributes" because producers and intermediaries may introspect them; domain data "SHOULD be encrypted" by agreement; "Protocol level security SHOULD be employed".
- The primer's placement rule (S8): extensions are "additional metadata that needs to be included to help ensure proper routing and processing"; metadata "not needed in the transportation or processing of the CloudEvent, should instead be placed within the proper extensibility points of the event (`data`) itself"; extensions "should be kept minimal".
- Documented extensions carry a warning (S7): "The attributes defined in this document have no official standing and might be changed, or removed, at any time." Implementations "are not mandated to limit their use of extension attributes to just the ones specified in this document."
- What the specification does not say: it does not define how a consumer must treat an extension it does not recognise beyond the JSON type mapping (string, number, boolean; `null` = unset) (S2). Treat "consumers ignore unknown extensions" as convention, not a quoted rule.

### Mapping ARCH-001 section 12 to CloudEvents

| ARCH-001 field | CloudEvents carrier | Basis | Note |
|---|---|---|---|
| `event_id` | core `id` | S1 | Unique per `source`; the FLOWS §15 inbox key. |
| `event_type` | core `type` | S1 | Reverse-DNS prefix recommended, e.g. `io.biztrust.policy.bound`. |
| `event_version` | no core attribute | S1 | Options: version suffix inside `type`, or a versioned `dataschema` URI, or a custom extension (name must be e.g. `eventversion`). The spec does not prescribe one. |
| `occurred_at` | core `time` | S1 | Occurrence time, not recording time. |
| `recorded_at` | extension `recordedtime` (Timestamp) | S12 | "when the CloudEvent was created by a producer"; "SHOULD be equal to or later than the occurrence time". Gives the bitemporal pair ARCH-001 asks for. |
| `effective_at_or_period` | none documented | S7 | No documented extension for valid-time. Candidate custom extension (`effectivetime`, Timestamp) or place in `data`. Per the primer, only promote it if routing or processing needs it (S8). |
| `tenant_id` | custom extension, e.g. `tenantid` (String) | S1, S7 | No documented tenant extension. Allowed as a custom extension. Carry an opaque identifier only (S1 privacy rule); it is a routing and isolation key, which is the primer's stated purpose for extensions. |
| `subject_type`, `subject_id` | core `subject` (String) | S1 | One string; a `type/id` convention supports the suffix filter the spec describes. A separate `subjecttype` extension is possible but undocumented. |
| `correlation_id` | extension `correlationid` (String, OPTIONAL, non-empty) | S11 | "An identifier that groups related events within the same logical flow or business transaction." |
| `causation_id` | extension `causationid` (String, OPTIONAL, non-empty) | S11 | "The unique identifier of the event that directly caused this event to be generated." |
| `traceparent` | extension `traceparent` (String, REQUIRED when used) and `tracestate` (String, OPTIONAL) | S5 | W3C Trace Context values. Multi-hop rule: it "MUST carry the trace information of the starting trace of the transmission" and "MUST NOT carry trace information of each individual hop". This is the ARCH-001 causation trace, not the transport hop trace. |
| `producer` | core `source` (URI-reference) | S1 | Absolute URI recommended, e.g. `urn:biztrust:module:policy`. |
| `authority_reference` | no documented match | S10, S7 | The `authcontext` extension carries the *principal* that triggered the occurrence: `authtype` (REQUIRED enum: `app_user`, `user`, `service_account`, `api_key`, `system`, `unauthenticated`, `unknown`), `authid` (OPTIONAL, avoid PII), `authclaims` (OPTIONAL JSON string, "MUST NOT contain actual credentials sufficient for the Consumer to impersonate the principal directly"). Delegated or external authority (a binding authority, an insurer mandate) is a different concept; it would be a custom extension (e.g. `authorityref`, URI-reference) or live in `data`. |
| provenance | `source`, `recordedtime`, `sequence`, `dssematerial` | S1, S12, S13, S17 | `sequence` (String, REQUIRED when used): relative order within `source`, "MUST be a non-empty lexicographically-orderable string", recommended monotonic and contiguous. `dssematerial` (verifiability extension, Binary): a DSSE envelope over the core attributes and named extensions, so a consumer can "cryptographically verify the authenticity and the integrity" without trusting intermediaries; status is a v0.1 draft. |
| ordering key | extension `partitionkey` (String, REQUIRED when used) | S6, S4 | Kafka binding: implementations SHOULD map `partitionkey` to the record key when present; "A mapping function MUST NOT modify the CloudEvent", so the attribute stays in the event. May change or be removed across multiple hops (S6). |
| data classification | extension `dataclassification` (REQUIRED when used), `dataregulation`, `datacategory` | S18 | Useful for the ARCH-001 sensitive-field redaction requirements; no official standing. |
| `data` | `data` | S1, S2 | With `datacontenttype` and a versioned `dataschema`. |

Observed constraint: with the extensions above the envelope carries roughly fifteen context attributes. In HTTP or Kafka binary mode each becomes a header; keep values short (identifiers, not documents) to stay well under the 8 KiB header limits the primer warns about (S8).

## AsyncAPI 3 versus 2

Sources: the 3.0.0 specification (S19), the official migration guide (S20) and the 3.0.0 release notes dated 5 December 2023 (S21).

| Change | AsyncAPI 2.x | AsyncAPI 3.0.0 | Source |
|---|---|---|---|
| Structure | Channel contained its operations and messages | "The decoupling of operations, channels, and messages is the most significant breaking change in v3." Root `channels` and root `operations` are separate; operations reference channels. | S20, S21 |
| Direction | `publish` / `subscribe` (widely misread) | `action: send` or `action: receive`, "your application either sends or receives something" | S20, S21 |
| Channel identity | Key was the topic path | Key is an arbitrary ID; the topic lives in the Channel Object's `address` | S19, S20 |
| Messages | One message (or `oneOf`) per operation; `messageId` field | `channel.messages` is a map; "the ID of the Message Object itself" is the key, so `messageId` is gone | S20, S21 |
| Request/reply | Not modelled | Operation `reply` with Operation Reply Object (`address`, `channel`, `messages`) and Operation Reply Address Object (`location` runtime expression) | S19, S21 |
| Server | Single `url` | `host` (required), `protocol` (required), `pathname`, `protocolVersion` | S19, S20 |
| Schema format | `schemaFormat` beside `payload` | Multi Format Schema Object: `schemaFormat` + `schema`; default format `application/vnd.aai.asyncapi+json;version=3.0.0`; JSON Schema draft-07 MUST be supported; Avro 1.9.0, OpenAPI 3.0.0, RAML 1.0, Protobuf RECOMMENDED | S19, S20 |
| References | Implicit by name for security and servers | "All such references MUST be explicit" (`$ref`) | S20, S21 |
| Security | `security` object on server | Array; scopes moved into Security Scheme Objects | S20 |
| Traits | Trait properties override the target (merge-patch) | "A property on a trait MUST NOT override the same property on the target object" | S20, S21 |
| Root object | `tags`, `externalDocs` at root | Moved to Info Object; `title`, `summary`, `externalDocs` added to Server, Channel and Operation | S21 |
| Channels | Required | Optional; a components-only document is valid | S20, S21 |
| Parameters | Schema-like | Restricted to `enum`, `default`, `description`, `examples`, `location` | S21 |
| Components | Schemas, messages, etc. | Also replies, reply addresses, tags, external docs, operations, channels | S21 |

Fields that matter for the envelope (S19): the Message Object has `headers` ("Schema definition of the application headers. Schema MUST be a map of key-value pairs. It MUST NOT define the protocol headers."), `payload`, `correlationId` (Correlation ID Object with a `location` runtime expression such as `$message.header#/correlationId`), `contentType` (defaults to root `defaultContentType`), `name`, `title`, `examples`, `bindings`, `traits`. The specification does not say whether CloudEvents binary-mode headers (`ce-*`, `ce_*`) count as "application" or "protocol" headers; that is an interpretation P0.9 has to make.

## What the official linters check

Official tooling per `asyncapi.com/tools` (S22): AsyncAPI CLI, AsyncAPI Studio, Parser (JavaScript), Parser (Go). Spectral is listed there as a third-party linter "with baked in support for ... AsyncAPI v2.x"; its native AsyncAPI 3 support is UNVERIFIED here.

### Parser-JS (the engine behind the CLI and Studio)

Parser-JS 3.x supports AsyncAPI 2.x and 3.x; 1.x is unsupported (S23). `validate()` "Returns array of all possible errors against the validation conditions." Validation runs on Spectral with three ruleset groups (S23):

- Core: "Basic and global validation. Apply to all AsyncAPI Spec versions (with some exceptions)."
- Recommended: "These are good practices. They won't create validation errors but warnings."
- Version-specific rulesets for 2.x and 3.x.

Rules can be turned off by name through the `ruleset` option, e.g. `"asyncapi-defaultContentType": "off"` (S23).

Rule inventory read from the ruleset sources on `master` (S24, S25):

| Rule | Severity | What it checks |
|---|---|---|
| `asyncapi-is-asyncapi` | error | "The input must be a document with a supported version of AsyncAPI." |
| `asyncapi-document-resolved` | error | Resolved document validates against the specification JSON Schema. |
| `asyncapi-document-unresolved` | error | Unresolved document validates against the specification JSON Schema. |
| `asyncapi-latest-version` | info | Document uses the latest specification version. |
| `asyncapi-internal` | (internal) | Parser plumbing, not a user rule. |
| `asyncapi-id` | recommended (warning) | Document should have `id`. |
| `asyncapi-defaultContentType` | recommended (warning) | Document should have `defaultContentType`. |
| `asyncapi-info-description`, `-info-contact`, `-info-contact-properties`, `-info-license`, `-info-license-url` | recommended (`license-url` off by default) | Info completeness. |
| `asyncapi-servers` | recommended (warning) | Non-empty `servers`. |
| `asyncapi-unused-component` | info | Component defined but never referenced. |
| `asyncapi3-operation-messages-from-referred-channel` | error | "Operation 'messages' must be a subset of the messages defined in the channel referenced in this operation." |
| `asyncapi3-required-operation-channel-unambiguity` | error | Root operation's `channel` must reference a root channel. |
| `asyncapi3-required-channel-servers-unambiguity` | error | Root channel's `servers` must be a subset of root servers. |
| `asyncapi3-channel-servers` | error | Channel servers must exist in `servers`. |
| `asyncapi3-channel-no-query-nor-fragment` | error | Channel `address` must not contain `?` or `#`. |
| `asyncapi3-channel-parameters` | error | Channel parameters defined, none redundant. |

Observed gap: the v2 ruleset includes `asyncapi2-message-examples` (examples validated against `payload` and `headers` schemas), `asyncapi2-schema-default`, `asyncapi2-schema-examples`, `asyncapi2-operation-operationId-uniqueness` and `asyncapi2-unused-securityScheme` (S26). The v3 core ruleset file read on 2026-09-05 lists only the six rules above; whether v3 example validation exists elsewhere in the code base is UNVERIFIED. Nothing in any ruleset knows about CloudEvents: the linters do not check that a payload or header schema is a valid CloudEvents envelope. That needs a second gate, for example validating examples against the JSON Schema the CloudEvents JSON format references (`cloudevents.json`, S2).

### CLI

`asyncapi validate [SPEC-FILE]` (S27): flags `--diagnostics-format` (`json|stylish|junit|html|text|teamcity|pretty|github-actions|sarif|code-climate|gitlab|markdown`, default `stylish`), `--fail-severity` (`error|warn|info|hint`, default `error`, "diagnostics of this level or above will trigger a failure exit code"), `--score`, `--suppressWarnings`, `--suppressAllWarnings`, `--watch`, `--save-output`. No custom-ruleset flag appears in the documented usage; custom Spectral rules are a parser-level option (S23). Related commands: `convert` (older versions to newer, or OpenAPI to AsyncAPI), `bundle`, `diff`, `optimize`, `format`, `new`, `start studio`, `start preview` (S27). Install: `npm install -g @asyncapi/cli` (S28).

### Studio

Browser editor with "Real-time validation across all files", import from URL, Markdown preview, Avro and JSON Schema support (S29). It uses the same parser, so it checks what Parser-JS checks.

## Broker bindings with first-party support

"First-party" below means a binding document maintained in the CloudEvents specification repository, in the AsyncAPI bindings repository, or in the broker vendor's own documentation. Date checked 2026-09-05.

### CloudEvents protocol bindings (`cloudevents/spec`)

| Protocol | Attribute carrier in binary mode | Notable rule | Source |
|---|---|---|---|
| HTTP | `ce-<name>` headers; structured mode `application/cloudevents+json`; batched `application/cloudevents-batch+json` | "Every compliant implementation SHOULD support both structured and binary modes"; "The batched mode MUST NOT be used unless solicited"; mode detected from `Content-Type` | S3 |
| Kafka | `ce_<name>` headers; `content-type` header unprefixed | Both modes need Kafka 0.11.0.0+ (older: structured only); SHOULD map `partitionkey` to the record key; "A mapping function MUST NOT modify the CloudEvent" | S4 |
| NATS | `ce-<name>` headers | Binary mode needs NATS 2.2+; "If the server is a version earlier than NATS 2.2, the content mode is always structured"; JetStream not mentioned | S14 |
| AMQP 1.0 | application properties `cloudEvents_<name>` or `cloudEvents:<name>` | Underscore "SHOULD be preferred" for JMS 2.0 compatibility; no batch mode | S15 |
| MQTT | user properties, names unchanged | "The binary mode only applies to MQTT 5.0"; MQTT 3.1.1 is structured JSON only | S16 |
| WebSockets, XMPP | listed in the repository | Not read for this ticket | S30 |

SDK rule (S30): "Each SDK MUST support structured-mode messages for each transport that it supports" and "SHOULD support binary-mode"; HTTP in both modes is mandatory for every official SDK (C#, Go, Java, Kotlin, JavaScript, PHP, PowerShell, Python, Ruby, Rust). Kafka, AMQP, MQTT and NATS support is per SDK and UNVERIFIED here.

### AsyncAPI protocol bindings (`asyncapi/bindings`)

Bindings present in the repository index (S31): AMQP, AMQP 1.0, Anypoint MQ, Google Cloud Pub/Sub, HTTP, IBM MQ, JMS, Kafka, Mercure, MQTT, MQTT5, NATS, Pulsar, Redis, ROS 2, SNS, Solace, SQS, STOMP, WebSockets. The 3.0.0 specification's bindings objects list the same names minus ROS 2 (S19). Details read for the candidates in ARCH-001:

| Binding | Version | Server | Channel | Operation | Message | Source |
|---|---|---|---|---|---|---|
| Kafka | 0.5.0 | `schemaRegistryUrl`, `schemaRegistryVendor` | `topic`, `partitions`, `replicas`, `topicConfiguration` | `groupId`, `clientId` | `key`, `schemaIdLocation`, `schemaIdPayloadEncoding`, `schemaLookupStrategy` | S32 |
| NATS | 0.1.0 | reserved, "MUST NOT contain any properties" | reserved | `queue` (max 255 chars) | reserved | S33 |
| HTTP | 0.3.0 | reserved | reserved | `method`, `query` | `headers`, `statusCode` (reply only) | S34 |
| AMQP 0-9-1 | 0.3.0 | none | `is` (`queue` or `routingKey`), `exchange`, `queue` | `expiration`, `userId`, `cc`, `priority`, `deliveryMode`, `timestamp`, `ack` | `contentEncoding`, `messageType` | S35 |
| Pulsar | 0.1.0 | `tenant` | `namespace`, `persistence`, `compaction`, `geo-replication`, `retention`, `ttl`, `deduplication` | reserved | reserved | S36 |

Observed: the NATS binding has no JetStream fields (stream, consumer, deduplication window); the Pulsar binding is the only one read that exposes a `deduplication` switch and a `tenant` at server level.

### Broker's own documentation

- NATS (S37): "Every current server and client supports headers"; "Keep the `Nats-` prefix out of your own keys, though, since NATS reserves it for system headers". So `ce-` headers are permitted and do not collide.
- NATS JetStream (S38, S39): "Tag the publish with a `Nats-Msg-Id` header. The server refuses to store the same ID twice within the stream's duplicate-tracking window." The window "is a stream setting, not a header: it's the `Duplicate Window`", default two minutes; retries after it expires create duplicates. Optimistic-concurrency headers: `Nats-Expected-Stream`, `Nats-Expected-Last-Sequence`, `Nats-Expected-Last-Subject-Sequence`, `Nats-Expected-Last-Msg-Id`; also `Nats-Rollup`, `Nats-TTL`.
- Apache Kafka: the record-header format could not be read from kafka.apache.org with the tooling used (the page returned a navigation shell). The CloudEvents Kafka binding's statement that headers exist from 0.11.0.0 (S4) is the only sourced claim; Kafka's own wording is UNVERIFIED.
- Temporal: ARCH-001 names it as a workflow candidate, not a transport; no Temporal binding exists in either specification repository (S30, S31), and Temporal's own documentation was not consulted for this ticket.

## Decision-relevant facts for P0.9

1. Attribute names are `[a-z0-9]` only, should not exceed 20 characters, and `data` is reserved (S1). ARCH-001's snake_case metadata names cannot be attribute names; P0.9 needs a documented rename at the envelope boundary (`tenant_id` to `tenantid`, `correlation_id` to `correlationid`, and so on), and the JSON format places every extension at the top level of the envelope, not inside `data` (S2).
2. Documented extensions already cover most of ARCH-001 section 12: `correlationid`, `causationid` (S11), `traceparent`/`tracestate` (S5), `recordedtime` (S12), `sequence` (S13), `partitionkey` (S6), `authtype`/`authid`/`authclaims` (S10), `dataclassification` (S18), `dssematerial` (S17). None has "official standing" and any "might be changed, or removed, at any time" (S7). Tenant, event version, effective time and delegated-authority reference have no documented extension; the specification allows custom ones (S7), so P0.9 must define and version them itself.
3. Context attributes are inspectable by intermediaries: "Sensitive information SHOULD NOT be carried or represented in context attributes" (S1), events over 64 KiB need not be forwarded (S1), and binary-mode headers can hit 8 KiB limits (S8). Tenant and authority extensions should be opaque identifiers; documents, claims and personal data belong in `data`, encrypted or referenced.
4. AsyncAPI 3 is the version to lint against: send/receive operations, decoupled channels, request/reply and the Multi Format Schema Object are 3.0.0 features (S19-S21), Parser-JS 3.x is the official validator for both 2.x and 3.x (S23), and `asyncapi validate --fail-severity error --diagnostics-format sarif` (or `github-actions`) is the CI gate (S27). The official rules validate document structure, references and channel/operation consistency (S24, S25); they do not validate CloudEvents conformance, so P0.9 needs a second gate against the CloudEvents JSON Schema (S2).
5. Kafka is the only broker among the ARCH-001 candidates with both a CloudEvents binding that carries the envelope in headers and maps `partitionkey` to the record key (S4) and an AsyncAPI binding with message `key` and schema-registry fields (S32). NATS has a CloudEvents binding (S14) but its AsyncAPI binding exposes only `queue` and nothing for JetStream (S33); JetStream deduplication is by `Nats-Msg-Id` inside a stream-configured window defaulting to two minutes (S38, S39), which does not replace the FLOWS §15 consumer inbox. Setting `Nats-Msg-Id` equal to the CloudEvents `id` is a natural pairing but is this document's inference, not a rule in either specification.

## Unverified items

- Kafka's own record-header documentation (header key/value format, message format v2) could not be fetched; only the CloudEvents binding statement is sourced.
- Whether Spectral's own bundled AsyncAPI ruleset supports 3.x; `asyncapi.com/tools` describes it as "AsyncAPI v2.x" support.
- Whether Parser-JS validates message examples against `payload`/`headers` schemas for 3.x documents; the v3 core ruleset file read lists six rules and no example rule.
- Per-SDK support for Kafka, NATS, AMQP and MQTT bindings in the official CloudEvents SDKs.
- Differences between `ce@v1.0.2` (tagged) and `main` (`1.0.3-wip`); the attribute table was read from `main`.
- The CloudEvents WebSockets and XMPP bindings, and the AsyncAPI MQTT, MQTT5, Google Pub/Sub, SNS/SQS, Solace, IBM MQ, JMS, Redis, STOMP, Mercure, Anypoint MQ, ROS 2 and WebSockets bindings were listed but not read.
- Whether AsyncAPI's "MUST NOT define the protocol headers" excludes CloudEvents binary-mode headers from `message.headers`; the specification text does not address CloudEvents.
- Temporal documentation was not consulted.

## Sources

All checked 2026-09-05.

- S1. CloudEvents core specification, `main`: https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md
- S2. CloudEvents JSON event format: https://github.com/cloudevents/spec/blob/main/cloudevents/formats/json-format.md
- S3. CloudEvents HTTP protocol binding: https://github.com/cloudevents/spec/blob/main/cloudevents/bindings/http-protocol-binding.md
- S4. CloudEvents Kafka protocol binding: https://github.com/cloudevents/spec/blob/main/cloudevents/bindings/kafka-protocol-binding.md
- S5. Distributed tracing extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/distributed-tracing.md
- S6. Partitioning extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/partitioning.md
- S7. Extensions README (standing and inclusion criteria): https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/README.md
- S8. CloudEvents primer: https://github.com/cloudevents/spec/blob/main/cloudevents/primer.md
- S9. CloudEvents releases (`ce@v1.0.2`, 2024-02-06): https://github.com/cloudevents/spec/releases
- S10. Auth context extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/authcontext.md
- S11. Correlation extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/correlation.md
- S12. Recorded time extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/recordedtime.md
- S13. Sequence extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/sequence.md
- S14. CloudEvents NATS protocol binding: https://github.com/cloudevents/spec/blob/main/cloudevents/bindings/nats-protocol-binding.md
- S15. CloudEvents AMQP protocol binding: https://github.com/cloudevents/spec/blob/main/cloudevents/bindings/amqp-protocol-binding.md
- S16. CloudEvents MQTT protocol binding: https://github.com/cloudevents/spec/blob/main/cloudevents/bindings/mqtt-protocol-binding.md
- S17. Verifiability extension (DSSE): https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/verifiability.md
- S18. Data classification extension: https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/data-classification.md
- S19. AsyncAPI Specification 3.0.0: https://www.asyncapi.com/docs/reference/specification/v3.0.0
- S20. AsyncAPI migration guide, v2 to v3: https://www.asyncapi.com/docs/migration/migrating-to-v3
- S21. AsyncAPI 3.0.0 release notes: https://www.asyncapi.com/blog/release-notes-3.0.0
- S22. AsyncAPI tools directory: https://www.asyncapi.com/tools
- S23. Parser-JS README: https://github.com/asyncapi/parser-js/blob/master/README.md
- S24. Parser-JS shared ruleset: https://github.com/asyncapi/parser-js/blob/master/packages/parser/src/ruleset/ruleset.ts
- S25. Parser-JS v3 ruleset: https://github.com/asyncapi/parser-js/blob/master/packages/parser/src/ruleset/v3/ruleset.ts
- S26. Parser-JS v2 ruleset: https://github.com/asyncapi/parser-js/blob/master/packages/parser/src/ruleset/v2/ruleset.ts
- S27. AsyncAPI CLI usage: https://github.com/asyncapi/cli/blob/master/docs/usage.md
- S28. AsyncAPI CLI page: https://www.asyncapi.com/tools/cli
- S29. AsyncAPI Studio README: https://github.com/asyncapi/studio/blob/master/README.md
- S30. CloudEvents SDK requirements: https://github.com/cloudevents/spec/blob/main/cloudevents/SDK.md
- S31. AsyncAPI bindings repository: https://github.com/asyncapi/bindings
- S32. AsyncAPI Kafka binding: https://github.com/asyncapi/bindings/blob/master/kafka/README.md
- S33. AsyncAPI NATS binding: https://github.com/asyncapi/bindings/blob/master/nats/README.md
- S34. AsyncAPI HTTP binding: https://github.com/asyncapi/bindings/blob/master/http/README.md
- S35. AsyncAPI AMQP binding: https://github.com/asyncapi/bindings/blob/master/amqp/README.md
- S36. AsyncAPI Pulsar binding: https://github.com/asyncapi/bindings/blob/master/pulsar/README.md
- S37. NATS message headers: https://docs.nats.io/learn/core-nats/headers
- S38. NATS JetStream publishing: https://docs.nats.io/learn/jetstream/publishing
- S39. NATS JetStream API headers: https://docs.nats.io/reference/jetstream/api/headers
- S40. cloudevents.io (CNCF graduated 2024-01-25; SDK list): https://cloudevents.io/
