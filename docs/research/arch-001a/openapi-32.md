# OpenAPI 3.2 status and toolchain readiness

| Field | Value |
|---|---|
| Ticket | [#97 — [ARCH-001A] Research: OpenAPI 3.2 status and toolchain readiness](https://github.com/bstBizEra/biztrust_guide/issues/97) |
| Feeds | ADR-005 (`docs/architecture/ADR_REGISTER.md`, `DRAFT_REQUIRED`); `BIZTRUST-ARCH-001` §11 |
| Date checked | 2026-09-05 (every URL below was read on this date) |
| Baseline | `origin/main` at `e1b20d1` |
| Method | Primary sources only: the OpenAPI Initiative (OAI) specification site and repositories, and each tool's own README, changelog, release notes or documentation. Release dates were taken from the GitHub Releases API, not from rendered pages. A tool without a first-party statement is marked **no first-party statement found**; an open issue or pull request in a tool's own tracker is recorded as evidence of *absence*, never as support. |
| Authority | Advisory only. This file informs ADR-005; it does not decide it. |

## Ticket

Issue [#97](https://github.com/bstBizEra/biztrust_guide/issues/97), raised by the wayfinder charting of 2026-09-05 for `ARCH-001A`.

## Question

ADR-005 proposes OpenAPI 3.2 for contract-first HTTP APIs. From the OAI and tool vendors' official sources: is 3.2 a published specification and since when; what does it add over 3.1; which linters, generators, mock servers and gateways state 3.2 support today; and what would a breaking-change policy rest on (overlays, `x-` extensions, semantic diff tools)? If 3.2 support is thin, what would 3.1 cost instead?

## Status of 3.2

**Published.** OpenAPI Specification v3.2.0 is a released specification. Its Appendix A revision history reads: `3.2.0 | 2025-09-19 | Release of the OpenAPI Specification 3.2.0`, with `3.1.2 | 2025-09-19 | Patch release of the OpenAPI Specification 3.1.2` on the same day and `3.1.1 | 2024-10-24`. [spec.openapis.org/oas/v3.2.0.html](https://spec.openapis.org/oas/v3.2.0.html). The GitHub release `3.2.0` was published `2025-09-19T16:20:24Z` ([release](https://github.com/OAI/OpenAPI-Specification/releases/tag/3.2.0)). `https://spec.openapis.org/oas/latest.html` resolves to "OpenAPI Specification v3.2.0" (HTTP 200, checked 2026-09-05). The OAI announced it on its blog on 2025-09-23 ([Announcing OpenAPI v3.2](https://www.openapis.org/blog/2025/09/23/announcing-openapi-v3-2)).

**Compatibility with 3.1.** The OAI's upgrade guide states: "All existing 3.1 documents will work without modification after updating the version number." ([learn.openapis.org/upgrading/v3.1-to-v3.2.html](https://learn.openapis.org/upgrading/v3.1-to-v3.2.html)). The specification's own versioning rule: "The `major`.`minor` portion of the version string (for example `3.1`) SHALL designate the OAS feature set. `.patch` versions address errors in, or provide clarifications to, this document, not the feature set." and "Tooling which supports OAS 3.1 SHOULD be compatible with all OAS 3.1.* versions." Deprecated fields "are expected to remain part of the OAS until the next major version" ([v3.2.0 §Versions](https://spec.openapis.org/oas/v3.2.0.html)).

**What comes after.** The specification repository carries a `v3.3-dev` branch alongside `v3.2-dev` ([branches](https://github.com/OAI/OpenAPI-Specification/branches)). The Moonwalk SIG "is working on the next major release of the OpenAPI Specification (OAS), version 4.0"; it states there is "no planned end date to 4.0", "we strongly recommend using the 3.x versions that exist today", and lists "Mechanical Upgrading: An automated upgrade process from 3.x to 4.0" as a principle ([github.com/OAI/sig-moonwalk](https://github.com/OAI/sig-moonwalk)).

### What 3.2 adds over 3.1

All items below are quoted or paraphrased from the OAI's 3.2.0 release note ([releases/tag/3.2.0](https://github.com/OAI/OpenAPI-Specification/releases/tag/3.2.0)) and the announcement ([blog](https://www.openapis.org/blog/2025/09/23/announcing-openapi-v3-2)).

| Area | Addition |
|---|---|
| Tags | Tag Object gains `summary`, `parent` (nesting) and `kind` (classification, e.g. `nav`), with an OAI registry of `kind` values. The upgrade guide frames this as replacing the `x-displayName` / `x-tagGroups` extension pattern. |
| HTTP methods | New `query` operation "alongside the existing get/post/put/delete/options/head/patch/trace"; `additionalOperations` map on a Path Item for any other method (e.g. `LINK`). |
| Document identity | Top-level `$self` "to allow users to define the base URI of the document, used to resolve relative references"; more guidance on multi-document descriptions. |
| Streaming | "Support for sequential media types such as `text/event-stream` for server-sent events (SSE) and `multipart/mixed`, `application/jsonl`, `application/json-seq`"; `itemSchema` describes each item; `prefixEncoding` / `itemEncoding` for multipart. |
| Parameters | New `in: querystring` location (whole query string handled via `content`); `allowReserved` permitted on headers and all `in` values; new `style: cookie`. |
| XML | `nodeType` (`element`, `attribute`, `text`, `cdata`, `none`); `attribute: true` and `wrapped: true` deprecated in its favour; `xml` usable in any Schema Object; IRI namespaces. |
| Examples | Example Object gains `dataValue` (structured) and `serializedValue` (wire form); `externalValue` documented as serialized. |
| Security | OAuth2 Device Authorization flow (`deviceAuthorization`, `deviceAuthorizationUrl`); `oauth2MetadataUrl` (RFC 8414); `deprecated` on security schemes; security schemes referenceable by URI. |
| Server Object | `name` field; URLs must not carry query or fragment; ABNF for variable substitution. |
| Polymorphism | Discriminator `propertyName` now optional; new `defaultMapping`. |
| Responses | `description` now optional; new `summary`. |
| Components | New `mediaTypes` map for reusable Media Type Objects. |
| Formal syntax | ABNF for path templating, server variables and runtime expressions. |
| References | JSON Schema draft-bhutton-01 (core and validation), RFC 8259 (JSON), RFC 9110 (HTTP). |
| Editorial | Extensive new material on media types, encoding, percent-encoding, SSE examples and binary data. |

## Tool support table

Versions are the latest GitHub release on 2026-09-05. "Stated" means the vendor's own words; the source column is the page those words were read from. Where a tool has no statement, the nearest first-party evidence (tracker item, dependency) is noted so the reader can see why the cell is empty rather than take it on trust.

| Tool | Version (date) | Stated 3.2 support | Stated 3.1 support | Source URL |
|---|---|---|---|---|
| **Linters** | | | | |
| Spectral (Stoplight) | v6.16.3 (2026-08-03) | **No first-party statement found.** The format detectors define `oas2`, `oas3` (any `openapi` whose major is 3), `oas3_0` (`^3\.0`), `oas3_1` (`^3\.1`) and no `oas3_2`; the `spectral:oas` ruleset attaches rules to those four formats only. Open issue #2910 "Add support for OpenAPI 3.2" (2026-03-12) and open PR #2917 "Add OpenAPI 3.2 format detection and ruleset support" (2026-03-19, last updated 2026-08-08). | Yes: `oas3_1` format ("OpenAPI 3.1.x"); README: "Validate and lint OpenAPI v2 & v3.x". | [formats/src/openapi.ts @ 411b144](https://github.com/stoplightio/spectral/blob/411b144950b85c6c8fa31881e390b66f7263712a/packages/formats/src/openapi.ts); [rulesets/src/oas/index.ts](https://github.com/stoplightio/spectral/blob/develop/packages/rulesets/src/oas/index.ts); [README](https://github.com/stoplightio/spectral/blob/develop/README.md); [#2910](https://github.com/stoplightio/spectral/issues/2910); [#2917](https://github.com/stoplightio/spectral/pull/2917) |
| Redocly CLI | @redocly/cli 2.51.2 (2026-09-04) | **Yes.** README: "Supports OpenAPI 3.2, 3.1, 3.0 and OpenAPI 2.0 (legacy Swagger), AsyncAPI 3.0 and 2.6, Arazzo 1.0." Changelog: 2.3.0 (2025-10-03) "Added basic support for OpenAPI 3.2"; 2.6.0 (2025-10-16) rules `spec-no-invalid-tag-parents`, `spec-example-values`, `spec-discriminator-defaultMapping`, `spec-no-invalid-encoding-combinations`; 2.12.0 (2025-11-25) "OpenAPI 3.2 XML modeling support"; 2.19.0 (2026-02-18) `spec-querystring-parameters`; 2.40.0 (2026-07-21) `dataValue` linting. Blog (2026-03-11): "Redocly fully supports OpenAPI 3.2 - linting, rendering, code samples, mock server, Respect". | Yes (same README line). | [README](https://github.com/Redocly/redocly-cli/blob/main/README.md); [CHANGELOG](https://github.com/Redocly/redocly-cli/blob/main/packages/core/CHANGELOG.md); [blog](https://redocly.com/blog/openapi-3-2) |
| vacuum (quobix / pb33f) | v0.30.3 (2026-09-02) | **Partial statement.** vacuum's own README states no version list; its parser libopenapi states "libopenapi has full support for OpenAPI 3, 3.1 and 3.2". vacuum v0.26.0 (2026-04-17) release note: "Added 3.2 regression test to ensure #805 is closed permanently" (#805: rule `no-ref-siblings` misapplied "on versions 3.1 & 3.2"). Spectral-ruleset compatible: "fully compatible with existing Spectral rulesets". | Via libopenapi (same sentence). | [vacuum README](https://github.com/daveshanley/vacuum/blob/main/README.md); [libopenapi README](https://github.com/pb33f/libopenapi/blob/main/README.md); [v0.26.0](https://github.com/daveshanley/vacuum/releases/tag/v0.26.0); [#805](https://github.com/daveshanley/vacuum/issues/805) |
| **Generators** | | | | |
| openapi-generator (OpenAPITools) | v7.25.0 (2026-08-24) | **No first-party statement found.** README: "OpenAPI Spec compatibility: 1.0, 1.1, 1.2, 2.0, 3.0, 3.1 (beta support)". Open bug #24212 (2026-07-06): "Unrecognized path-item operations (e.g. OpenAPI 3.2 'query') are silently dropped from generated code with --skip-validate-spec". No 3.2 mention in release notes v7.18.0–v7.25.0. | "3.1 (beta support)". | [README](https://github.com/OpenAPITools/openapi-generator/blob/master/README.md); [#24212](https://github.com/OpenAPITools/openapi-generator/issues/24212); [releases](https://github.com/OpenAPITools/openapi-generator/releases) |
| Kiota (Microsoft) | v1.35.0 (2026-09-04) | **Yes.** CHANGELOG 1.30.0 (2026-01-27): "Added support for OpenAPI 3.2.0". Depends on `Microsoft.OpenApi` 3.10.2 (`Directory.Packages.props`). | Yes: 1.24.0 (2025-03-12) "Added support for OpenAPI 3.1". | [CHANGELOG](https://github.com/microsoft/kiota/blob/main/CHANGELOG.md); [v1.30.0](https://github.com/microsoft/kiota/releases/tag/v1.30.0); [Directory.Packages.props](https://github.com/microsoft/kiota/blob/main/Directory.Packages.props) |
| OpenAPI.NET (`Microsoft.OpenApi`) | v3.10.2 (2026-08-20); 2.12.2 and 1.6.31 lines maintained in parallel | **Yes.** v3.0.0 (2025-11-11): "adds support for OpenAPI 3.2.0" (breaking major). Same note: "ASP.net users should remain on version 1.X for ASP.net < 10, and version 2.X for ASP.net 10, this new major version will be implemented in a future version of ASP.net". README: "we just released a new major version of the library, which brings support for OpenAPI 3.2!" | Yes (v2.x line). | [v3.0.0](https://github.com/microsoft/OpenAPI.NET/releases/tag/v3.0.0); [README](https://github.com/microsoft/OpenAPI.NET/blob/main/README.md) |
| Swagger Core (Java, swagger-api) | v2.2.55 (2026-08-31) | **No first-party statement found.** README: "Since version 2.2.0 Swagger Core supports OpenAPI 3.1". Open issue #5181 "[Question]: Support OAS 3.2" (2026-05-19); open PRs #5253 (QUERY method), #5254, #5255 "in preparation for OAS 3.2" (2026-07). | Yes (2.2.0+). | [README](https://github.com/swagger-api/swagger-core/blob/master/README.md); [#5181](https://github.com/swagger-api/swagger-core/issues/5181); [#5253](https://github.com/swagger-api/swagger-core/pull/5253) |
| Swagger Parser (Java, swagger-api) | v2.1.48 (2026-08-31) | **No first-party statement found.** README: "Since version 2.1.0 Swagger Parser supports OpenAPI 3.1". Open issue #2248 "[Feature]: Support for OpenAPI Spec 3.2" (2025-11-13). | Yes (2.1.0+). | [README](https://github.com/swagger-api/swagger-parser/blob/master/README.md); [#2248](https://github.com/swagger-api/swagger-parser/issues/2248) |
| swagger-parser (JS, APIDevTools) | v13.0.0 (2026-09-02) | **No first-party statement found.** README title: "Swagger 2.0 and OpenAPI 3.0 parser/validator". Open PR #286 "Add OpenAPI 3.2 support" (2026-04-21). | Partial: v12.1.0 (2025-10-14) "Add support for version 3.1.2"; README not updated. | [README](https://github.com/APIDevTools/swagger-parser/blob/main/README.md); [v12.1.0](https://github.com/APIDevTools/swagger-parser/releases/tag/v12.1.0); [#286](https://github.com/APIDevTools/swagger-parser/pull/286) |
| **Documentation renderers** | | | | |
| Swagger UI | v5.32.15 (2026-09-04) | **Yes.** README compatibility table: 5.32.0 (2026-02-27) lists "2.0, 3.0.0, 3.0.1, 3.0.2, 3.0.3, 3.0.4, 3.1.0, 3.1.1, 3.1.2, 3.2.0". | Yes since 5.0.0 (2023-06-12). | [README](https://github.com/swagger-api/swagger-ui/blob/master/README.md) |
| Swagger Editor | — | **No first-party statement found.** README: "Only SwaggerEditor@5 supports OpenAPI 3.1.0". | Yes (v5). | [README](https://github.com/swagger-api/swagger-editor/blob/master/README.md) |
| Redoc (renderer) | — | **Mixed.** README feature list: "Support for OpenAPI 3.1, OpenAPI 3.0, and Swagger 2.0"; README banner: "Redoc 3.0 is coming — one renderer for OpenAPI 3.2, AsyncAPI, GraphQL, and MCP". Redocly blog claims "rendering" among supported features (see Redocly CLI row). | Yes. | [README](https://github.com/Redocly/redoc/blob/main/README.md); [blog](https://redocly.com/blog/openapi-3-2) |
| **Mock servers** | | | | |
| Prism (Stoplight) | v5.16.0 (2026-07-17) | **No first-party statement found.** README: "Comprehensive API Specification Support: OpenAPI v3.1, OpenAPI v3.0, OpenAPI v2.0 (formerly Swagger) and Postman Collections." No 3.2 mention in releases v5.15.x–v5.16.0. | Yes. | [README](https://github.com/stoplightio/prism/blob/master/README.md); [releases](https://github.com/stoplightio/prism/releases) |
| Redocly mock server | (part of Redocly CLI 2.51.2) | Claimed in the Redocly blog: "mock server" listed among fully supported features. | Yes. | [blog](https://redocly.com/blog/openapi-3-2) |
| **Diff / breaking-change tools** | | | | |
| oasdiff | v1.30.0 (2026-08-30) | **Yes (reads and diffs).** docs/OPENAPI-31.md: "oasdiff reads 3.2 specs". v1.29.0 (2026-08-16): "Changes to streamed item schemas are now detected" (`itemSchema`, five new change IDs). v1.30.0 (2026-08-30): "Operations under the 3.2 `query` field and `additionalOperations` map were invisible to the diff ... they are now diffed like any other operation"; new validate rules `additional-operations-*`, `query-field-for-3-2-plus`. `oasdiff upgrade` rewrites 3.0 "into the latest 3.x canonical form (currently 3.2.0)". | Yes: "generally available starting with v1.15.0" (2026-04-25); "162 new rule IDs" for 3.1 keywords. | [OPENAPI-31.md](https://github.com/oasdiff/oasdiff/blob/main/docs/OPENAPI-31.md); [v1.29.0](https://github.com/oasdiff/oasdiff/releases/tag/v1.29.0); [v1.30.0](https://github.com/oasdiff/oasdiff/releases/tag/v1.30.0) |
| openapi-diff (OpenAPITools, Java) | 2.1.7 (2026-01-26) | **No.** README: "Supports OpenAPI spec v3.0." | No statement. | [README](https://github.com/OpenAPITools/openapi-diff/blob/master/README.md) |
| Optic | v1.0.9 (2025-08-10) | **No first-party statement found; repository archived** (`archived=true`, last push 2026-01-08). | No statement. | [github.com/opticdev/optic](https://github.com/opticdev/optic) |
| **API gateways** | | | | |
| Kong Gateway — OAS Validation plugin | (docs, current) | **No.** "Swagger v2 and OpenAPI 3.0.x and 3.1.0 specifications" (JSON Schema Draft 2019-09 validator; request/response validation `application/json` only). | Yes (3.1.0). | [developer.konghq.com/plugins/oas-validation/](https://developer.konghq.com/plugins/oas-validation/) |
| Kong decK `openapi2kong` | (docs, current) | **No first-party version statement found** on the command page. | No statement. | [developer.konghq.com/deck/file/openapi2kong/](https://developer.konghq.com/deck/file/openapi2kong/) |
| Kong Konnect API catalog / Dev Portal | (docs, current) | **No.** "Spec should be valid according to the OpenAPI 2.0, 3.0.x, or 3.1.x specification ... OAS validation is performed using Spectral." | Yes (3.1.x). | [developer.konghq.com/api-products/](https://developer.konghq.com/api-products/) |
| Azure API Management | (docs, `ms.date` 2025-09-26) | **No.** "API Management only supports: OpenAPI version 2; OpenAPI version 3.0.x (up to version 3.0.3); OpenAPI version 3.1 (import only)". Custom extensions "Are ignored on import. Aren't saved or preserved for export." | Import only: "OpenAPI 3.1 should be treated as import-compatible only, not feature-compatible. For full fidelity, use OpenAPI 2.0 or 3.0.x." | [api-management-api-import-restrictions](https://learn.microsoft.com/en-us/azure/api-management/api-management-api-import-restrictions) |
| AWS API Gateway (REST APIs) | (docs, current) | **No.** "Currently, API Gateway supports OpenAPI v2.0 and OpenAPI v3.0 definition files"; among exceptions: "The `deprecated` field is not supported", "`securitySchemes` type, if used, must be `apiKey`", "`$ref` cannot be used to reference other files". | **No.** | [api-gateway-import-api](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-import-api.html); [important notes](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-known-issues.html) |
| Google Cloud API Gateway | (docs, current) | **No.** Supports "OpenAPI 2.0 (formerly Swagger)", "OpenAPI 3.0.x", "OpenAPI 3.1.x"; "API Gateway supports all patch versions of 3.0 and 3.1". | Yes (3.1.x). | [api-gateway/docs/openapi-overview](https://docs.cloud.google.com/api-gateway/docs/openapi-overview) |
| **Hosted docs / SDK vendors (for reference)** | | | | |
| Bump.sh | (docs, current) | **Partial.** "We support all major versions from Swagger (OpenAPI v2), OpenAPI v3/3.1, and partially OpenAPI v3.2" — currently the QUERY method, server `name`, tag `summary`, response `summary`, security scheme `deprecated`. | Yes. | [docs.bump.sh openapi-support](https://docs.bump.sh/help/specification-support/openapi-support/) |
| Speakeasy | (docs, current) | **No first-party support statement found** for its generator; its site carries explanatory material on 3.2 only. | — | [speakeasy.com/openapi/release-notes](https://www.speakeasy.com/openapi/release-notes/) |

Summary counts (3.2 stated as supported, in the vendor's own words): Redocly CLI, Kiota, OpenAPI.NET, Swagger UI, oasdiff; partial: vacuum (via libopenapi), Bump.sh; none of the four gateways checked; none of Spectral, Prism, openapi-generator, the Swagger Java stack or the JS swagger-parser.

## Breaking-change policy building blocks

1. **Specification Extensions (`x-`).** OAS 3.2.0: "Allows extensions to the OpenAPI Schema. The field name MUST begin with `x-`, for example, `x-internal-id`. Field names beginning `x-oai-` and `x-oas-` are reserved for uses defined by the OpenAPI Initiative. The value can be any valid JSON value." The OAI "maintains several extension registries, including registries for individual extension keywords and extension keyword namespaces", and "Extensions are one of the best ways to prove the viability of proposed additions to the specification." ([v3.2.0 §Specification Extensions](https://spec.openapis.org/oas/v3.2.0.html#specification-extensions)). Two consequences for a policy: extensions are legitimate carriers for project metadata (stability tier, sunset date, authority class), and gateways may strip them — Azure APIM: custom extensions "Are ignored on import. Aren't saved or preserved for export." ([source](https://learn.microsoft.com/en-us/azure/api-management/api-management-api-import-restrictions)).

2. **Native deprecation markers.** 3.2 carries `deprecated` on operations, parameters and now security schemes ("indicating that the scheme may still be supported, but that it should not be used") ([release note](https://github.com/OAI/OpenAPI-Specification/releases/tag/3.2.0)). AWS API Gateway drops `deprecated` on import ([source](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-known-issues.html)), so deprecation must also be enforced outside the gateway.

3. **Overlay Specification (OAI).** Overlay 1.0.0 published 2024-10-17; 1.1.0 published 2026-01-16 (GitHub release `1.1.0`, `2026-01-16T12:59:30Z`; spec page dated 14 January 2026). 1.1.0 adds a `copy` action, an info `description`, "Better update/delete capabilities for primitive values", "RFC9535 compliance", and a file naming convention. `target` is "a RFC9535 JSONPath query expression selecting nodes in the target document"; `update` merges into objects / appends to arrays / replaces primitives; `remove` is "a boolean value that indicates that each of the target nodes MUST be removed". ([overlay/v1.0.0](https://spec.openapis.org/overlay/v1.0.0.html); [overlay/v1.1.0](https://spec.openapis.org/overlay/v1.1.0.html); [release 1.1.0](https://github.com/OAI/Overlay-Specification/releases/tag/1.1.0)). The OAI repository lists implementations including Bump.sh CLI, Speakeasy CLI, overlays-js, overlay-jvm, apigee-go-gen, openapi-format, oas-patch, Specmatic, BinkyLabs.OpenApi.Overlays (.NET) and Zuplo CLI ([OAI/Overlay-Specification](https://github.com/OAI/Overlay-Specification)). Redocly CLI 1.32.0 (2025-03-03): "Added support for linting, preprocessors, decorators, and type extensions for Overlay v1 documents" ([CHANGELOG](https://github.com/Redocly/redocly-cli/blob/main/packages/core/CHANGELOG.md)). Speakeasy: `speakeasy overlay compare --before ... --after ...` generates an overlay from two versions; "currently limited to 1.0.0" ([docs](https://www.speakeasy.com/docs/prep-openapi/overlays/create-overlays)). Bump.sh: `bump overlay definition_file overlay_file`, and it describes the Overlay spec as "currently in beta" (stale relative to the OAI's 1.0.0/1.1.0 releases) ([docs](https://docs.bump.sh/help/specification-support/overlays/)). Use for this project: one canonical 3.2 source, plus overlays that derive gateway-safe 3.0/3.1 variants and partner-facing subsets, so the derivations are declarative and reviewable rather than hand-edited copies.

4. **Semantic diff.** oasdiff is the only tool checked that states it diffs 3.2 constructs. `oasdiff breaking` shows "only the changes that break existing API clients"; `oasdiff changelog` lists "changes that can affect API consumers, breaking or not". v1.30.0 (2026-08-30): "every check's severity is now derived from a single reviewed model of what each change does to the API contract, enforced in CI" — "58 new checks and corrected the severity of 36 existing ones"; overrides via `--severity-levels`; new `breaking-files` command "for pre-commit hooks". ([README](https://github.com/oasdiff/oasdiff); [v1.30.0](https://github.com/oasdiff/oasdiff/releases/tag/v1.30.0)). OpenAPITools openapi-diff states 3.0 only; Optic is archived. A CI gate can therefore be: `oasdiff breaking <base> <head>` fails the build; `oasdiff changelog` feeds the release notes; severities disputed by the team are pinned with `--severity-levels` in the repository.

5. **Version-string policy.** Because the OAI states a 3.1 document "will work without modification after updating the version number" and the spec defines `major.minor` as the feature set, the project can pin `openapi: 3.2.0`, forbid patch-level distinctions in tooling (per the spec's SHOULD), and treat the `openapi` field as a contract property changed only by ADR.

6. **Layout.** 3.2's `$self` and multi-document guidance ("it is RECOMMENDED that tools resolve from the entry document") support the `openapi/components/*.yaml` layout already proposed in `BIZTRUST-ARCH-001` §11, provided every document has an OpenAPI Object or Schema Object at its root ([v3.2.0 §4.1.2](https://spec.openapis.org/oas/v3.2.0.html)).

## What choosing 3.1 instead would cost

Features given up (each is 3.2-only per the OAI release note): native tag hierarchy (`summary`/`parent`/`kind`, falling back to `x-tagGroups`-style extensions); the `query` method and `additionalOperations`; `in: querystring`; sequential media types and `itemSchema` for SSE / JSON Lines streams; OAuth2 device flow, `oauth2MetadataUrl` and `deprecated` on security schemes; `$self`; response `summary`; discriminator `defaultMapping`; example `dataValue` / `serializedValue`; `components.mediaTypes`; XML `nodeType`. For BizTrust's proposed contract (bearer tokens, JSON, problem+json, idempotency keys, ETags) none of these is on the critical path today; the ones most likely to matter later are tag hierarchy for the four API families and `itemSchema` if event streams are exposed over HTTP.

Tooling gained by 3.1: Spectral's `oas3_1` rules and format-scoped rulesets; Prism mocking (states 3.1); openapi-generator (states 3.1 as beta); Swagger Core/Parser (Java); Google Cloud API Gateway and Kong (3.1.x / 3.1.0). Tooling *not* gained: AWS API Gateway (3.0 only) and full-fidelity Azure APIM (3.1 "import only"; "For full fidelity, use OpenAPI 2.0 or 3.0.x"). A gateway-import artifact would have to be a derived 3.0 document under either choice.

Cost of moving from 3.1 to 3.2 later: by the OAI's statement, a version-string change; `oasdiff upgrade` already targets 3.2.0 as the canonical 3.x form. oasdiff's docs add the practical caveat that "some downstream tools perform strict version checking on the `openapi:` field value" and may reject 3.2.0 even where keywords are identical ([oasdiff.com/docs/openapi-31-migration](https://www.oasdiff.com/docs/openapi-31-migration)). The cost is therefore low in authoring effort and concentrated in the toolchain gate, which is the same gate 3.2 needs now.

## Decision-relevant facts for ADR-005

- OpenAPI 3.2.0 is published (Appendix A: 2025-09-19; GitHub release `2025-09-19T16:20:24Z`); `latest.html` resolves to 3.2.0; the OAI states 3.1 documents "will work without modification after updating the version number"; a `v3.3-dev` branch exists and Moonwalk (4.0) has "no planned end date", with the OAI recommending 3.x today.
- Linting is covered: Redocly CLI has stated 3.2 support since 2.3.0 (2025-10-03) with 3.2-specific rules through 2.40.0 (2026-07-21); Spectral has no `oas3_2` format and an open issue/PR (#2910, #2917); vacuum's parser libopenapi states 3.2 support.
- Client generation is split: Kiota (1.30.0, 2026-01-27) and OpenAPI.NET 3.x state 3.2 support; openapi-generator states only "3.1 (beta support)" and has an open bug that 3.2 `query` operations are silently dropped; the Swagger Java stack (Core, Parser) and the JS swagger-parser have open 3.2 items and no support statement.
- Mocking and diffing: Prism states 3.1 as its ceiling; Redocly claims 3.2 in its mock server; oasdiff reads 3.2 and, as of v1.29.0–v1.30.0 (Aug 2026), diffs `itemSchema`, `query` and `additionalOperations` and ships a reviewed severity model with `--severity-levels` overrides and a `breaking-files` pre-commit command; openapi-diff is 3.0-only and Optic is archived.
- No gateway checked states 3.2: AWS REST (2.0/3.0), Azure APIM (3.0.x full; 3.1 import-only; custom `x-` extensions dropped), Google (3.0.x/3.1.x), Kong (3.0.x/3.1.0 plugin; 3.1.x catalog). Any gateway import needs a derived 3.0/3.1 artifact regardless of whether the source is 3.1 or 3.2 — an Overlay 1.1 pipeline (or `oasdiff`/vendor downgrade) is the building block, and `x-` metadata must not be relied on surviving import.

## Unverified items

- Kong decK `openapi2kong`: no version-acceptance statement found on its documentation page; not tested.
- Speakeasy SDK generator: no first-party statement on 3.2 support found (only explanatory content about the spec).
- Redoc standalone renderer: README lists 3.1/3.0/2.0 while a banner announces "Redoc 3.0 is coming — one renderer for OpenAPI 3.2"; Redocly's blog claims rendering support. Which Redoc version renders 3.2-only fields (e.g. nested tags) was not verified.
- Swagger Editor: no 3.2 statement found.
- oasdiff's wording that "The OpenAPI Initiative guarantees strict compatibility within 3.x going forward (3.2.x, 3.3.x, ...)" was not found verbatim in any OAI text; the OAI's own statements are the narrower ones quoted above (3.1 documents work under 3.2 after a version bump; `major.minor` designates the feature set).
- Spectral behaviour on a `openapi: 3.2.0` document: by source inspection the `oas3` format matches on major version, so `oas3`-scoped rules would run and `oas3_1`-scoped rules would not; this was inferred from source, not executed.
- Gateways outside the four checked (Apigee, Tyk, APISIX, Gravitee, Envoy Gateway) were not examined.
- Redocly's changelog dates were taken from the `@redocly/cli@x.y.z` GitHub release timestamps; the changelog file itself is undated.
- Nothing here was run locally; all support claims are the vendors' words on 2026-09-05 and should be re-checked before ADR-005 is accepted.

## Sources

All checked 2026-09-05.

OpenAPI Initiative
- https://spec.openapis.org/oas/v3.2.0.html (Appendix A revision history; §Versions; §Specification Extensions; §4.1.2)
- https://spec.openapis.org/oas/latest.html
- https://github.com/OAI/OpenAPI-Specification/releases/tag/3.2.0
- https://github.com/OAI/OpenAPI-Specification/releases (3.1.2, 3.1.1, 3.0.4 dates)
- https://github.com/OAI/OpenAPI-Specification/branches (`v3.3-dev`)
- https://www.openapis.org/blog/2025/09/23/announcing-openapi-v3-2
- https://learn.openapis.org/upgrading/v3.1-to-v3.2.html
- https://github.com/OAI/sig-moonwalk
- https://spec.openapis.org/overlay/v1.0.0.html
- https://spec.openapis.org/overlay/v1.1.0.html
- https://github.com/OAI/Overlay-Specification (implementations list)
- https://github.com/OAI/Overlay-Specification/releases/tag/1.1.0

Linters
- https://github.com/stoplightio/spectral/blob/411b144950b85c6c8fa31881e390b66f7263712a/packages/formats/src/openapi.ts
- https://github.com/stoplightio/spectral/blob/develop/packages/rulesets/src/oas/index.ts
- https://github.com/stoplightio/spectral/blob/develop/README.md
- https://github.com/stoplightio/spectral/issues/2910 ; https://github.com/stoplightio/spectral/pull/2917
- https://github.com/stoplightio/spectral/releases
- https://github.com/Redocly/redocly-cli/blob/main/README.md
- https://github.com/Redocly/redocly-cli/blob/main/packages/core/CHANGELOG.md
- https://github.com/Redocly/redocly-cli/releases
- https://redocly.com/blog/openapi-3-2
- https://github.com/daveshanley/vacuum/blob/main/README.md
- https://github.com/daveshanley/vacuum/releases/tag/v0.26.0 ; https://github.com/daveshanley/vacuum/issues/805
- https://github.com/pb33f/libopenapi/blob/main/README.md

Generators and parsers
- https://github.com/OpenAPITools/openapi-generator/blob/master/README.md
- https://github.com/OpenAPITools/openapi-generator/issues/24212
- https://github.com/OpenAPITools/openapi-generator/releases
- https://github.com/microsoft/kiota/blob/main/CHANGELOG.md
- https://github.com/microsoft/kiota/releases/tag/v1.30.0
- https://github.com/microsoft/kiota/blob/main/Directory.Packages.props
- https://github.com/microsoft/OpenAPI.NET/releases/tag/v3.0.0
- https://github.com/microsoft/OpenAPI.NET/blob/main/README.md
- https://github.com/swagger-api/swagger-core/blob/master/README.md
- https://github.com/swagger-api/swagger-core/issues/5181 ; https://github.com/swagger-api/swagger-core/pull/5253
- https://github.com/swagger-api/swagger-parser/blob/master/README.md
- https://github.com/swagger-api/swagger-parser/issues/2248
- https://github.com/APIDevTools/swagger-parser/blob/main/README.md
- https://github.com/APIDevTools/swagger-parser/releases/tag/v12.1.0 ; https://github.com/APIDevTools/swagger-parser/pull/286

Renderers and mock servers
- https://github.com/swagger-api/swagger-ui/blob/master/README.md
- https://github.com/swagger-api/swagger-editor/blob/master/README.md
- https://github.com/Redocly/redoc/blob/main/README.md
- https://github.com/stoplightio/prism/blob/master/README.md
- https://github.com/stoplightio/prism/releases

Diff tools
- https://github.com/oasdiff/oasdiff
- https://github.com/oasdiff/oasdiff/blob/main/docs/OPENAPI-31.md
- https://github.com/oasdiff/oasdiff/releases/tag/v1.29.0 ; https://github.com/oasdiff/oasdiff/releases/tag/v1.30.0 ; https://github.com/oasdiff/oasdiff/releases/tag/v1.15.0
- https://www.oasdiff.com/docs/openapi-31-migration
- https://github.com/OpenAPITools/openapi-diff/blob/master/README.md
- https://github.com/opticdev/optic

Gateways and hosted services
- https://developer.konghq.com/plugins/oas-validation/
- https://developer.konghq.com/deck/file/openapi2kong/
- https://developer.konghq.com/api-products/
- https://learn.microsoft.com/en-us/azure/api-management/api-management-api-import-restrictions
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-import-api.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-known-issues.html
- https://docs.cloud.google.com/api-gateway/docs/openapi-overview
- https://docs.bump.sh/help/specification-support/openapi-support/
- https://docs.bump.sh/help/specification-support/overlays/
- https://www.speakeasy.com/docs/prep-openapi/overlays/create-overlays
- https://www.speakeasy.com/openapi/release-notes/

<!-- agent: researcher (wayfinder research, 2026-09-05) -->
