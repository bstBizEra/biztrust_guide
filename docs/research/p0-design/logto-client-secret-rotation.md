# Logto client secret rotation: overlap, expiry and the legacy secret

| Field | Value |
|---|---|
| Ticket | [Issue #240](https://github.com/bstBizEra/biztrust_guide/issues/240) (parent [#128](https://github.com/bstBizEra/biztrust_guide/issues/128); answers the P0.12 design's open question 3) |
| Design served | [`docs/architecture/p0/P0.12-secrets-and-configuration.md`](../../architecture/p0/P0.12-secrets-and-configuration.md), the rotation exercise for the Logto client secret and negative control 5 |
| Sources checked | 2026-09-06, Logto's official documentation, API reference and GitHub release notes only (see Sources) |
| Research status | `COMPLETE FOR THE P0.12 QUESTION; NOTHING SELECTED` |
| Implementation authority | `NOT GRANTED` |

Every claim below is tied to a source ID in the Sources section. Anything not found on an official page is listed under Unverified items. Quotations are verbatim from the cited page as retrieved on the check date.

## Question

How is a Logto machine-to-machine application's client secret rotated: can an application hold more than one secret at a time, can a secret carry an expiry, how is a new secret created and an old one deleted through the Console and the Management API, and what happens to tokens issued under the old secret? The P0.12 design assumed a single secret replaced rather than overlapped and marked the mechanics `UNVERIFIED`.

## Answer

**An application can hold several secrets at once, each with an optional expiry, so rotation is an overlap, not a cut-over.** Since Logto v1.19.0 (2024-08-08), "Secure apps (machine-to-machine, traditional web, Protected) can now have multiple app secrets with expiration. This allows for secret rotation and provides an even safer experience." [R1]. A secret is created by name with an optional `expiresAt` ("The epoch time in milliseconds when the secret will expire. If not provided, the secret will never expire.") [A1]; it is deleted by name [A3]; only its name can be changed afterwards [A4]. The overlap the P0.12 exercise needs is therefore: create the new secret, move the platform's `SecretSource` to it, then delete the old one.

**The secret an application was created with is a "legacy secret" with its own endpoint.** "The legacy secret created before this feature can still be used for client authentication. However, it is recommended to delete the old ones and create new secrets with expiration for enhanced security." [R1]. Deleting it does not leave the application without a secret: `DELETE /api/applications/{id}/legacy-secret` will "Delete the legacy secret for the application and replace it with an internal secret used only by Logto. The internal secret is not returned by Management APIs and cannot be used for client authentication." [A5]; since v1.42.0 (2026-07-30), "Internal application secrets are no longer exposed through Management APIs." [R2]. An application created after v1.19.0 may or may not carry a legacy secret; the endpoint answers 400 when "The application does not have a legacy secret" [A5].

**What happens to tokens issued under a deleted secret is not documented.** The machine-to-machine quick start shows the token request (`grant_type=client_credentials`, `resource`, `scope`, credentials as Basic `{App ID}:{App Secret}`) and an access token with `expires_in: 3600` [D2], but no official page states whether an access token already issued survives the deletion or expiry of the secret that obtained it. Under the OAuth 2.0 client credentials grant the secret authenticates the token request, not the token, so the platform should expect issued tokens to run to their own expiry; that is an inference from the grant's shape, recorded under Unverified, and control 5's measurement is what settles it.

**Listing secrets returns their values.** `GET /api/applications/{id}/secrets` returns each secret's `value` in clear (1 to 64 characters) [A2]. For P0.12 that means the Management API token the platform uses to administer its own secrets is itself a credential of the highest class, and a read of that endpoint is a secret read that the store's request log will not see; the design's evidence contract should name the Management API audit trail, or a rule that the platform never lists secrets, as the compensating record.

## Findings

### F1. Multiple secrets with expiry, since v1.19.0

The release note lists the five endpoints and the Console surface: "To manage your application secrets, go to Logto Console -> Applications -> Application Details -> Endpoints & Credentials. The original app secret read-only input field is now replaced with a new secrets management table. You can create, update, and delete secrets in this table." [R1]. The API reference fixes the shapes: `POST /api/applications/{id}/secrets` with `name` ("The secret name. Must be unique within the application.", 1 to 256 characters) and optional `expiresAt` [A1]; the 201 response carries `tenantId`, `applicationId`, `name`, `value` (1 to 64 characters), `createdAt` and `expiresAt` [A1]; `GET /api/applications/{id}/secrets` returns the same objects, values included [A2]; `DELETE /api/applications/{id}/secrets/{name}` "removes a secret for the application by name" with a 204 [A3]; `PATCH /api/applications/{id}/secrets/{name}` takes only `name` [A4].

### F2. Which applications have a secret

"Application secret is a key used to authenticate the application in the authentication system, specifically for private clients (Traditional Web and M2M apps) as a private security barrier." "Single Page Apps (SPAs) and Native apps don't provide App secret." [D1]. The API's client in P0 is a machine-to-machine application, so it is in scope.

### F3. The legacy secret and the internal secret

Applications created before v1.19.0 hold a legacy secret that still authenticates [R1]. The endpoint that removes it replaces it with an internal secret that "cannot be used for client authentication" [A5]; the API changelog records that on 2026-07-30 the endpoint's `secret` property became not required and its 204 response was removed, marked breaking [C1], which matches v1.42.0's note that internal secrets are no longer exposed [R2]. For a platform that creates its application after v1.19.0, the first thing the rotation exercise should establish is whether a legacy secret exists at all (the 400 answer), so that the exercise rotates the named secrets and not a secret that cannot be listed.

### F4. The token request and lifetime

The quick start's request is a form-encoded POST to the token endpoint with `grant_type=client_credentials`, `resource` and `scope`, authenticated by a Basic header built from the App ID and App Secret; the response's `expires_in` is 3600 seconds in the example [D2]. The quick start does not mention rotation or revocation [D2].

### F5. Expiry enforcement

`expiresAt` is described as the moment "when the secret will expire" [A1]. No page checked states what the token endpoint returns for a request authenticated with an expired secret; the natural reading is a refused request, recorded under Unverified.

## Decision-relevant facts for P0.12

1. **Control 5 measures an overlap, not a cut-over.** The exercise creates a second named secret with an `expiresAt`, switches `SecretSource` to it, confirms the token endpoint accepts the new secret, then deletes the old one by name and confirms the old secret is refused. The design's `ASSUMED` position on question 3 (a single secret replaced) is reversed by [R1] and [A1].
2. **Tokens already issued are the measurement.** No page states their fate; the exercise records whether a token obtained with the old secret is still accepted by the API and by Logto's resources after the secret is deleted, until its own `expires_in` elapses.
3. **The legacy secret is checked first.** The exercise's step 1 asks `DELETE /api/applications/{id}/legacy-secret` only if `GET .../secrets` shows the application still relies on one; an application created on a current version may have none, and the 400 answer says so [A5].
4. **Every secret carries an expiry.** Since a secret without `expiresAt` "will never expire" [A1], the inventory's `rotation_period` for the Logto client should be enforced by creating each secret with `expiresAt` at the period's end, so an unrotated secret stops working rather than lingering.
5. **Listing returns values.** The Management API credential that can list secrets is a bootstrap-class secret in the inventory, and the platform's own code path should never call the list endpoint in production; the design's least-privilege table for the Management API role should say so.

## Unverified items

- What the token endpoint returns for an expired or deleted secret: not stated on any page checked. UNVERIFIED; measured by control 5.
- Whether access tokens issued with a secret survive that secret's deletion or expiry: not stated; the inference from the client credentials grant is that they run to their own expiry. UNVERIFIED; measured by control 5.
- A maximum number of secrets per application: not stated [A1]. UNVERIFIED.
- Whether the Console's secrets table shows secret values after creation or only once: not stated on the pages checked. UNVERIFIED.
- The exact Logto version BizTrust would run: the stack decision names none; every citation here is to the current documentation on the check date.

## Sources

All checked 2026-09-06.

Logto documentation
- [D1] Application data structure, "Application secret": https://docs.logto.io/integrate-logto/application-data-structure
- [D2] Machine-to-machine quick start: https://docs.logto.io/quick-starts/m2m

Logto Management API reference
- [A1] Add application secret, `POST /api/applications/{id}/secrets`: https://openapi.logto.io/operation/operation-createapplicationsecret
- [A2] Get application secrets, `GET /api/applications/{id}/secrets`: https://openapi.logto.io/operation/operation-listapplicationsecrets
- [A3] Delete application secret, `DELETE /api/applications/{id}/secrets/{name}`: https://openapi.logto.io/operation/operation-deleteapplicationsecret
- [A4] Update application secret, `PATCH /api/applications/{id}/secrets/{name}`: https://openapi.logto.io/operation/operation-updateapplicationsecret
- [A5] Delete application legacy secret, `DELETE /api/applications/{id}/legacy-secret`: https://openapi.logto.io/operation/operation-deleteapplicationlegacysecret
- [C1] API changelog, entries of 2026-05-22 and 2026-07-30 on the secrets endpoints: https://openapi.logto.io/changes

Logto release notes (GitHub)
- [R1] v1.19.0, 2024-08-08, "Multiple app secrets management": https://github.com/logto-io/logto/releases/tag/v1.19.0
- [R2] v1.42.0, 2026-07-30, "Internal application secrets are no longer exposed through Management APIs": https://github.com/logto-io/logto/releases/tag/v1.42.0
