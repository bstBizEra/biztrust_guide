# Research: APISIX as the gateway candidate on the security spine

## Ticket

[#133 — Research: APISIX as the gateway candidate on the security spine](https://github.com/bstBizEra/biztrust_guide/issues/133)

Vocabulary is taken from `docs/architecture/BIZTRUST-ARCH-001.md` section 8 (identity and authorization contract): Logto owns authentication and organization identity context; BizTrust owns tenant business structure and authority; every protected request must verify token signature/issuer/expiry, API audience, `organization_id`, required scopes, active tenant and membership, resource scope and business authority, approval authority, and the database RLS outcome. An organization identifier arriving in a URL, header, query string or body is requested context only.

All claims below were checked on 2026-09-05 against the unversioned "latest" pages at `apisix.apache.org/docs/apisix/...`, the `apache/apisix` GitHub repository, and the Apache licence page. Anything not stated in those sources is listed under "Unverified items" and is not inferred.

## Question

The P0 security spine names APISIX as a gateway candidate between the Logto organization token and the API boundary. From official sources only: what do the `openid-connect` and `jwt-auth` plugins validate (signature, issuer, audience, expiry); can an organization claim be required and forwarded to upstream headers; mTLS to upstream; rate limiting and request-id propagation; Admin API and declarative configuration; licence; and the exit path. What can the gateway prove about tenant context, and what remains the application's job for P0.3 and P0.4?

## Findings

### F1. `openid-connect` plugin: what it validates

The plugin has a bearer-token mode: `bearer_only` — "If true, strictly require bearer access token in requests for authentication." Signature verification of a bearer JWT is done either against a configured key (`public_key`: "Public key used to verify JWT signature if asymmetric algorithm is used. Providing this value to perform token verification will skip token introspection in client credentials flow."), or the provider's JWKS (`use_jwks`: "If true and if `public_key` is not set, use the JWKS to verify JWT signature and skip token introspection in client credentials flow."), or by calling the provider's introspection endpoint (`introspection_endpoint`: "URL of the token introspection endpoint for the OpenID provider used to introspect access tokens."). Issuer: `claim_validator.issuer.valid_issuers` is "An array of trusted JWT issuers. If unconfigured, the issuer returned by the discovery endpoint will be used, and a token is rejected while the discovery document cannot be fetched, since no trusted issuer is known then." Audience: `claim_validator.audience.claim` (default `aud`), `claim_validator.audience.required` ("If true, audience claim is required and the name of the claim will be the name defined in `claim`."), and `claim_validator.audience.match_with_client_id` ("If true, require the audience to match the client ID."). Audience is *not* required by default (`required` defaults to `false`). Scopes: `required_scopes` — "Scopes required to be present in the access token. If any required scope is missing, the Plugin rejects the request with a 403 forbidden error." Expiry: the page documents `introspection_expiry_claim` (default `exp`, "controls the TTL of the cached and introspected access token") and JWK cache expiry; it does not state in a sentence that a JWKS-verified bearer JWT is rejected on `exp` (see U1).
Source: https://apisix.apache.org/docs/apisix/plugins/openid-connect/ (checked 2026-09-05).

### F2. `openid-connect` plugin: what it forwards upstream

Three forwarding switches exist, all defaulting to `true`: `set_access_token_header` ("If true, set the access token in a request header. By default, the `X-Access-Token` header is used."), `set_id_token_header` ("If true and if the ID token is available, set the value in the `X-ID-Token` request header." with the note "this header contains `base64(JSON(decoded_claims))` and carries no cryptographic signature."), and `set_userinfo_header` ("If true and if user info data is available, set the value in the `X-Userinfo` request header."). `access_token_in_authorization_header` puts the access token in `Authorization` instead. The documented claim checks are limited to issuer, audience and scopes; the page documents no generic "require claim X" option, so a Logto `organization_id` claim cannot be *required* by this plugin's documented configuration alone (U2).
Source: https://apisix.apache.org/docs/apisix/plugins/openid-connect/ (checked 2026-09-05).

### F3. `jwt-auth` plugin: what it validates and forwards

"The `jwt-auth` Plugin supports the use of JSON Web Token (JWT) as a mechanism for clients to authenticate themselves before accessing Upstream resources." It is consumer-keyed: `key_claim_name` (default `key`) is "The claim in the JWT payload that identifies the associated secret, such as `iss`." Each consumer credential carries `algorithm` (HS256 default; HS/RS/ES/PS families and EdDSA), `secret`, or `public_key` ("Public key in PEM format required by the configured asymmetric algorithm."). Time claims: `claims_to_verify` defaults to `["exp", "nbf"]` — "Specify the JWT claim(s) to verify, to ensure that the token is used within its allowed timeframe." The page does not mention `aud` validation and mentions `iss` only as a possible `key_claim_name`; no audience check is documented. On success "APISIX adds additional headers, such as `X-Consumer-Username`, `X-Credential-Identifier`, and other Consumer custom headers if configured, to the request." `store_in_ctx` ("If true, store JWT payload in the request context variable `ctx.jwt_auth_payload`.") exposes the payload to later plugins; `hide_credentials` ("If true, do not pass the header, query, or cookie with JWT to Upstream services.") strips the token. This plugin models one static key per consumer, not a rotating IdP JWKS, so it fits machine/API-key style clients better than Logto organization tokens.
Source: https://apisix.apache.org/docs/apisix/plugins/jwt-auth/ (checked 2026-09-05).

### F4. Forwarding derived values as upstream headers (`proxy-rewrite`)

`proxy-rewrite` `headers.set` / `headers.add` / `headers.remove` rewrite request headers; "Header value could be set to a constant, one or more NGINX variables, or the matched result of `regex_uri` using variables such as `$1-$2-$3`." The page's example sets `"X-Apisix-Consumer": "$consumer_name"`. `set` "cannot be used for the `Host` header". This is the documented mechanism for stamping gateway-known values (consumer name, request id, remote address) onto the upstream request; it does not itself parse JWT claims into variables (U3).
Source: https://apisix.apache.org/docs/apisix/plugins/proxy-rewrite/ (checked 2026-09-05).

### F5. Delegating the authorization decision: `forward-auth` and `opa`

`forward-auth` "supports the integration with an external authorization service for authentication and authorization. If the authentication fails, a customizable error message will be returned to the client. If the authentication succeeds, the request will be forwarded to the Upstream service along with the following request headers that APISIX added". APISIX sends `X-Forwarded-Proto`, `X-Forwarded-Method`, `X-Forwarded-Host`, `X-Forwarded-Uri`, `X-Forwarded-For`; `request_headers` chooses client headers to pass to the auth service; `upstream_headers` are "External authorization service response headers that should be forwarded to the Upstream service"; a 2xx from the auth service allows, non-2xx denies; `status_on_error` (default 403) applies on network error. `opa` sends `request`, `var`, and optionally `route`/`service`/`consumer` to an OPA server at `/v1/data/<policy>`; OPA returns `allow`, optional `reason`, `headers`, `status_code`; `send_headers_upstream` is the "List of header names to forward from the OPA response to the Upstream". These are the documented ways to make the gateway enforce a tenant-aware decision the plugin schema cannot express — at the price of an extra network hop per request and of moving the decision into a service that must itself hold BizTrust membership data.
Sources: https://apisix.apache.org/docs/apisix/plugins/forward-auth/ ; https://apisix.apache.org/docs/apisix/plugins/opa/ (checked 2026-09-05).

### F6. Custom logic in the gateway (`serverless-pre-function`)

The serverless plugins "enable the execution of user-defined logic at the beginning and end of the execution phases" in phases `rewrite`, `access`, `header_filter`, `body_filter`, `log`, `before_proxy`; attributes are `phase` (default `access`) and `functions` (array of Lua function strings); "Only Lua functions are allowed in the serverless plugins and not other Lua code." Combined with `jwt-auth` `store_in_ctx` this is a way to read a claim at the gateway, but it is bespoke Lua inside gateway configuration, not a declarative feature. The page states no security caveat about arbitrary code; that concern is the reviewer's, not the source's (U5).
Source: https://apisix.apache.org/docs/apisix/plugins/serverless/ (checked 2026-09-05).

### F7. mTLS to upstream

"Sometimes the upstream requires mTLS. In this situation, the APISIX acts as the client, it needs to provide client certificate to communicate with upstream." Configure on the Upstream object: `tls.client_cert` ("Sets the client certificate while connecting to a TLS Upstream."), `tls.client_key` ("Sets the client private key while connecting to a TLS Upstream."), or `tls.client_cert_id` ("Set the referenced SSL id."). "This feature requires APISIX to run on APISIX-Runtime." Upstream `scheme` may be `http`, `https`, `grpc`, `grpcs` (L7). Verification of the *upstream server's* certificate is narrow: `tls.verify` — "Turn on server certificate verification, currently only kafka upstream is supported." Client-to-gateway mTLS is separate (SSL object `client.ca`, `client.depth`), and "the mTLS protection only happens in HTTPS. If your route can also be accessed via HTTP, you should add additional protection in HTTP or disable the access via HTTP."
Sources: https://apisix.apache.org/docs/apisix/mtls/ ; https://apisix.apache.org/docs/apisix/admin-api/ (Upstream section) (checked 2026-09-05).

### F8. Rate limiting

`limit-count`: `count` ("The maximum number of requests allowed within a given time interval."), `time_window`, `key_type` (`var`, `var_combination`, `constant`), `key` (default `remote_addr`; built-ins include `remote_addr`, `server_addr`, `http_x_real_ip`, `http_x_forwarded_for`, `consumer_name`; `var_combination` takes e.g. `"$remote_addr $consumer_name"`), `rejected_code` (default 503), `policy` (`local`, `redis`, `redis-cluster`, `redis-sentinel`), `allow_degradation`, `show_limit_quota_header` ("If true, include `X-RateLimit-Limit` ... and `X-RateLimit-Remaining` ... in the response header."), `group` for shared quotas across routes. `limit-req` is leaky-bucket: `rate` ("The maximum number of requests allowed per second. Requests exceeding the rate and below burst will be delayed."), `burst`, `nodelay`, same key model. Per-tenant limiting therefore keys on a variable the gateway already knows (consumer, IP, header), not on a JWT claim unless that claim has first been surfaced as a variable/header (U3).
Sources: https://apisix.apache.org/docs/apisix/plugins/limit-count/ ; https://apisix.apache.org/docs/apisix/plugins/limit-req/ (checked 2026-09-05).

### F9. Request-id propagation

`request-id`: `header_name` (default `X-Request-Id`), `include_in_response` (default true), `algorithm` (`uuid` default, `nanoid`, `range_id`, `ksuid`). When the incoming request already carries the header, "the Plugin will use the header value as the unique ID and will not overwrite it". With `include_in_response: false` "the request ID is forwarded to the Upstream service but not returned in the response header". Consequence: a client-supplied id is trusted as-is, so the application's audit log should record it as a correlation id, not as an authenticated fact.
Source: https://apisix.apache.org/docs/apisix/plugins/request-id/ (checked 2026-09-05).

### F10. Admin API

The Admin API listens on port 9180 under `/apisix/admin`, authenticated by the `X-API-KEY` header ("The `X-API-KEY` shown below refers to the `deployment.admin.admin_key.key`"), with `allow_admin` IP allow-listing, and optionally mTLS via `admin_api_mtls` (`admin_ssl_ca_cert`, `admin_ssl_cert`, `admin_ssl_cert_key`). Resources: Route, Service, Consumer, Upstream, SSL, Global Rule, Plugin Config, Consumer Group, Stream Route. Route `vars` "Matches based on the specified variables consistent with variables in Nginx. Takes the form `[[var, operator, val], [var, operator, val], ...]]`." "Currently, the response is returned from etcd" — etcd is the configuration store in the default (traditional) mode.
Sources: https://apisix.apache.org/docs/apisix/admin-api/ ; https://apisix.apache.org/docs/apisix/mtls/ (checked 2026-09-05).

### F11. Declarative configuration (standalone mode)

Deployment roles are `traditional` (data plane + control plane in one, ports 9080/9180), `data_plane`, and `control_plane`. With `role: data_plane` and `role_data_plane.config_provider: yaml`, "The routing rules in the `conf/apisix.yaml` file are loaded into memory immediately after the APISIX node service starts"; the file is checked every second and hot-reloaded; "APISIX will not load the rules into memory from file `conf/apisix.yaml` if there is no `#END` at the end." `config_provider: json` uses `conf/apisix.json` and "the `#END` marker is not required". An API-driven standalone mode keeps rules in memory and accepts full-replacement updates via `PUT /apisix/admin/configs` with an `X-Digest` header. A Git-reviewed `apisix.yaml` without etcd is therefore a documented deployment shape, which suits a small P0 footprint.
Source: https://apisix.apache.org/docs/apisix/deployment-modes/ (checked 2026-09-05).

### F12. Licence

The repository `LICENSE` file opens "Apache License / Version 2.0, January 2004 / http://www.apache.org/licenses/" and appends an "Apache APISIX Subcomponents" section listing third-party files (Kubernetes ingress-nginx, OpenFunction samples), also Apache-2.0. Apache-2.0 grants "a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license" (s.2) and an equivalent patent licence (s.3); redistribution must carry the licence, retain notices, mark modified files and reproduce the NOTICE file (s.4); the Work is provided "AS IS" without warranty (s.7). No copyleft obligation attaches to BizTrust's own code.
Sources: https://github.com/apache/apisix/blob/master/LICENSE ; https://www.apache.org/licenses/LICENSE-2.0 (checked 2026-09-05).

## What the gateway can prove about tenant context, and what stays the application's job

| The gateway can prove (documented APISIX behaviour) | Stays the application's job (ARCH-001 s.8) |
|---|---|
| The bearer token's signature is valid against the IdP's JWKS or a configured public key, or the IdP's introspection endpoint accepted it (`openid-connect`, F1). | That the token's subject is a *currently active* BizTrust member of the tenant named in the token — membership, suspension and offboarding live in BizTrust Tenancy, not in the token. |
| The token's issuer is one of `claim_validator.issuer.valid_issuers` or the discovery document's issuer (F1). | That `organization_id` in the token equals the tenant the request is *about* — the URL/header/body identifier is "requested context only" and must be matched by the application. |
| The audience claim is present and, if configured, equals the client id (`claim_validator.audience.required` / `match_with_client_id`; off by default) (F1). | Resource scope and business authority (legal entity, branch, team, insurer relationship, product/channel entitlement, financial limit). |
| The listed `required_scopes` are all present in the access token (F1). | Approval authority for controlled actions and the `AuthorityAgreement` check that lets `binding:confirm` actually represent cover (ADR-013). |
| A consumer-keyed JWT's `exp`/`nbf` are inside the window (`jwt-auth` `claims_to_verify`, F3). | Setting the tenant on the database session so the RLS outcome is computed per request; the gateway has no database session. |
| The request arrived on a connection where the gateway presented a client certificate to the upstream (`tls.client_cert`, F7) — the application can require mTLS on its listener and reject anything not from the gateway. | Treating `X-ID-Token`, `X-Userinfo`, `X-Consumer-Username` and any organization header as *unsigned hints*: the doc says `X-ID-Token` "carries no cryptographic signature". The application re-verifies the forwarded access token (or `Authorization`) itself, so its decision does not depend on the gateway's presence. |
| A request id exists on the upstream request and (optionally) the response; a client-supplied id is preserved, not authenticated (F9). | Recording the request id as a correlation id in audit evidence, alongside the authenticated actor and tenant derived from the token, not from the header. |
| Per-key request counts within a window or per-second rate, keyed on IP/consumer/header variables (F8). | Business-level quotas and entitlements per tenant/product/channel; the gateway cannot key on a JWT claim without that claim first being surfaced as a variable (U3). |
| An external authorizer (`forward-auth`/`opa`) returned 2xx/`allow` for this request (F5). | Owning and serving that authorizer's data: membership, authority and entitlement facts are BizTrust's; the gateway only relays the verdict. |

## Decision-relevant facts for P0.3 and P0.4

1. **`openid-connect` in `bearer_only` mode checks signature (JWKS/public key/introspection), issuer, optional audience and `required_scopes`; audience is not required by default** — `claim_validator.audience.required` must be set `true` for the ARCH-001 "API audience" bullet to be enforced at the edge (F1). Whether an expired JWKS-verified JWT is rejected is not stated on the page (U1).
2. **There is no documented way to require an arbitrary claim such as Logto's `organization_id` in either plugin** — `openid-connect` validates issuer/audience/scopes only; `jwt-auth` verifies `exp`/`nbf` and a consumer-lookup claim. Requiring an organization at the gateway means `forward-auth`/`opa` (extra hop, external service) or bespoke Lua in `serverless-pre-function` (F2, F3, F5, F6).
3. **What the gateway forwards about identity is unsigned.** `X-ID-Token` is `base64(JSON(decoded_claims))` and "carries no cryptographic signature"; `X-Userinfo` and `X-Consumer-Username` are plain headers. P0.3 must have the application verify the forwarded access token itself and must never accept an organization header as authenticated context (F2, F3; ARCH-001 s.8 last paragraph).
4. **mTLS gateway-to-application is a first-class Upstream setting (`tls.client_cert`/`tls.client_key`/`tls.client_cert_id`) but needs APISIX-Runtime, and upstream *server*-cert verification is documented only for Kafka** — so the application listener enforces "only the gateway may connect", while the gateway does not verify the application's certificate (F7). Rate limiting keys on IP/consumer/header variables and `request-id` preserves a client-supplied id (F8, F9).
5. **Operationally light and licence-clean:** Apache-2.0 with an Apache-2.0 subcomponents list; a Git-reviewed `conf/apisix.yaml` (`config_provider: yaml`, `#END` marker, one-second hot reload) runs a data plane without etcd, and the Admin API (port 9180, `X-API-KEY`, `allow_admin`, optional mTLS) exists for the traditional/API-driven modes (F10, F11, F12).

## Exit path

If the gateway is removed, the application loses only what the gateway added at the edge: first-line token rejection before the request reaches application code, IP/consumer rate limiting, request-id minting, a single place to terminate client TLS/mTLS and to present a client certificate to the application, and declarative routing. It loses nothing it was required to do anyway: every bullet in ARCH-001 s.8 — signature, issuer, expiry, audience, `organization_id`, scopes, active tenant and membership, resource scope and authority, approval authority, RLS — is either impossible for the gateway (membership, authority, RLS) or must be re-done by the application because the gateway's forwarded evidence is unsigned (F2). The design rule that keeps the exit cheap: the application verifies the original bearer token itself (from `Authorization` or `X-Access-Token`), treats every gateway header as a hint, generates its own request id when `X-Request-Id` is absent, and binds its listener to mTLS-from-gateway as a *deployment* control rather than an *authorization* control. Under that rule the gateway is defence in depth, and removing it is a routing and TLS change, not an authorization change. If instead P0.3 lets the application trust `X-Userinfo`/`X-ID-Token`/an organization header, removal (or a bypass of the gateway) becomes a tenant-isolation failure — the exit path would be closed by design, not by APISIX.

## Unverified items

- **U1.** The `openid-connect` page does not contain a sentence stating that a JWKS- or public-key-verified bearer JWT is rejected when `exp` has passed; the only expiry attributes documented are `introspection_expiry_claim` (TTL of cached introspected tokens), `access_token_expires_in`/`_leeway` (session renewal) and `jwk_expires_in` (JWK cache). Whether expiry is enforced on the JWKS path is UNVERIFIED from first-party APISIX docs (the behaviour lives in the underlying library, which is not a first-party APISIX source).
- **U2.** No first-party page documents a generic "required claim" option for `openid-connect` beyond issuer, audience and scopes. Absence in the docs is reported as absence; it was not confirmed against the plugin source code.
- **U3.** Whether JWT claims are exposed as NGINX/APISIX variables usable by `proxy-rewrite` headers, Route `vars`, or `limit-count` keys is not documented on the pages checked; `jwt-auth` documents only `ctx.jwt_auth_payload` (a Lua context variable, not an NGINX variable).
- **U4.** Compatibility of Logto's organization tokens (issuer, `aud` format, JWKS endpoint) with `openid-connect`'s discovery/JWKS flow was not checked; Logto is out of scope for this ticket.
- **U5.** The `serverless` page states no security caveat about executing Lua from configuration; the caveat in F6 is the reviewer's, not the source's.
- **U6.** Doc pages are the unversioned "latest" at apisix.apache.org; the APISIX release they describe was not pinned. Pin a version before P0.3 writes configuration.
- **U7.** Whether a client-supplied `X-ID-Token`/`X-Userinfo` header is stripped before the plugin sets its own is not stated on the page; the application should not rely on those headers regardless (fact 3).

## Sources

All checked 2026-09-05.

- Apache APISIX — `openid-connect` plugin: https://apisix.apache.org/docs/apisix/plugins/openid-connect/
- Apache APISIX — `jwt-auth` plugin: https://apisix.apache.org/docs/apisix/plugins/jwt-auth/
- Apache APISIX — `proxy-rewrite` plugin: https://apisix.apache.org/docs/apisix/plugins/proxy-rewrite/
- Apache APISIX — `forward-auth` plugin: https://apisix.apache.org/docs/apisix/plugins/forward-auth/
- Apache APISIX — `opa` plugin: https://apisix.apache.org/docs/apisix/plugins/opa/
- Apache APISIX — `serverless` plugins: https://apisix.apache.org/docs/apisix/plugins/serverless/
- Apache APISIX — Mutual TLS: https://apisix.apache.org/docs/apisix/mtls/
- Apache APISIX — `limit-count` plugin: https://apisix.apache.org/docs/apisix/plugins/limit-count/
- Apache APISIX — `limit-req` plugin: https://apisix.apache.org/docs/apisix/plugins/limit-req/
- Apache APISIX — `request-id` plugin: https://apisix.apache.org/docs/apisix/plugins/request-id/
- Apache APISIX — Admin API: https://apisix.apache.org/docs/apisix/admin-api/
- Apache APISIX — Deployment modes (standalone): https://apisix.apache.org/docs/apisix/deployment-modes/
- apache/apisix repository `LICENSE`: https://github.com/apache/apisix/blob/master/LICENSE
- Apache License, Version 2.0: https://www.apache.org/licenses/LICENSE-2.0
- BizTrust — `docs/architecture/BIZTRUST-ARCH-001.md` section 8 (local checkout, read-only).

<!-- agent: researcher (wayfinder research, 2026-09-05) -->
