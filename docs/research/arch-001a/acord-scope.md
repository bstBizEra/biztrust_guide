# ACORD licensing and the compatibility scope worth claiming

| Field | Value |
|---|---|
| Ticket | [Issue #101](https://github.com/bstBizEra/biztrust_guide/issues/101) |
| Feeds | `docs/architecture/BIZTRUST-ARCH-001.md` section 18, bullet "ACORD licensing and exact compatibility scope"; section 14 (integration boundary) |
| Sources checked | 2026-09-05, first-party pages on `acord.org` only |
| Status | Research complete; the recommendation is advisory and needs the operator's acceptance before section 18 is edited |
| Authority | Advisory only. No contract, licence or membership is entered into by this document. |

## Ticket

[#101 — Research: ACORD licensing and the compatibility scope worth claiming](https://github.com/bstBizEra/biztrust_guide/issues/101), label `wayfinder:research`.

## Question

From ACORD's official sources: which standards are relevant to broker-insurer data exchange for commercial lines and travel; what membership or licence is required to implement them or to claim compatibility; whether any standard is freely implementable; and what compatibility scope a Lao-market broker platform could honestly claim at v0.1. If the answer is "none needed for v0.1", say so with the source.

Everything below marked **[sourced]** is quoted or paraphrased from an ACORD page listed under Sources. Everything marked **[recommendation]** is reasoned from those sources and is not an ACORD statement. Items ACORD does not state on a public page are collected under Unverified items.

## Which ACORD standards touch broker-insurer exchange for commercial lines and travel (sourced)

ACORD's public catalogue lists these standard families ([S1](#sources)):

| Family | What ACORD says it covers | Relevance to a broker platform |
|---|---|---|
| **Property & Casualty (P&C) — XML and AL3** | "AL3 is designed as a one-way, batch communication method for policy and commission data. XML is constructed to support real-time requirements for business transactions via request and response messages." Business cases listed: New Business Quote, New Business Submission, Policy Change, Renewal, Reinstatement. Published transaction specifications include Commercial Auto Policy Quote Inquiry, Commercial Property Policy Quote and Rate, Commercial Package Policy Rate, Commercial Inland Marine Policy Rate, General Liability Policy Rate Inquiry, Workers Comp Policy Quote Inquiry ([S2](#sources)). | The commercial-lines quote, submission and policy-change vocabulary. Noted as "also relevant for Delegated Authority and Workers' Comp" ([S1](#sources)). US-market origin; a "Personal & Business Automobile State Issues Guide" is part of the package ([S2](#sources)). |
| **Global Reinsurance & Large Commercial (GRLC) — XML and JSON** | "Placing, Accounting, and Claims". GRLC Gen 2.0 lets "insurers, brokers, and service providers ... leverage a unified set of digital data standards from placing to binding to claims to settlement" ([S3](#sources), [S4](#sources)). The 2021 ePlacing release covers "advanced electronic placement processes, from submission to bind" and, in ACORD's words, "can be leveraged by stakeholders not only in reinsurance, but across all lines of business" ([S5](#sources)). | The only ACORD family whose stated purpose is broker-to-carrier placing. Built with the London market and the Ruschlikon reinsurance community; the accounting and claims side (EBOT, ECOT, Claim Movement) is back-office exchange "between brokers, insurers, and reinsurers" ([S6](#sources)). |
| **Asia-Pacific General Insurance XML** | Business cases "support most commercial and personal lines of business as well as specialty classes bound by the London Market": policy lifecycle (New Business, Endorsement, Cancellation, Reinstatement, Renewal), claims lifecycle (FNOL/FNOI, Claim Lodgement, Claim Inquiry), reporting of Claims Losses, Premium Collected, Current Account Status and Risks Bound, and "Synchronisation of Policy and Claims data" ([S7](#sources)). | The regional standard closest to BizTrust's market and to the bordereaux and account-current questions already open in section 18. Latest release v1.4.1, March 2026 ([S7](#sources)). |
| **Next-Generation Digital Standards (NGDS) — JSON** | "lightweight program and technology-agnostic ... for members to use in fine-grained transactions, such as microservices and RESTful APIs"; user stories grouped by Channel Management, Claims, Customer Service, Enterprise Services, Finance, Financial Services Agreement Administration and Sales. Latest final release v1-13-0, May 2026 ([S8](#sources)). | The API-shaped vocabulary. The fact sheet is readable by "ACORD members and non-members alike", but "Members of ACORD Standards programs automatically have access to ACORD Next-Generation Digital Standards" ([S9](#sources)). |
| **ACORD Forms** | A US library: the public Forms Index is organised as "COUNTRYWIDE P&C FORMS" plus "STATE P&C FORMS" per US state; commercial forms include Commercial Insurance Application (125), Commercial General Liability Section (126) and Commercial Policy Change Request (175); ACORD "is required to file certain forms with state insurance departments" ([S10](#sources), [S11](#sources)). | Paper and eForm layouts, not a data-exchange standard. No form in the index has "travel" in its title ([S10](#sources)). |
| **Multi-Functional / Delegated Authority** | Delegated Authority reporting "from data capture of the initial risk through to bind, and subsequent premium and claims reporting"; the download programme is for "Lloyd's Coverholders" ([S12](#sources)). | Relevant only if BizTrust becomes a coverholder-style reporter to London-market capacity. |
| **Reference Architecture** | Business Glossary, Information Model, Data Model, Capability, Component, Process and Product Models. "ACORD members and non-members may subscribe" ([S13](#sources)). ACORD's own governance text says the Reference Architecture "in itself ... is not a Standard" ([S14](#sources)). | A paid modelling reference, not a compatibility target. |

**Travel.** No first-party ACORD page found on 2026-09-05 names travel insurance as a line of business, a transaction specification, a form, or a GRLC or Asia-Pacific business case. The P&C page says line-of-business codes live in the P&C Codelists, which are served from `standards.acord.org`, an application that rendered without content to a non-member on 2026-09-05 ([S2](#sources)). Whether a travel code exists there is an Unverified item, not a finding.

## Membership and licence requirements to implement or to claim compatibility (sourced)

**Access to the standards is by membership or licence.**

- "We offer many Standards, as well as implementation guides and construction tools, to ACORD members. Once you join the proper ACORD membership or participation program, you will need to set up an account on acord.org to access the Standards and corresponding files available for that program." ([S1](#sources))
- "ACORD GRLC Data Standards are available to ACORD member organizations" ([S5](#sources)); for the GRLC data dictionary, "You will need an ACORD membership or license to access full content." ([S6](#sources))
- Terms of Program Membership, D.1: "ACORD program memberships offer access to and use of ACORD forms and/or ACORD electronic standards and/or other ACORD assets. The same will be made available subject to you first signing the ACORD license agreement related to such assets. ... not all ACORD programs offer access to all ACORD forms, standards and other assets" ([S15](#sources)). The licence agreements are supplied by Member Services on request and are not published ([S15](#sources)).

**Programmes that fit a broker platform, with published fees** (Terms of Program Membership version 2025-10-27, [S15](#sources); programme pages [S16](#sources), [S17](#sources), [S18](#sources), [S19](#sources)):

| Programme | Intended for | Standards package | Fee as published |
|---|---|---|---|
| P&C Insurance Broker/Agent Electronic Standards Membership | "Insurance Brokers, Agencies, MGAs, and Wholesalers in the business of distributing property & casualty insurance policies" | P&C XML schemas and specifications, implementation guides, AL3, NGDS; Test Harness and Certifications; "ACORD Branding and Logo Usage" | USD 187.46 per million of gross revenue, USD 13,519 minimum per term (A.5) |
| GRLC Broker/Agent Electronic Standards Membership | brokers "distributing reinsurance and large commercial policies" | GRLC XML schemas and specifications, implementation guides, GRLC Data Dictionary, NGDS; Test Harness and Certifications; branding and logo usage | USD 187.46 per million of gross revenue, USD 13,519 minimum (A.7, "Reinsurance Broker/Agent") |
| Solution Provider Electronic Standards Associate Membership | "established vendor organizations which provide solutions to the insurance industry" | P&C, L&A and GRLC packages, AL3, "AML Schema and Specifications for Australia, New Zealand and South Africa", implementation guides, GRLC Data Dictionary, NGDS | "Please contact ACORD Member Services to discuss pricing options" (A.8) |
| APAC Standards Pilot Program | "solution providers domiciled or focused within APAC with a total revenue of $5 million or less ... with no prior ACORD membership in the past five years" | "Access to ACORD APAC Standards", NGDS, "Access to all other lines of business/regional standards in all formats", Standards Project Group observer rights; Test Harness "may be an additional fee" | USD 2,500 for a one-year trial, creditable toward full membership ([S19](#sources)) |
| Standards License for London Market Associations | members of IUA, LIIBA and LMA | "a limited license to use the ACORD Global Reinsurance & Large Commercial Standards" | not published ([S16](#sources)) |

Membership is a binding contract construed under New Jersey law, renews annually, requires audited or unaudited financials on request for fee calculation, and carries a non-disparagement clause covering "any ACORD trademark" (D.2, D.6, D.7, D.10, [S15](#sources)).

**Claiming compatibility.** ACORD offers a formal route and a trademark constraint:

- "ACORD Testing & Certification allows organizations to demonstrate proper implementation of ACORD messages. ... After a successful use of the test harness, organizations can claim their ACORD System Certified credential". Certification requires evidence of Test Runs submitted through a service desk that "is available to ACORD Members", sign-off by the Standards team, and "any associated invoicing" settled before the badge is claimed. The Test Harness covers GRLC XML, P&C XML, L&A XML, Employee Benefits XML, AMS and DRI ([S20](#sources)). The credential "Certifies organizations for proper implementation of ACORD messages for specific insurance processes within their systems" ([S20](#sources)).
- "ACORD, ACORD ObjX, ACORD OLifE, AL3, ACORD Advantage, ACORD XML, and 'Association for Cooperative Operations Research and Development' are trademarks of ACORD." ([S21](#sources)) "ACORD Branding and Logo Usage" is listed as a member benefit on each standards membership page ([S16](#sources), [S17](#sources), [S18](#sources)).
- ACORD's antitrust policy commits it to state on every published standard that "Implementation and use of the standard is voluntary" and that "ACORD does not endorse any product or service designed or built to the standard" ([S14](#sources)).

Taken together [sourced]: the schemas are contractually licensed, the certified-compatibility badge is a paid member process, and the words used to say "ACORD" are trademarks whose branding use is a member benefit.

## What is freely implementable, if anything (sourced)

- **No ACORD data standard is published for free download to non-members.** Every standards page checked routes access through "the proper ACORD membership or participation program" ([S1](#sources), [S2](#sources), [S3](#sources), [S7](#sources), [S8](#sources)). The one "free" statement on those pages is "Standards Training Materials ... are free to download for all ACORD members" — members only ([S2](#sources)). Implementation tooling is likewise "complimentary to ACORD members" ([S25](#sources)).
- **What is public without membership:** the catalogue pages and release lists; the P&C transaction-specification titles; the GRLC FAQs, which give business-level definitions of Placing, EBOT, ECOT, Claim Movement and the acknowledgement and query flows ([S6](#sources)); the NGDS "Getting Started" fact sheet, for "ACORD members and non-members alike" ([S9](#sources)); the ACORD Forms Index of titles and numbers ([S10](#sources)); the Terms of Program Membership ([S15](#sources)); the Standards Programs General Guidelines ([S14](#sources)).
- **Forms are licensed, not free:** "ACORD Forms may only be used with a valid license" and vendor-embedded forms still require "a license directly from ACORD" ([S11](#sources)). The complimentary Big "I" and PIA end-user licence is only for members of those two US agent associations with P&C revenue under USD 50 million ([S22](#sources), [S23](#sources)).
- **Reference Architecture:** purchasable by non-members ([S13](#sources)) — paid, not free, and not a standard ([S14](#sources)).
- **Voluntariness is not a licence.** ACORD's "entirely voluntary" clause ([S14](#sources)) is an antitrust commitment that no one is coerced into using the standards; it says nothing about copying the schemas without a licence, and the Terms of Use say "No content from the ACORD website may be copied, reproduced, republished ... except as otherwise explicitly stated in writing by ACORD" ([S21](#sources)).

Answer to "is anything freely implementable": the public business-level vocabulary (message names, process stages, the acknowledgement and query pattern described in the GRLC FAQs) can be read and learned from without a contract. The schemas, codelists, data dictionaries and implementation guides that would make a system "ACORD-compatible" in any testable sense cannot be obtained without a membership or licence agreement, on the sources checked.

## An honest compatibility scope for a Lao-market broker platform at v0.1 (recommendation)

Reasoned from the sources above; labelled as recommendation.

1. **Claim nothing ACORD-branded at v0.1.** BizTrust has no membership, no licence, no Test Harness run and no badge. Using "ACORD-compatible", "ACORD XML", "AL3" or the ACORD logo in product, documentation or sales material would assert a trademark-bearing claim the platform cannot evidence ([S20](#sources), [S21](#sources)). The correct v0.1 wording is "designed so that an ACORD mapping adapter can be added later", which is already the position of section 14 ("ACORD compatibility should be implemented as a mapping layer where commercially useful. ACORD is not the BizTrust database model.").
2. **No membership is needed for v0.1, and the sources support saying so.** Implementation is voluntary ([S14](#sources)); no Lao insurer, regulator or partner requirement to exchange ACORD messages has been supplied to this repository (see Unverified items); and the smallest published entry point that would give a Lao vendor the Asia-Pacific and NGDS schemas is the USD 2,500 APAC Standards Pilot ([S19](#sources)), which is a decision for the operator when a counterparty actually asks for ACORD messages — not before.
3. **If and when a counterparty asks, the families that matter are, in order:** Asia-Pacific General Insurance XML (regional; covers the policy and claims lifecycle and the bordereaux-style reporting BizTrust already lists as unresolved in section 18) ([S7](#sources)); GRLC Placing (only if BizTrust places large commercial or facultative risk into the London or international market) ([S3](#sources), [S5](#sources)); NGDS JSON for API-shaped exchange ([S8](#sources)). The US P&C XML/AL3 family and ACORD Forms carry US state-level content and should not be a target ([S2](#sources), [S10](#sources)).
4. **Travel stays out of any ACORD claim.** No public ACORD page names travel; treat travel as a BizTrust canonical product with no ACORD mapping until the codelists are inspected under a licence.
5. **Architecturally, keep the adapter seam and nothing more.** Section 14's canonical model plus per-provider adapter is the mirror image of what ACORD's own FAQ tells implementers: "treat the GRLC schema as your master reference model ... implement transformation logic ... validate the output using the GRLC Test Harness" ([S6](#sources)). BizTrust keeps its own canonical model and maps outward, so that a future ACORD adapter is a licensed add-on rather than a schema rewrite.
6. **Record the trigger, not the intent.** Section 18 should close the bullet by naming what would reopen it: a signed insurer or reinsurer integration requirement that specifies ACORD messages, or an operator decision to seek ACORD System Certification. Either triggers a membership and licence procurement task with the fee table above as the cost baseline.

## One-paragraph recommendation for section 18

Replace the open bullet "ACORD licensing and exact compatibility scope" with a resolved statement to this effect: *ACORD data standards (P&C XML/AL3, GRLC, Asia-Pacific General Insurance, NGDS) are available only under ACORD membership or licence agreements; "ACORD System Certified" is a paid member process; and "ACORD", "ACORD XML" and "AL3" are ACORD trademarks. ACORD states that implementation of its standards is voluntary and that it endorses no product built to them. BizTrust v0.1 therefore claims no ACORD compatibility, holds no ACORD membership or licence, and uses no ACORD marks; the canonical model and adapter boundary in section 14 are retained so that a licensed ACORD mapping adapter (Asia-Pacific General Insurance XML first, GRLC Placing only for London-market placement, NGDS for API exchange) can be added when a counterparty contract requires ACORD messages or the operator elects to pursue certification. Travel products have no identified ACORD mapping. The entry cost, as published on 2026-09-05, is USD 2,500 for the APAC Standards Pilot (eligible APAC solution providers under USD 5 million revenue) or USD 13,519 minimum per term for a broker/agent standards membership; the licence agreements themselves are unpublished and must be obtained from ACORD Member Services before any commitment.* Source: `docs/research/arch-001a/acord-scope.md`.

## Unverified items

Not established on any first-party ACORD page checked on 2026-09-05. Each is a question for ACORD Member Services or for the operator, not a fact.

1. **Text of the standards licence agreements.** ACORD says they exist and must be signed before access ([S15](#sources), D.1) but does not publish them. Redistribution rights, sublicensing to BizTrust tenants, and whether a "compatible" claim is permitted without certification are therefore unverified.
2. **Whether the Solution Provider or APAC Pilot programmes admit an organisation that is both a broker and a software vendor**, and whether a Lao PDR entity counts as "domiciled or focused within APAC" ([S19](#sources)). Eligibility is stated in one sentence with no country list.
3. **Whether a travel line-of-business code exists in the P&C or Asia-Pacific codelists.** The codelists sit behind `standards.acord.org`, which rendered without content to a non-member on 2026-09-05 ([S2](#sources)).
4. **Whether any Lao insurer, reinsurer, regulator or platform partner requires ACORD messages.** Nothing in this repository or on ACORD's site says so. ACORD's member directory was not searched for Lao entities; a directory listing would not establish a requirement in any case.
5. **Which format a counterparty would use** — GRLC Gen 2 JSON, GRLC XML 2016.10, Asia-Pacific GI XML, or NGDS. The families overlap; the choice is dictated by the counterparty, not by ACORD.
6. **The "Standards License for London Market Associations"** — scope and cost are not published ([S16](#sources)).
7. **The full membership benefit grid.** The public PDF ([S24](#sources)) lists benefit rows (schemas by line of business, cross-programme reporting, implementation guides, Asia-Pacific GI, AL3 "Requires AL3 License and Carrier P&C Standards Membership", forms, Reference Architecture facets "Member discount applies") but its column headings did not extract legibly, so which programme receives which row is taken from the programme pages, not from the grid.
8. **ACORD's Intellectual Property Rights Policy.** The Terms of Use refer to it on a "Governing Documents page" ([S21](#sources)); that URL returned 404 on 2026-09-05, so the policy text was not read.

## Sources

All checked 2026-09-05. Pages were fetched directly from `acord.org`; text was read from the fetched HTML or PDF. Where a page is member-gated that is noted.

- **S1** ACORD Data Standards (catalogue and access statement) — https://www.acord.org/standards-architecture/acord-data-standards
- **S2** Property & Casualty Data Standards — https://www.acord.org/standards-architecture/acord-data-standards/Property_Casualty_Data_Standards (codelists link to https://standards.acord.org/#/pc/codelists, member-gated)
- **S3** Reinsurance & Large Commercial (GRLC) Data Standards — https://www.acord.org/standards-architecture/acord-data-standards/Global_Reinsurance_Data_Standards
- **S4** News, 10 Apr 2025, "ACORD Launches 'GRLC Generation 2.0' Data Standards" — https://www.acord.org/ACORD-about/acord-news/2025/04/10/acord-launches-grlc-generation-2.0-data-standards-to-support-digitalization-throughout-global-(re)insurance-industry
- **S5** News, 29 Sep 2021, "ACORD Releases (Re)insurance Data Standards for Electronic Placing" — https://www.acord.org/ACORD-about/acord-news/2021/09/29/acord-releases-(re)insurance-data-standards-for-electronic-placing
- **S6** GRLC Frequently Asked Questions — https://www.acord.org/standards-architecture/acord-data-standards/Global_Reinsurance_Data_Standards/grlc-faqs
- **S7** Asia-Pacific Data Standards — https://www.acord.org/standards-architecture/acord-data-standards/Asia_Pacific_Data_Standards
- **S8** Next-Generation Digital Standards — https://www.acord.org/standards-architecture/acord-data-standards/next-generation-digital-standards
- **S9** News, 29 Jul 2026, "Getting Started with Next-Generation Digital Standards" — https://www.acord.org/news-detail/2026/07/29/getting-started-with-next-generation-digital-standards
- **S10** ACORD Forms Index (PDF, rev. 8/10/2026) — https://www.acord.org/docs/default-source/forms/forms_index.pdf
- **S11** Forms FAQ — https://www.acord.org/forms-pages/acord-forms/forms-faq
- **S12** Delegated Authority Standards — https://www.acord.org/standards-architecture/acord-data-standards/multi-functional-standards/delegated-authority-standards
- **S13** ACORD Reference Architecture — https://www.acord.org/standards-architecture/reference-architecture
- **S14** ACORD Standards Programs General Guidelines & Procedures, effective 4 Apr 2018 (PDF), including Appendix 1 Antitrust/Competition Law Policy, sections B "Open Access to the Standards-Setting Process" and D "Voluntary Use of Standards" — https://www.acord.org/docs/default-source/governance/acord-standards-programs-general-guidelines-procedures.pdf?sfvrsn=8b33ac55_10
- **S15** Terms of Program Membership, version 2025-10-27 (PDF) — https://www.acord.org/static/legal/terms_of_program_membership.pdf
- **S16** Programs & Offerings (membership categories; London Market Associations licence; Forms End User Licensing Program) — https://www.acord.org/membership-participation/programs-offerings
- **S17** P&C Broker/Agent Standards Membership — https://www.acord.org/membership-participation/programs-offerings/p-c-broker-agent-standards-membership
- **S18** GRLC Broker/Agent Standards Membership — https://www.acord.org/membership-participation/programs-offerings/grlc-broker-agent-standards-membership ; Solution Provider Membership — https://www.acord.org/membership-participation/programs-offerings/solution-provider-standards-membership
- **S19** APAC Standards Pilot Program — https://www.acord.org/membership-participation/programs-offerings/apac-standards-pilot-program
- **S20** Testing & Certification — https://www.acord.org/standards-architecture/implement-standards/testing-certification ; ACORD Credentials — https://www.acord.org/membership-participation/awards-certifications/digital-credentials
- **S21** Terms of Use (trademark and copyright notices) — https://www.acord.org/terms-of-use
- **S22** Forms Subscriptions & Licensing — https://www.acord.org/forms-pages/forms-participation-programs
- **S23** News, 4 Dec 2025, "ACORD License Available for Big 'I' Members" — https://www.acord.org/ACORD-about/acord-news/2025/12/04/acord-license-available-for-big-i-members
- **S24** Membership asset grid (PDF) — https://www.acord.org/docs/default-source/membership-programs-info/membershipassetgrid.pdf
- **S25** Implementation Resources — https://www.acord.org/standards-architecture/implement-standards

Pages that could not be read: `https://www.acord.org/ACORD-about/governing-documents` (404) and the delegated-authority "license-agreement" URL surfaced by search (404).

<!-- agent: researcher (wayfinder research, 2026-09-05) -->
