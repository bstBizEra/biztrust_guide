# Secrets management candidates: rotation and least privilege

| Field | Value |
|---|---|
| Ticket | [Issue #136](https://github.com/bstBizEra/biztrust_guide/issues/136) (parent [#128](https://github.com/bstBizEra/biztrust_guide/issues/128), blocks [#147](https://github.com/bstBizEra/biztrust_guide/issues/147)) |
| Work package | `BIZTRUST-GUIDE-WP-ARCH-001A` |
| Delivery-plan item served | P0.12 "Secrets/configuration management: rotation and least-privilege evidence" (`docs/architecture/DELIVERY_PLAN.md`) |
| Sources checked | 2026-09-05, official documentation and licence files only (see Sources) |
| Research status | `COMPLETE FOR P0.12 DESIGN INPUT; NO CANDIDATE SELECTED` |
| Implementation authority | `NOT GRANTED` |

Every claim below is tied to a source ID in the Sources section. Anything not found in an official page is listed under Unverified items and is not used in the comparison table. Quotations are verbatim from the cited page as retrieved on the check date.

## Ticket

[#136 Research: secrets management candidates, rotation and least privilege](https://github.com/bstBizEra/biztrust_guide/issues/136). Output required: this file on branch `research/secrets-management`, plus a resolution comment carrying the comparison table.

## Question

P0.12 requires a rotation exercise and least-privilege evidence. From official documentation only, compare HashiCorp Vault (licence since the BSL change), OpenBao, SOPS with age or KMS, and a cloud KMS with secret store (AWS Secrets Manager with AWS KMS chosen) on: dynamic database credentials and rotation, audit of secret access, application integration shapes, self-host footprint, licence, and exit path. Name which candidates can rotate the PostgreSQL application role's credential without downtime, and how the documentation says to prove it.

Lao data residency for the cloud option is a separate question owned by ADR-019 (`docs/architecture/ADR_REGISTER.md`) and is not decided here.

## Comparison table

| Candidate | Dynamic DB credentials and rotation | Audit of secret access | Application integration shapes | Self-host footprint | Licence | Exit path |
|---|---|---|---|---|---|---|
| **HashiCorp Vault** (Community) | Dynamic roles issue per-request PostgreSQL users via `creation_statements` with `VALID UNTIL '{{expiration}}'`, `default_ttl`/`max_ttl`, lease revocation [V2][V3]. Static roles are "a 1-to-1 mapping of Vault roles to usernames in a database"; Vault "stores and automatically rotates passwords" on `rotation_period` (default 24h, minimum 5s) or cron `rotation_schedule` with optional `rotation_window`; the two are "mutually exclusive" [V2][V4]. Manual `POST /database/rotate-role/:name`; root rotation `POST /database/rotate-root/:name` with the warning that the root password "will not be accessible once rotated" [V4]. PostgreSQL plugin lists "Root Credential Rotation" as supported [V3]. | "Vault audit devices record all API requests and responses in detail"; "Vault only writes a keyed hash (HMAC-SHA256) of most string values"; if no enabled device can be written, "Vault refuses to service the corresponding API request"; device types file, syslog, socket; auditing is disabled at init and must be enabled [V5]. | HTTP API/CLI; Vault Agent auto-auth, template rendering to files with an `exec` block that runs a command "when template output changes", `static_secret_render_interval` (default 5m), renewal at 2/3 of lease, re-fetch at 90% TTL for non-renewable leases; process supervisor mode injects env vars and `restart_on_secret_changes` (`always` default, `never`) [V6][V7][V8]. | Integrated Storage (Raft) "stores Vault's data on the server's filesystem and uses a consensus protocol to replicate data to each server"; "we recommended at least 5 servers for a standard production deployment"; single-server production "strongly discourage[d]"; odd node count advised [V9][V10]. | Business Source License 1.1, Licensor IBM, "Vault Version 1.15.0 or later". Additional Use Grant: "You may make production use of the Licensed Work, provided Your use does not include offering the Licensed Work to third parties on a hosted or embedded basis in order to compete with IBM Corp's paid version(s)". Change Date "Four years from the date the Licensed Work is published"; Change License MPL 2.0 [V1]. | Raft snapshot API: "returns a snapshot of the current state of the raft cluster"; restore "Installs the provided snapshot"; force-restore "bypasses checks ensuring the Autounseal or shamir keys are consistent with the snapshot data" [V11]. Data is Vault-encrypted; usable only by a Vault-compatible engine with the same unseal material. |
| **OpenBao** | Same engine shape: "Static roles are a 1-to-1 mapping of OpenBao roles to usernames in a database"; `rotation_period` is `<required>`, "The minimum is 5 seconds"; `POST /database/rotate-role/:name`; `POST /database/rotate-root/:name` with the same root-password warning; `GET /database/static-creds/:name` returns `username`, `password`, `last_openbao_rotation`, `rotation_period`, `ttl` [O4][O5]. PostgreSQL plugin lists root credential rotation and static roles as supported [O6]. The retrieved API page contains no `rotation_schedule` or `rotation_window` parameter (0 matches) [O5]. | "the audit log contains _every_ interaction with the OpenBao API, including errors"; "Most strings ... are hashed with a salt using HMAC-SHA256"; "OpenBao will not respond to requests when no enabled audit devices can record them"; device types File, HTTP, Syslog, Socket [O7]. | OpenBao Agent: "Automatically authenticate to OpenBao and manage the token renewal process"; template rendering; "Runs a child process with OpenBao secrets injected as environment variables" [O8]. Vault-shaped HTTP API (`X-Vault-Token` header in the documented samples) [O5]. | Raft Integrated Storage: "all the nodes in an OpenBao cluster will have a replicated copy of OpenBao's data"; supports HA; Filesystem, In-Memory and PostgreSQL backends also documented [O9]. Installs as packages "for Amazon Linux, Debian, Fedora, RHEL, Ubuntu", containers on GHCR/Quay/Docker Hub, single `bao` binary, Helm [O10]. | `LICENSE` file: "Mozilla Public License, version 2.0" (copyright line "Copyright (c) 2015 HashiCorp, Inc.") [O2]. Site: "fork of Vault managed by the Linux Foundation's OpenSSF"; mission: "provide this software under an OSI-approved open-source license, led by a community run under open governance principles" [O1]. "OpenBao is a Sandbox project at OpenSSF" [O3]. | Raft snapshot endpoints with the same wording as Vault ("returns a snapshot of the current state of the raft cluster"; force-restore "bypasses checks ensuring the Autounseal or shamir keys are consistent") [O11]. |
| **SOPS with age (or KMS)** | None. SOPS "is an editor of encrypted files"; `rotate` "generates a new data encryption key and reencrypt all values with the new key", which rotates the file's data key, not any database password [S1][S3]. The PostgreSQL role password is a value inside the file; changing it is a manual `ALTER ROLE` plus re-encrypt plus redeploy (no doc describes automation). Key groups split the data key with "Shamir's Secret Sharing" so a threshold of groups is required to decrypt [S4]. | Optional decrypt log: "SOPS will write a log entry into a pre-configured PostgreSQL database when a file is decrypted. The log includes a timestamp, the username SOPS is running as, and the file that was decrypted"; config fixed at `/etc/sops/audit.yaml` [S5]. With a KMS master key, the KMS provider's own logs apply (not covered here). | `sops decrypt` to stdout/file; `exec-env` and `exec-file` "place all output into the environment of a child process and into a temporary file, respectively" [S5]. Design intent: "Secrets must be stored in GIT" and "always be encrypted on disk ... and only be decrypted on the target systems" [S6]. | No server. Files live in git; decryption needs the age identity (`keys.txt` under the user config dir) or KMS access [S7]. age is "a simple, modern and secure file encryption tool, format, and Go library" with X25519, passphrase and SSH-key recipients; format spec at age-encryption.org/v1 [A1]. | SOPS: "Mozilla Public License Version 2.0"; CNCF Sandbox since 2023 [S1]. age: BSD 3-Clause ("Copyright 2019 The age Authors", Google LLC, Filippo Valsorda) [A2]. | Trivial: `sops decrypt` yields plaintext; file format is open and "SOPS will remain backward compatible on the major version" [S2]. |
| **AWS Secrets Manager + AWS KMS** | No dynamic (per-request) credentials. Rotation by Lambda: `create_secret`, `set_secret`, `test_secret`, `finish_secret` steps, staging labels `AWSPENDING` -> `AWSCURRENT`, previous version kept as `AWSPREVIOUS`; failures retried "multiple times during the open rotation windows" [W2][W4]. Two strategies: single user ("open database connections are not dropped") and alternating users ("appropriate for applications that require high availability ... After rotation, both `user` and `user_clone` credentials are valid"), the latter needing a separate superuser secret [W3][W6]. Templates `SecretsManagerRDSPostgreSQLRotationSingleUser` / `MultiUser` are listed for "Amazon RDS and Amazon Aurora PostgreSQL" (dependency PyGreSQL 6.1.0); a generic template exists for "any type of secret" [W5]. Schedule "as often as every four hours"; "Rotate immediately" option [W6]. | "AWS CloudTrail records all API calls for Secrets Manager as events"; `GetSecretValue` entries are generated; service events `RotationStarted`, `RotationSucceeded`, `RotationFailed`, `RotationAbandoned`, `TestRotation*` [W8][W9]. KMS `Decrypt`/`GenerateDataKey` calls carry encryption context `SecretARN` and `SecretVersionId`, usable "to identify these cryptographic operation in audit records and logs" [W7]. | SDK `GetSecretValue`/`BatchGetSecretValue`; "we recommend that you cache your secret values by using client-side caching"; Python cache "By default, the cache refreshes secrets every hour"; also EKS, Lambda, CloudFormation, GitHub/GitLab integrations listed [W10][W11]. | None to run. Rotation Lambda must have network access to the database (Step 4) and turning rotation on needs `iam:CreateRole` and `iam:AttachRolePolicy`, which "allows an identity to grant themselves any permissions" [W6]. Secret encryption is envelope encryption under `aws/secretsmanager` or a customer-managed symmetric KMS key; name, description, rotation settings, key ARN and tags are not encrypted [W7]. | Proprietary managed service under AWS terms (not a source-code licence; not assessed here). | Per-secret `GetSecretValue`; secret versions retrievable by staging label. No bulk export documented on the pages checked (see Unverified). Region and residency: ADR-019. |

## Which candidates can rotate the PostgreSQL application role's credential without downtime, and how the docs say to prove it

### AWS Secrets Manager, alternating-users strategy: yes, stated explicitly

The only candidate whose documentation makes the no-downtime claim in words. Single user: "When the secret rotates, open database connections are not dropped. While rotation is happening, there is a short period of time between when the password in the database changes and when the secret is updated. During this time, there is a low risk of the database denying calls that use the rotated credentials ... After rotation, new connections use the new credentials." Alternating users: "It is also appropriate for applications that require high availability. If an application retrieves the secret during rotation, the application still gets a valid set of credentials. After rotation, both `user` and `user_clone` credentials are valid. There is even less chance of applications getting a deny during this type of rotation than single user rotation." [W3]

Proof, per the docs:
1. Turn on rotation with "Rotate immediately when the secret is stored" or call `RotateSecret` [W6][W9].
2. The function's `testSecret` step "tests the `AWSPENDING` version of the secret by using it to access the database" before `finishSecret` moves `AWSCURRENT` [W4].
3. "As you test your function, use the AWS CLI to see version stages: call `describe-secret` and look at `VersionIdsToStages`" [W4]; expect the new version under `AWSCURRENT` and the old under `AWSPREVIOUS`.
4. Confirm the CloudTrail service events `RotationStarted` then `RotationSucceeded` (not `RotationFailed`/`RotationAbandoned`) [W9], and the application's `GetSecretValue` entries after rotation [W8].
5. Caveats the docs themselves state: with the alternating strategy the app must re-read the secret (cache refresh default one hour [W11]) and the two users must keep identical grants: "If you change the original user's permissions after the clone is created, you must also change the cloned user's permissions" [W3]. Amazon RDS Proxy "does not support the alternating users strategy" [W6]. The PostgreSQL templates are written for RDS/Aurora; a self-managed PostgreSQL needs the generic template and custom code [W5].

### Vault and OpenBao: yes by design for dynamic roles; static roles rotate the password but the docs do not state the effect on open sessions

Dynamic roles: each application instance obtains its own user with `VALID UNTIL '{{expiration}}'` and a lease; "Services that need to access a database no longer need to hardcode credentials: they can request them from Vault, and use Vault's leasing mechanism to more easily roll keys" [V2][V3]. Because a new lease is issued before the old one expires, an instance can open connections on the new user while the old user is still valid; there is no single shared password to flip. The docs describe this mechanism but do not use the words "zero downtime" (recorded under Unverified as an inference from the mechanism, not a quotation).

Static roles: Vault/OpenBao change the mapped user's password and hand out the new one; the docs are explicit on the trigger and the readback but silent on whether PostgreSQL keeps existing sessions open (PostgreSQL's `ALTER ROLE` page is also silent, see Unverified). A rotation therefore has a window between the password change and the application re-reading `static-creds`; Vault Agent closes it by re-rendering and running `exec`, or by `restart_on_secret_changes = "always"` in process-supervisor mode [V7][V8].

Proof, per the docs:
1. Read `GET /database/static-creds/:name` and record `password` and `last_vault_rotation` (OpenBao: `last_openbao_rotation`) [V4][O5].
2. `POST /database/rotate-role/:name` to "manually trigger a rotation to change the stored password and reset the TTL" [V4][O5].
3. Read `static-creds` again: new `password`, advanced `last_vault_rotation`, `ttl` reset toward `rotation_period` [V4].
4. Both the read and the rotate appear in the audit device log (HMAC'd values, request and response) [V5][O7]; this is the least-privilege and rotation evidence P0.12 asks for.
5. Connect to PostgreSQL with the new password; for dynamic roles, `vault read database/creds/my-role` twice yields two distinct users, and revoking the first lease invalidates that user "within a reasonable time of the lease expiring" [V2][V3].
6. Do not rotate the connection's own root credential through a static role: "any dynamic or static users managed by that database configuration will fail after rotation because the password for config/ is no longer valid"; use `rotate-root` instead, with a dedicated Vault user because the rotated root password "will not be accessible" [V2][V4].
7. Out-of-band changes break the exercise: "Out-of-band password rotations will cause Vault to be out of sync with the state of the DB user, and will require manually updating the user's password in the external PostgreSQL DB" [V3].

### SOPS with age or KMS: no

`sops rotate` "generates a new data encryption key and reencrypt all values with the new key" [S3]; nothing in the SOPS or age documentation changes a database password or coordinates a cut-over. Rotating the application role means editing the encrypted file, running `ALTER ROLE` by hand, committing, and redeploying; whether that is downtime-free depends entirely on the deployment tooling, and the only evidence SOPS produces is the optional decrypt log [S5]. It remains a reasonable carrier for bootstrap material (for example the Vault/OpenBao unseal or AppRole seed, or the AWS rotation Lambda's superuser secret) rather than a runtime secrets manager.

## Findings per candidate

### HashiCorp Vault

Licence. The repository `LICENSE` is Business Source License 1.1; Licensor "International Business Machines Corporation (IBM)"; Licensed Work "Vault Version 1.15.0 or later. The Licensed Work is (c) 2024 IBM Corp."; grant "to copy, modify, create derivative works, redistribute, and make non-production use"; Additional Use Grant permitting production use "provided Your use does not include offering the Licensed Work to third parties on a hosted or embedded basis in order to compete with IBM Corp's paid version(s) of the Licensed Work"; Change Date "Four years from the date the Licensed Work is published"; Change License "MPL 2.0" [V1]. For BizTrust, running Vault to protect its own application secrets is production use inside the grant; offering a hosted secrets service to third parties would not be. The HashiCorp licence FAQ page could not be read past a JavaScript checkpoint, so its definitions of "competitive offering" and "embedded" are Unverified here.

Rotation model. Two mechanisms coexist: dynamic roles (per-request users with TTL and lease revocation) and static roles (Vault-owned password on a fixed user, `rotation_period` default 24h or cron `rotation_schedule` with `rotation_window`; a missed window "will not be rotated until the next scheduled rotation") [V2][V4]. `skip_import_rotation` controls whether the password is rotated when the static role is created [V4]. The PostgreSQL plugin supports SCRAM (`password_authentication="scram-sha-256"`) for the root connection [V3].

Audit and least privilege. Audit devices log every request and response with HMAC-SHA256 hashing of string values, and Vault refuses service when no device can write, which makes the log itself a control rather than a best-effort record [V5]. Policies are path-based; the static-role warning notes that "anyone with the proper Vault policies can access the associated user account" [V2].

Footprint. Integrated Storage needs no external system; the internals page recommends "at least 5 servers for a standard production deployment" for failure tolerance 2, gives the 3-node option (quorum 2, tolerance 1), and strongly discourages a single node [V9][V10]. That is the heaviest self-host bill of the four candidates.

Exit. Raft snapshots are the documented backup/restore path [V11]; the data stays Vault-encrypted, so exit in practice means OpenBao (same storage and API shape) or re-issuing secrets, not reading the snapshot elsewhere.

### OpenBao

Identity and licence. The project site describes it as a "fork of Vault managed by the Linux Foundation's OpenSSF" [O1]; the `LICENSE` file is MPL 2.0 [O2]; it is an OpenSSF Sandbox project [O3]. The exact Vault version the fork was taken from is behind a collapsed FAQ accordion whose text is not in the served HTML (Unverified).

Parity that matters for P0.12. The database engine, static roles, `rotate-role`, `rotate-root` (with the identical root-password warning), audit devices (plus an HTTP device), Agent auto-auth/templating/process supervisor, Raft storage and Raft snapshot API all appear with the same wording as Vault [O4] to [O11]. Two differences were observed in the retrieved pages: `rotation_period` is marked `<required>` and no `rotation_schedule`/`rotation_window` parameters are documented [O5]; and a PostgreSQL storage backend is listed alongside Raft [O9], which could let BizTrust reuse its PostgreSQL operations discipline for the secrets store itself (not evaluated further here).

Footprint. Same operational shape as Vault; distribution packages, containers and Helm are documented [O10]. The Raft node-count guidance quoted for Vault was not located on an OpenBao page (Unverified for OpenBao specifically).

### SOPS with age (or KMS)

SOPS is "an editor of encrypted files that supports YAML, JSON, ENV, INI and BINARY formats and encrypts with AWS KMS, GCP KMS, Azure Key Vault, HuaweiCloud KMS, age, and PGP", MPL 2.0, CNCF Sandbox [S1]. Its docs recommend age over PGP [S7]; age is BSD 3-Clause [A2]. Values are encrypted with AES256_GCM and the data key with the KMS/PGP/age master keys; the documented threat model is about compromised cloud credentials or private keys, not runtime access control [S6]. Key groups add a threshold requirement across master keys [S4]. Rotation (`sops rotate`) is data-key rotation, and the docs recommend renewing the data key "on a regular basis" [S3]. Audit is an optional PostgreSQL decrypt log (timestamp, OS user, file) with a fixed config path so users cannot disable it [S5]. Integration is `decrypt`, `exec-env`, `exec-file` [S5]. It carries no server, no dynamic credentials and no policy engine; least-privilege evidence is limited to who holds which age identity or KMS grant. SOPS can also use a Vault/OpenBao transit engine as its master key [S8], which is one way the candidates compose rather than compete.

### AWS Secrets Manager with AWS KMS

Encryption. Envelope encryption: a 256-bit AES data key per secret value, generated and wrapped by the chosen symmetric KMS key (`aws/secretsmanager` managed key or a customer-managed key); the plaintext data key is used outside KMS and then removed from memory; `kms:ViaService` and the `SecretARN`/`SecretVersionId` encryption context can restrict and audit key use; secret name, description, rotation settings, key ARN and tags are stored unencrypted [W7].

Rotation. Managed rotation exists only for some AWS-managed secret types; database secrets rotate by Lambda through the four-step protocol with staging labels [W1][W2][W4]. The alternating-users strategy is the one the docs tie to high availability, at the cost of a second database user with mirrored grants and a stored superuser secret [W3][W6]. Schedules are `rate()`/`cron()`, minimum every four hours, with a rotation window and retries [W6].

Audit. All API calls, including `GetSecretValue`, are CloudTrail events, and rotation state changes are emitted as service events (`RotationStarted`, `RotationSucceeded`, `RotationFailed`, `RotationAbandoned`, `TestRotation*`) [W8][W9]; KMS-side `Decrypt`/`GenerateDataKey` events carry the secret ARN and version in the encryption context [W7].

Footprint and blast radius. Nothing to host, but enabling rotation requires IAM permissions the docs flag as equivalent to self-granting any permission, and the rotation function is "a privileged deputy" that must validate `AWSCURRENT` before changing credentials to avoid confused-deputy misuse [W4][W6]. Client-side caching (default hourly refresh) is recommended and bounds how quickly an app observes a rotation [W10][W11].

Residency. Region choice and any Lao data-location constraint are ADR-019's question; nothing in this research changes that.

## Decision-relevant facts for P0.12

1. Only AWS Secrets Manager's documentation states in words that rotation keeps the application connected ("open database connections are not dropped"; alternating users "appropriate for applications that require high availability") [W3]. Vault and OpenBao achieve the same outcome structurally through dynamic roles with overlapping leases, but their docs do not make the claim and PostgreSQL's `ALTER ROLE` page is silent on existing sessions, so a P0.12 exercise on a Vault/OpenBao static role must measure connection behaviour rather than cite it.
2. Vault and OpenBao are the only candidates that produce the two artefacts P0.12 asks for from one system: a request/response audit log that blocks service when it cannot write, and a rotation record (`last_vault_rotation` / `last_openbao_rotation`, `rotate-role`) [V4][V5][O5][O7]. SOPS yields only a decrypt log; AWS yields CloudTrail plus rotation service events [S5][W8][W9].
3. Licence: Vault is BSL 1.1 with production use permitted unless offered "to third parties on a hosted or embedded basis" to compete with IBM's paid versions, converting to MPL 2.0 four years after each version's publication [V1]; OpenBao is MPL 2.0 today [O2]; SOPS is MPL 2.0 and age is BSD 3-Clause [S1][A2]. If BizTrust ever exposes secrets management to tenants as a hosted feature, the Vault grant is the clause to re-read; OpenBao carries no such clause.
4. Self-host cost is the real divider: Vault's own guidance is five servers for production (three is the minimum with failure tolerance one) [V9]; OpenBao is the same shape [O9]; SOPS is zero servers; AWS is zero servers but requires a rotation Lambda with database network access and IAM permissions the docs call self-escalating [W6].
5. OpenBao's retrieved database API lacks Vault's cron `rotation_schedule`/`rotation_window` (only `rotation_period`, minimum 5s, required) [O5]; and AWS's PostgreSQL rotation templates target RDS/Aurora, so a self-managed PostgreSQL needs custom rotation code from the generic template [W5]. Both are practical constraints for the rotation exercise, not blockers.

## Unverified items

- HashiCorp licence FAQ (definitions of "competitive offering", "embedded", the list of products under BSL, and the date of the licence change, reported in secondary sources as August 2023): the page `https://www.hashicorp.com/en/license-faq` returned a Vercel "Security Checkpoint" to non-JavaScript clients and the answer text was collapsed in the rendered fetch. UNVERIFIED; the `LICENSE` file [V1] is the authority used instead.
- Which Vault version OpenBao forked from, and whether all existing MPL code stays MPL: the OpenBao homepage FAQ lists the questions ("Which version of Hashicorp Vault are you planning to fork from?", "Will the existing MPL 2.0 licensed code be migrated to another license?") but the accordion answers are not in the served HTML. UNVERIFIED.
- OpenBao cluster-size guidance (3 vs 5 nodes): not located on an OpenBao page; only Vault's internals page was found [V9]. UNVERIFIED for OpenBao.
- Whether PostgreSQL keeps existing sessions authenticated after `ALTER ROLE ... PASSWORD`: `https://www.postgresql.org/docs/current/sql-alterrole.html` contains no statement either way. UNVERIFIED; must be measured in the P0.12 exercise.
- That Vault/OpenBao dynamic roles give zero-downtime rotation: an inference from the lease mechanism described in [V2][V3], not a quotation. UNVERIFIED as a documented claim.
- Whether CloudTrail `GetSecretValue` entries omit the secret value: not stated on the pages checked [W8][W9]. UNVERIFIED.
- A bulk export path for AWS Secrets Manager: not found on the pages checked. UNVERIFIED.
- AWS Secrets Manager region availability relevant to Lao residency: out of scope, ADR-019.
- Vault Enterprise-only feature boundaries (for example replication) were not assessed; only Community-documented behaviour is cited.

## Sources

All checked 2026-09-05.

HashiCorp Vault
- [V1] Vault `LICENSE` (BSL 1.1): https://github.com/hashicorp/vault/blob/main/LICENSE
- [V2] Databases secrets engine (static roles, rotation_period/rotation_schedule/rotation_window, root-credential warning, leasing): https://developer.hashicorp.com/vault/docs/secrets/databases
- [V3] PostgreSQL database secrets engine (capabilities table, creation_statements, static role example, out-of-band warning, scram-sha-256): https://developer.hashicorp.com/vault/docs/secrets/databases/postgresql
- [V4] Database secrets engine API (static-roles, static-creds, rotate-role, rotate-root, rotation_period minimum, skip_import_rotation): https://developer.hashicorp.com/vault/api-docs/secret/databases
- [V5] Audit devices: https://developer.hashicorp.com/vault/docs/audit
- [V6] Vault Agent overview: https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent
- [V7] Vault Agent templates (`exec`, `static_secret_render_interval`, renewal behaviour): https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent/template
- [V8] Vault Agent process supervisor mode (`restart_on_secret_changes`): https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent/process-supervisor
- [V9] Integrated Storage internals (deployment table, five-server recommendation): https://developer.hashicorp.com/vault/docs/internals/integrated-storage
- [V10] Integrated Storage concepts: https://developer.hashicorp.com/vault/docs/concepts/integrated-storage
- [V11] Raft storage API (snapshot, restore, force-restore): https://developer.hashicorp.com/vault/api-docs/system/storage/raft
- Not usable: HashiCorp licence FAQ https://www.hashicorp.com/en/license-faq (checkpoint; see Unverified)

OpenBao
- [O1] Project site (fork statement, mission statement): https://openbao.org/
- [O2] OpenBao `LICENSE` (MPL 2.0): https://github.com/openbao/openbao/blob/main/LICENSE
- [O3] What is OpenBao (OpenSSF Sandbox, dynamic secrets, leasing, revocation): https://openbao.org/docs/what-is-openbao/
- [O4] Databases secrets engine (static roles, root-credential warning): https://openbao.org/docs/secrets/databases/
- [O5] Database secrets engine API (rotate-root, rotate-role, static-creds, rotation_period): https://openbao.org/docs/api/secret/databases/ (source: https://github.com/openbao/openbao/blob/main/website/content/docs/api/secret/databases/index.mdx)
- [O6] PostgreSQL database secrets engine: https://openbao.org/docs/secrets/databases/postgresql/
- [O7] Audit devices: https://openbao.org/docs/audit/
- [O8] OpenBao Agent: https://openbao.org/docs/agent-and-proxy/agent/
- [O9] Integrated Storage (Raft) configuration: https://openbao.org/docs/configuration/storage/raft/
- [O10] Install: https://openbao.org/docs/install/
- [O11] Raft storage API: https://openbao.org/docs/api/system/storage/raft/ (source: https://github.com/openbao/openbao/blob/main/website/content/docs/api/system/storage/raft.mdx)

SOPS and age
- [S1] SOPS README (definition, key services, licence, CNCF): https://github.com/getsops/sops/blob/main/README.rst
- [S2] SOPS docs index (backward compatibility): https://getsops.io/docs/
- [S3] Key management (`rotate` command, Key Rotation): https://getsops.io/docs/usage/key-management/ (source: https://github.com/getsops/docs/blob/main/content/en/docs/usage/key-management/_index.md)
- [S4] Key groups (Shamir threshold): https://getsops.io/docs/usage/identities/key-groups/
- [S5] Advanced usage (Auditing; `exec-env`, `exec-file`): https://getsops.io/docs/usage/advanced/
- [S6] Security (operational requirements, threat model): https://getsops.io/docs/security/
- [S7] age identities (recommended over PGP, `keys.txt` location): https://getsops.io/docs/usage/identities/age/
- [S8] HashiCorp Vault / OpenBao as SOPS key service (transit engine): https://getsops.io/docs/usage/identities/hashicorp-vault-openbao/
- [A1] age README: https://github.com/FiloSottile/age/blob/main/README.md
- [A2] age `LICENSE` (BSD 3-Clause): https://github.com/FiloSottile/age/blob/main/LICENSE

AWS Secrets Manager and AWS KMS
- [W1] Rotate secrets (managed vs Lambda rotation): https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html
- [W2] Rotation by Lambda function (step parameters, retries): https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda.html
- [W3] Lambda function rotation strategies (single user, alternating users): https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html
- [W4] Lambda rotation functions (four steps, `VersionIdsToStages`, confused deputy): https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html
- [W5] Rotation function templates (PostgreSQL single/alternating, generic): https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_available-rotation-templates.html
- [W6] Set up automatic rotation for database secrets (strategy choice, schedule, IAM warning, network access): https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_turn-on-for-db.html
- [W7] Secret encryption and decryption with AWS KMS: https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html
- [W8] Log events with CloudTrail: https://docs.aws.amazon.com/secretsmanager/latest/userguide/monitoring-cloudtrail.html
- [W9] CloudTrail entries (operation and rotation events): https://docs.aws.amazon.com/secretsmanager/latest/userguide/cloudtrail_log_entries.html
- [W10] Get a secret value using Python (caching recommendation): https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets-python.html
- [W11] Python client-side caching (hourly refresh): https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_cache-python.html

PostgreSQL (consulted only to test a claim; recorded under Unverified)
- ALTER ROLE: https://www.postgresql.org/docs/current/sql-alterrole.html
