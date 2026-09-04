# Logto organizations as the tenant security context

## Ticket

[#95 — [ARCH-001A] Research: Logto organizations as the tenant security context](https://github.com/bstBizEra/biztrust_guide/issues/95). Parent map: #91. Blocks: #104.

## Question

ADR-002 and ADR-003 propose Logto for identity and Logto *organizations* as the tenant security context. From Logto's official documentation only: what an organization is and is not; organization roles and scopes; how organization context appears in tokens (claims, audience, per-organization tokens); machine-to-machine access within an organization; multi-organization membership; what happens on organization deletion; licensing and self-host versus cloud; and the documented exit path (data export, OIDC portability). Name the gaps an ADR would have to close by spike.

All pages were checked on 2026-09-05. Sources are Logto's documentation site (docs.logto.io), the Management API reference (openapi.logto.io), the `logto-io/logto` GitHub repository at `master`, and Logto's own pricing pages. Where a claim is taken from repository source code rather than prose documentation, that is stated, because code is a snapshot of `master` on the date checked and not a supported contract.

## Findings

### F1. What an organization is

Logto defines an organization as "a group of users (identities). It can represent the teams, business customers, and partner companies who can access to your application." A user with membership is "an organization member (i.e. member) within that organization's context." Organizations are positioned for "multi-tenant SaaS and business-to-business (B2B) apps." Source: https://docs.logto.io/organizations/understand-how-organizations-work and https://docs.logto.io/organizations (checked 2026-09-05).

### F2. What an organization is not: it is not a Logto tenant, and it does not isolate application data

Logto uses "tenant" for its own administrative unit (a Logto instance with its own configuration and console) and "organization" for the customer-facing multi-tenancy entity inside a tenant. The architecture guide says: "One production Logto tenant is usually sufficient for most needs" and "If you are building a SaaS application with the concept of 'workspace' or 'organization' for each customer, you can use organizations to manage each customer's workspace within a single tenant." The multi-tenant guide says "An organization in an identity management system corresponds to your SaaS app's workspace, project, or tenant" and treats data isolation between organizations as a separate concern the application implements; Logto's organization feature provides identity, membership and permissions, not storage partitioning. In the database schema every organization row carries a `tenant_id` foreign key to `tenants`, confirming organizations are children of a Logto tenant. Sources: https://docs.logto.io/introduction/plan-your-architecture, https://docs.logto.io/use-cases/multi-tenancy/build-multi-tenant-saas-application, https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organizations.sql (checked 2026-09-05).

### F3. Organization template: roles and permissions are defined once, shared by all organizations

An organization template is "a blueprint that specifies which roles and permissions are available in each organization." "Every organization created in your Logto tenant automatically inherits the template." "Changes to the template update the roles and permissions available to all organizations," and customization "is at the template level, not per organization." Organization roles are "Collections of permissions granted to users or M2M (machine-to-machine) clients within an organization." Organization permissions are "Fine-grained non-API actions (e.g., UI features, business logic) that can be assigned to roles." Global roles "can have API resource permissions but cannot have organization permissions"; organization roles "can have both API resource permissions and organization (non-API) permissions." The `organization_roles` table references only `tenants`, not `organizations`, and has a `type` column (`User` or `MachineToMachine`), which matches the prose: role definitions are tenant-wide, role *assignments* are per organization. Sources: https://docs.logto.io/authorization/organization-template, https://docs.logto.io/authorization/role-based-access-control, https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_roles.sql (checked 2026-09-05).

### F4. Three authorization models, and which one carries organization context to an API

Logto documents three models. (1) Global API resources: JWT access tokens whose `aud` is the API resource identifier and whose `scope` comes from global roles; "When access is not organization-specific or users/clients operate across all organizations." (2) Organization (non-API) permissions: an "organization token" whose `aud` is the organization itself, used for in-app feature gating. (3) Organization-level API resources: a JWT for a registered API resource that also carries `organization_id`, with scopes filtered to the user's organization roles. The comparison table states that model 3 defines API resources with permissions and uses organization roles but not global roles. Model 3 is the one that lets a resource server enforce tenant context. Source: https://docs.logto.io/authorization/role-based-access-control (checked 2026-09-05).

### F5. Organization token (model 2): request and claims

To obtain an organization token the client must have been granted the scope `urn:logto:scope:organizations` at sign-in; the token is requested with `grant_type=refresh_token` plus `organization_id=<id>` (the SDKs expose `getOrganizationToken(organizationId)`), with `resource` set to `urn:logto:resource:organizations`. The resource server must "ensure the `aud` (audience) matches the formatted organization identifier (e.g., `urn:logto:organization:{organization_id}`)", split the space-separated `scope`, and check `exp`. The ID token exposes an `organizations` claim listing the organization IDs the user belongs to. In core source, the `organization_roles` ID-token claim is built as `${organizationId}:${roleName}` strings (`packages/core/src/oidc/scope.ts`). Organization tokens are always JWTs: "opaque tokens cannot be used as organization tokens. Organization tokens are always issued in JWT format." Sources: https://docs.logto.io/authorization/organization-permissions, https://docs.logto.io/concepts/opaque-token, https://docs.logto.io/end-user-flows/organization-experience/organization-switcher, https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/scope.ts (checked 2026-09-05).

### F6. Organization-level API resource token (model 3): request and claims

Request `/oidc/token` with `grant_type=refresh_token`, `resource=<API resource identifier>` and `organization_id=<id>`. "The resulting JWT will contain both the API audience (`aud` claim) and the organization context (`organization_id` claim), with scopes filtered to those granted by the user's organization roles." The documented validation steps for the API are: verify signature against Logto's JWKs, check `exp`, check `iss`, check `aud` equals the registered API resource, check `organization_id` "aligns with the request context", and check required permissions in `scope`. The same API resource can serve both contexts: "If you request an access token **without** an `organization_id`, only global roles/permissions are considered. If you request an access token **with** an `organization_id`, Logto evaluates the user's organization roles." In core source, `getExtraTokenClaimsForOrganizationApiResource` returns `{ organization_id: organizationId }` only when both `organization_id` and `resource` are present. Sources: https://docs.logto.io/authorization/organization-level-api-resources, https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/extra-token-claims.ts (checked 2026-09-05).

### F7. Membership and MFA are enforced at token issuance (source code, not prose contract)

The prose says organization tokens carry only the scopes the user's organization roles grant; the enforcement is visible in core source. In `packages/core/src/oidc/grants/utils.ts`, `checkOrganizationAccess` calls `queries.organizations.relations.users.exists({ organizationId, userId })` and throws an `AccessDenied` with `statusCode = 403` and message "user is not a member of the organization"; it also calls `getMfaStatus` and rejects with "organization requires MFA but user has no MFA configured". `handleOrganizationToken` sets `at.aud = buildOrganizationUrn(organizationId)` and reduces `scope` to `availableScopes.filter((name) => scope.has(name))`. In `refresh-token.ts`, a refresh token that lacks `urn:logto:scope:organizations` is rejected with `InsufficientScope` when `organization_id` is supplied. The prose for `isMfaRequired` says: "Members without MFA configured will not be able to exchange organization tokens until they set up MFA" and the feature "only checks if the user has MFA configured. It does not force users to use MFA when exchanging access tokens." Sources: https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/grants/utils.ts, https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/grants/refresh-token.ts, https://docs.logto.io/organizations/organization-management (checked 2026-09-05).

### F8. Machine-to-machine access inside an organization

"Machine-to-machine applications can also be added to organizations. You can assign roles to machine-to-machine applications like you assign roles to users." The organization template supports M2M organization roles (the `organization_roles.type` column and the `organization_role_application_relations` table with a `check_organization_role_type(..., 'MachineToMachine')` constraint). An M2M app obtains an organization-scoped token with `grant_type=client_credentials`, `organization_id`, `scope`, and optionally `resource` for an organization-level API resource; the documentation says "The only difference is that you need to use the client_credentials grant type instead of the refresh_token grant type." In core source (`client-credentials.ts`), if `organization_id` is supplied and `queries.organizations.relations.apps.exists(...)` is false, Logto throws `AccessDenied` (403) "app has not associated with the organization"; scopes are filtered by `getApplicationScopes(organizationId, clientId)`. The `organization_application_relations` table has a check constraint allowing only `MachineToMachine` application types. Separately, the Logto Management API is reached with an M2M app holding the built-in "Logto Management API access" role (resource `https://[tenant-id].logto.app/api`, scope `all`); that is tenant-wide, not organization-scoped. Sources: https://docs.logto.io/organizations/organization-management, https://docs.logto.io/authorization/organization-level-api-resources, https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/grants/client-credentials.ts, https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_application_relations.sql, https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_role_application_relations.sql, https://docs.logto.io/integrate-logto/interact-with-management-api (checked 2026-09-05).

### F9. Multi-organization membership and switching

"a user can be a member of multiple organizations. For example, a user can have a personal workspace and join the company's workspace." Users keep "a single identity while accessing different workspaces (organizations) based on their assigned roles." The switcher pattern is: list the user's organizations, then on selection "call the SDK method `getOrganizationToken(organizationId)`"; "Each time they switch, the app fetches a new organization token." A backend can enumerate a user's organizations and roles with `GET /api/users/{userId}/organizations`, which returns each organization with an `organizationRoles` array. Sources: https://docs.logto.io/introduction/plan-your-architecture, https://docs.logto.io/use-cases/multi-tenancy/build-multi-tenant-saas-application, https://docs.logto.io/end-user-flows/organization-experience/organization-switcher, https://openapi.logto.io/operation/operation-listuserorganizations (checked 2026-09-05).

### F10. Organization creation, invitation and just-in-time provisioning

Organizations are created in the Console or by the application backend via the Management API ("Wrap these calls in your own API layer... validate the request by checking their permissions, then call the Logto Management API"); the Account API is not documented as creating organizations. Members join by admin assignment, by email invitation (`organization_invitations` with statuses `Pending`, `Accepted`, `Expired`, `Revoked` and a unique pending invitation per invitee and organization), or by JIT provisioning: enterprise SSO users "will automatically join the organization and get default organization roles", and for email-domain JIT "if their verified email address match the configured JIT email domains at the organization level, they will be provisioned" — new sign-ups only, not existing users signing in. Default roles "come from the organization template." Each enterprise customer "requires a unique connector." Sources: https://docs.logto.io/end-user-flows/organization-experience/create-organization, https://docs.logto.io/organizations/just-in-time-provisioning, https://docs.logto.io/end-user-flows/enterprise-sso, https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_invitations.sql (checked 2026-09-05).

### F11. Organization data shape and the `customData` hook

The `organizations` table holds `id`, `name` (128 chars), `description`, `custom_data` (jsonb), `is_mfa_required`, `is_trusted_device_allowed`, `color`, `branding`, `custom_css`, `created_at`, and `tenant_id`. The custom-claims script receives, for user access tokens issued for an organization, the organization's `id`, `name`, `description` and `customData` "for storing internal organization mappings", and can call `api.denyAccess()`; "Logto built-in token claims cannot be overridden or modified." For self-hosted deployments the docs warn that "granting script edit or test access is equivalent to granting code execution on the Logto host." Sources: https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organizations.sql, https://docs.logto.io/developers/custom-token-claims/create-script, https://docs.logto.io/developers/custom-token-claims (checked 2026-09-05).

### F12. What happens on organization deletion

The Management API documents `DELETE /api/organizations/{id}` as "Delete organization by ID." with no stated cascade behaviour, and the organization management and configuration pages do not describe deletion effects. The database schema on `master` is explicit: `organization_user_relations`, `organization_application_relations`, `organization_role_user_relations`, `organization_role_application_relations` and `organization_invitations` all reference `organizations (id)` (directly or through the membership relation) with `on delete cascade`. So membership, role assignments, M2M associations and invitations are removed with the organization at the database level. No official page states what happens to already-issued organization tokens (see Unverified). Sources: https://openapi.logto.io/operation/operation-deleteorganization, https://docs.logto.io/organizations/organization-management, and the five `packages/schemas/tables/organization_*.sql` files under https://github.com/logto-io/logto/tree/master/packages/schemas/tables (checked 2026-09-05).

### F13. Licensing

The repository README states the license as "MPL-2.0" and the `LICENSE` file is the Mozilla Public License Version 2.0. The self-hosted plans page lists OSS Community (free, "Complete authentication and authorization", "Unlimited users and applications"), Self-hosted Pro ("$199/mo, billed annually", early access) and Self-hosted Enterprise (custom). Gating is by "A signed license file, pasted into Logto Console... verified offline", and the page states "Everything that is free in Logto OSS today stays free. The commercial license only ever unlocks capabilities; it never blocks something your deployment can already do." Paid self-hosted additions listed are console collaborators with role governance, mandatory MFA policy enforcement, branding removal, IdP-initiated SSO, unlimited SAML applications and supported SLAs. Sources: https://github.com/logto-io/logto/blob/master/README.md, https://github.com/logto-io/logto/blob/master/LICENSE, https://logto.io/self-hosted-plans (checked 2026-09-05).

### F14. Cloud pricing and what is cloud-only

Logto Cloud lists Free ($0, up to 50,000 MAU, 50K tokens), Pro ("From $24/mo", unlimited MAU, "50K free tokens, then billed by usage", "$0.08 per 100 extra"), and Enterprise (contact). Organizations on Cloud are an add-on on Pro at "$48" per month with unlimited organizations and unlimited users per organization; the Free plan does not include organizations. Other Pro add-ons: RBAC ($32), MFA ($48), Enterprise SSO ($48 per connector), advanced security ($48). The OSS page lists as Cloud-only: multi-tenant console, inviting console members, console MFA, Protected App, built-in email service, "Bring your UI", IdP-initiated enterprise SSO, unlimited SAML apps ("OSS version is limited to 3 SAML apps"), and removing the "Powered by Logto" mark. The OSS deployment page requires PostgreSQL via `DB_URL` and documents Docker and Kubernetes deployment. Sources: https://logto.io/pricing, https://docs.logto.io/logto-oss, https://docs.logto.io/logto-oss/deployment-and-configuration (checked 2026-09-05).

### F15. Exit path: data export and portability

Cloud tenant settings state: "Deleting a tenant permanently removes all associated user data and configurations. This action CANNOT be undone." On leaving: "If you plan to stop using Logto Cloud for a project, Logto can help you export all user data." and "Self-service migration (all configurations and user data) between Logto Cloud and OSS version is not supported." There is no documented self-service bulk export API; the user-migration page covers import only (Management API create-user with password hashes in Argon2, MD5, SHA1, SHA256, Bcrypt, PBKDF2 or `Legacy`, rate-limited, plus a JIT migration Action) and contains no information about exporting users or data from Logto itself. The OSS CLI documents schema alteration deploy/rollback, not dumps; on OSS the operator owns the PostgreSQL database directly. Protocol portability rests on Logto's statement that it adheres to OpenID Connect on OAuth 2.0 and supports SAML. Cloud hosting regions are "Europe, Australia, and US"; Logto states it is "SOC 2 Type II certified". Sources: https://docs.logto.io/logto-cloud/tenant-settings, https://docs.logto.io/user-management/user-migration, https://docs.logto.io/logto-oss/using-cli/database-alteration, https://logto.io/trust-and-security (checked 2026-09-05).

### F16. Personal access tokens and impersonation with organization context

"PAT-obtained tokens support the same organization permissions and scopes as refresh token flows" via the `urn:ietf:params:oauth:grant-type:token-exchange` grant with `subject_token_type=urn:logto:token-type:personal_access_token`. The user-impersonation page documents only the `resource` parameter for token exchange and does not mention `organization_id`. Sources: https://docs.logto.io/user-management/personal-access-token, https://docs.logto.io/developers/user-impersonation (checked 2026-09-05).

## Decision-relevant facts for ADR-002 and ADR-003

- **Organization is a membership-and-permission boundary, not a data boundary.** Logto organizations decide who is a member and which scopes a token carries; the application must partition its own data by `organization_id`. All organizations live inside one Logto tenant, and the organization template (roles and permissions) is tenant-wide, so BizTrust cannot give one tenant a different role vocabulary than another without modelling it in `customData` or application logic (F2, F3).
- **Tenant context reaches a BizTrust API only through the organization-level API resource token.** That JWT has `aud` = the registered API resource, `organization_id` = the organization, and `scope` filtered by the user's organization roles; the API must check `organization_id` against the request. The plain organization token has `aud` = `urn:logto:organization:{id}` and is meant for in-app feature gating, and every organization-context token is a JWT, never opaque (F4, F5, F6).
- **Membership and organization MFA are enforced at token issuance, and every token is for exactly one organization.** Non-members get 403; `isMfaRequired` blocks token exchange for users without MFA configured but does not force MFA at exchange time. Multi-organization users hold one identity and fetch a fresh token per organization when they switch; the ID token lists `organizations` and `organization_roles` as `orgId:role` (F5, F7, F9).
- **Machine identities participate the same way.** An M2M app must be associated with the organization and given an M2M organization role, then uses `client_credentials` with `organization_id`; otherwise 403 "app has not associated with the organization". Management API access is a separate, tenant-wide M2M role (F8).
- **Licensing and exit are asymmetric between OSS and Cloud.** OSS is MPL-2.0 with organizations, RBAC, and SSO in the free tier and the operator owning the PostgreSQL database; Cloud organizations are a $48/month add-on on Pro, Cloud data export is by request only, and Cloud-to-OSS migration is documented as unsupported for self-service. Organization deletion cascades membership, roles, M2M associations and invitations at the schema level, but the API documentation does not state this and token behaviour after deletion is undocumented (F12, F13, F14, F15).

## Gaps an ADR must close by spike

1. **Post-deletion and post-removal token behaviour.** No official page states whether an organization token or organization-level API token already issued remains valid after the organization is deleted or the member is removed. Spike: issue a token, remove the member (and separately delete the organization), then call the API and the introspection endpoint before `exp`.
2. **The exact `organization_id` check the API must make.** The docs say `organization_id` must "align with the request context" but not how the context is conveyed (path, header, subdomain). Spike: define the BizTrust convention and write the mismatch tests ADR-003 requires (token for org A used against org B, token without `organization_id` used against an organization route).
3. **Mapping between Logto organization and BizTrust tenant.** Whether BizTrust's tenant key lives in `organizations.customData`, in a BizTrust-side mapping table, or both, and which side is authoritative on rename or re-creation. The custom-claims script can read `customData` and can deny issuance, but on self-host it is code execution on the Logto host; spike whether it is needed at all versus a BizTrust-side lookup.
4. **Template-wide roles versus BizTrust's per-tenant authority model.** The organization template is shared by all organizations. Spike: enumerate BizTrust's authority profile roles and confirm they can be expressed as one shared template plus BizTrust-owned entitlements, without per-tenant role definitions.
5. **Self-service export on the chosen hosting model.** On Cloud, export is by request; on OSS, the database is owned by the operator but no export tool is documented. Spike: on an OSS instance, dump users, organizations, memberships and roles with `pg_dump` and re-import into a fresh instance, and record the password-hash and connector-secret behaviour.
6. **OIDC portability.** Confirm with a second OIDC provider in the lab that BizTrust's client integration depends only on standard claims plus the Logto-specific ones (`organization_id`, `organizations`, `organization_roles`), and record what a replacement would have to emit.
7. **Cloud versus OSS feature parity for the features BizTrust needs** (organization MFA, enterprise SSO per customer, custom token claims, JIT). The OSS page lists Cloud-only items, but the deployment page contains no parity statement; spike on the target OSS version and record the SAML three-app cap if SAML customers are expected.
8. **Token exchange and impersonation with organization context.** The impersonation page documents `resource` only. Spike whether `organization_id` is accepted on the token-exchange grant for support-agent use cases.

## Unverified or unverifiable items

- UNVERIFIED: whether existing organization or organization-level API tokens are revoked or continue to validate until `exp` after organization deletion or member removal. No official page states this; the schema cascade covers relations only.
- UNVERIFIED: whether Logto Cloud imposes any limit on organization count or members per organization on Enterprise, or whether OSS has any limit. The pricing page says "Unlimited" for the Pro organizations add-on; no statement was found for OSS.
- UNVERIFIED: whether `organization_id` is accepted on the `urn:ietf:params:oauth:grant-type:token-exchange` grant for impersonation (the PAT page says yes for PAT subject tokens; the impersonation page is silent).
- UNVERIFIED: the format and scope of the "export all user data" service Logto offers on Cloud (whether it includes organizations, memberships, roles and connector configuration). The tenant-settings page says to contact Logto.
- UNVERIFIED: whether the ID token `organizations` and `organization_roles` claims are documented as a stable public contract. The `organization_roles` format `orgId:roleName` was read from `packages/core/src/oidc/scope.ts` on `master`, not from a docs page.
- UNVERIFIED: the Self-hosted Pro price is labelled early access on the plans page and may change; the number is recorded as seen on 2026-09-05.
- The `checkOrganizationAccess`, `handleOrganizationToken` and client-credentials membership checks are quoted from source on `master` at the date checked and are not a versioned guarantee.

## Sources

Documentation (docs.logto.io):

- https://docs.logto.io/organizations
- https://docs.logto.io/organizations/understand-how-organizations-work
- https://docs.logto.io/organizations/organization-management
- https://docs.logto.io/organizations/just-in-time-provisioning
- https://docs.logto.io/introduction/plan-your-architecture
- https://docs.logto.io/use-cases/multi-tenancy/build-multi-tenant-saas-application
- https://docs.logto.io/authorization/role-based-access-control
- https://docs.logto.io/authorization/organization-template
- https://docs.logto.io/authorization/organization-permissions
- https://docs.logto.io/authorization/organization-level-api-resources
- https://docs.logto.io/authorization/global-api-resources
- https://docs.logto.io/concepts/opaque-token
- https://docs.logto.io/end-user-flows/organization-experience/organization-switcher
- https://docs.logto.io/end-user-flows/organization-experience/create-organization
- https://docs.logto.io/end-user-flows/organization-experience/setup-app-service-with-management-api
- https://docs.logto.io/end-user-flows/enterprise-sso
- https://docs.logto.io/integrate-logto/interact-with-management-api
- https://docs.logto.io/developers/custom-token-claims
- https://docs.logto.io/developers/custom-token-claims/create-script
- https://docs.logto.io/developers/user-impersonation
- https://docs.logto.io/user-management/personal-access-token
- https://docs.logto.io/user-management/user-migration
- https://docs.logto.io/logto-oss
- https://docs.logto.io/logto-oss/deployment-and-configuration
- https://docs.logto.io/logto-oss/using-cli/database-alteration
- https://docs.logto.io/logto-cloud/tenant-settings

Management API reference (openapi.logto.io):

- https://openapi.logto.io/operation/operation-deleteorganization
- https://openapi.logto.io/operation/operation-listuserorganizations
- https://openapi.logto.io/operation/operation-listorganizationapplications

Repository (github.com/logto-io/logto, `master`, read 2026-09-05):

- https://github.com/logto-io/logto/blob/master/README.md
- https://github.com/logto-io/logto/blob/master/LICENSE
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organizations.sql
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_roles.sql
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_user_relations.sql
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_role_user_relations.sql
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_application_relations.sql
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_role_application_relations.sql
- https://github.com/logto-io/logto/blob/master/packages/schemas/tables/organization_invitations.sql
- https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/scope.ts
- https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/extra-token-claims.ts
- https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/grants/utils.ts
- https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/grants/refresh-token.ts
- https://github.com/logto-io/logto/blob/master/packages/core/src/oidc/grants/client-credentials.ts

Pricing and trust (logto.io):

- https://logto.io/pricing
- https://logto.io/self-hosted-plans
- https://logto.io/trust-and-security
