# Payment reconciliation and bank-statement standards: primary-source pack for the P2 manual

| Field | Value |
|---|---|
| Ticket | [#163 [GUIDE-V2] Research: payment reconciliation and bank-statement standards from primary sources](https://github.com/bstBizEra/biztrust_guide/issues/163) (parent [#153](https://github.com/bstBizEra/biztrust_guide/issues/153); blocks [#168](https://github.com/bstBizEra/biztrust_guide/issues/168)) |
| Date every URL below was checked | 2026-09-06 |
| Prepared by | research agent, for the engineer rewriting the P2 manual (#168) and for the legal seat where marked |
| Status | Complete for the four sources named in the ticket; gaps are marked `UNVERIFIED` or `UNVERIFIABLE` |

This file records what three first-party publishers say (ISO 20022 Registration Authority at iso20022.org, PCI Security Standards Council at pcisecuritystandards.org, Bank of the Lao PDR at bol.gov.la) and nothing else. It draws **no conclusion of law**. Where a sentence would need a lawyer, an assessor or a bank contract to become true for BizTrust, it says so.

## 1. Ticket

Issue #163 asks: P2E reconciliation compares BizTrust, the payment provider, the bank statement and the carrier settlement. From primary sources: the purposes of ISO 20022 camt.052, camt.053 and camt.054; PCI DSS scope statements for what a platform may store when it orchestrates card payments; the Bank of the Lao PDR payment-system instruments already found under the contract map's Lao research (#100, cited rather than repeated); and any first-party documentation of QR payment schemes operating in Laos. Exact URLs, date checked, no conclusion of law.

## 2. Question

When the P2 manual names a reconciliation status, which published standard (if any) defines the fact behind it, what does a bank statement entry actually carry that a matcher can key on, what may a platform that orchestrates card payments without storing card data keep in its own records, and which Lao rails and instruments does the Bank of the Lao PDR itself publish?

Repository vocabulary used here comes from `docs/architecture/FLOWS.md` section 12 (payment state) and 12A (client-money and reconciliation dimensions), `docs/architecture/BIZTRUST-ARCH-001.md` section 13 (financial boundary), and `docs/architecture/DOMAIN_MODEL.md` section 2.3 (`BANK_TRANSACTION`, `STATEMENT_ITEM`, `RECONCILIATION_ITEM`).

## 3. ISO 20022 cash-management messages

### 3.1 Which document these words come from

The ISO 20022 Registration Authority publishes the Message Definition Report (MDR) for the Bank-to-Customer Cash Management message set on iso20022.org. The copy read for this file is **"Bank-to-Customer Cash Management - Maintenance 2020 - 2021, Message Definition Report - Part 2, For evaluation by the Payments SEG", December 2020** (S1). It carries the identifiers `DRAFT1camt.052.001.09`, `DRAFT1camt.053.001.09` and `DRAFT1camt.054.001.09`. Its overview sentence is:

> "The Bank-to-Customer message set provides the messages used to request and provide account information for reconciliation and cash positioning between an account servicer and its customer." (S1, section 1)

The live catalogue pages (`iso20022.org/iso-20022-message-definitions` and `iso20022.org/catalogue-messages/iso-20022-messages-archive`) did not respond from the research environment on 2026-09-06 (timeouts and connection resets on every attempt, see section 8). The message definitions below are therefore quoted from the iso20022.org-hosted MDR, which is the same publisher. Whether the wording of the finally published V09 differs from this SEG-review draft, and which later versions (V10 onward) exist in the catalogue today, is `UNVERIFIED`.

### 3.2 Purpose of each message, in the publisher's words

| Message | Name | Scope (S1, "MessageDefinition Functionality") | Usage points that matter for reconciliation (S1) |
|---|---|---|---|
| camt.052 | BankToCustomerAccountReport | "sent by the account servicer to an account owner or to a party authorised by the account owner to receive the message. It can be used to inform the account owner, or authorised party, of the entries reported to the account, and/or to provide the owner with balance information on the account at a given point in time." | "provides information for cash management and/or reconciliation. It can be used to: - report pending and booked items; - provide balance information." And: "For a statement, the Bank-to-Customer Account Statement message should be used." |
| camt.053 | BankToCustomerStatement | "sent by the account servicer to an account owner or to a party authorised by the account owner to receive the message. It is used to inform the account owner, or authorised party, of the entries booked to the account, and to provide the owner with balance information on the account at a given point in time." | "provides information for cash management and/or reconciliation. It contains information on booked entries only." And: "Depending on services and schedule agreed between banks and their customers, statements may be generated and exchanged accordingly, for example for intraday or prior day periods." |
| camt.054 | BankToCustomerDebitCreditNotification | "sent by the account servicer to an account owner or to a party authorised by the account owner to receive the message. It can be used to inform the account owner, or authorised party, of single or multiple debit and/or credit entries reported to the account." | "can be used to: - report pending and booked items; - notify one or more debit entries; - notify one or more credit entries; - notify a combination of debit and credit entries." And: "It does not contain balance information." |

All three: "It can include underlying details of transactions that have been included in the entry." and "It is possible that the receiver of the message is not the account owner, but a party entitled ... to receive the account information (also known as recipient)." (S1). The companion request message is camt.060 AccountReportingRequest, "used to ask the account servicing institution to send a report ... in a BankToCustomerAccountReport (camt.052), a BankToCustomerStatement (camt.053) or a BankToCustomerDebitCreditNotification (camt.054)" (S1, section 1.1).

Each message is built from three blocks: `GroupHeader`, then `Report` (camt.052, "Reports on a cash account"), `Statement` (camt.053, "Reports on booked entries and balances for a cash account") or `Notification` (camt.054, "Notifies debit and credit entries for the account"), then `SupplementaryData` (S1, "Outline" of each message).

### 3.3 What a statement entry carries

The entry component is `ReportEntry11` (S1, section 6.1.9.2, "Provides further details on an entry in the report."). The elements a matcher can key on, with the publisher's definitions:

| Element (XML tag) | Definition in S1 |
|---|---|
| EntryReference `<NtryRef>` | "Unique reference for the entry." |
| Amount `<Amt>` | "Amount of money in the cash entry." |
| CreditDebitIndicator `<CdtDbtInd>` | "Indicates whether the entry is a credit or a debit entry." |
| ReversalIndicator `<RvslInd>` | "Indicates whether or not the entry is the result of a reversal." Usage: "This element should only be present if the entry is the result of a reversal." |
| Status `<Sts>` | "Status of an entry on the books of the account servicer." Coded through `EntryStatus1Choice`: "Specifies the status of an entry on the books of the account servicer." with a `Code` from the external code set `ExternalEntryStatus1Code` or a `Proprietary` text (S1, 6.1.28.2). |
| BookingDate `<BookgDt>` | "Date and time when an entry is posted to an account on the account servicer's books." Usage: "Booking date is the expected booking date, unless the status is booked, in which case it is the actual booking date." |
| ValueDate `<ValDt>` | "Date and time at which assets become available to the account owner in case of a credit entry, or cease to be available to the account owner in case of a debit entry." Usage: "If entry status is pending and value date is present, then the value date refers to an expected/requested value date." |
| AccountServicerReference `<AcctSvcrRef>` | "Unique reference as assigned by the account servicing institution to unambiguously identify the entry." |
| BankTransactionCode `<BkTxCd>` | "Set of elements used to fully identify the type of underlying transaction resulting in an entry." |
| AmountDetails, Charges, Interest | Original amount, charges "pre-advised or included in the entry amount", and interest "included in the entry amount"; the Usage notes say these entry-level components are for "batch or aggregate bookings". |
| CardTransaction `<CardTx>` | "Provides details of the card transaction included in the entry amount, when globalised by the account servicer." |
| EntryDetails `<NtryDtls>` | "Provides details on the entry." (`EntryDetails10`, whose `TransactionDetails` is `EntryTransaction11`, S1 6.1.9.3 and 6.1.9.4.) |

Inside the transaction details, the references block includes `EndToEndIdentification <EndToEndId>`:

> "Unique identification, as assigned by the initiating party, to unambiguously identify the transaction. This identification is passed on, unchanged, throughout the entire end-to-end chain. Usage: The end-to-end identification can be used for reconciliation or to link tasks relating to the transaction. It can be included in several messages related to the transaction." (S1, 6.1.9.3.1.5)

Balances are carried in `CashBalance8` ("Set of elements used to define the balance details.") whose `Type` "Specifies the nature of a balance." through `BalanceType13` with a `Code` from an external code set or a `Proprietary` text, plus `Amount`, `CreditDebitIndicator`, `Date` and `Availability` (S1, 6.1.5). The balance and entry-status code values themselves (for example the opening-booked and closing-booked codes) live in the ISO 20022 external code sets, which were not retrieved; their current list is `UNVERIFIED` here. The Bank of the Lao PDR's own message standard (S9 below) shows the comments "OPBD - balance at the business day opening" and "CLBD -- closing booked balance" against its camt.053 balance-type field, which is the only first-party rendering of those codes found for this file.

## 4. PCI DSS scope for a platform that orchestrates card payments without storing card data

### 4.1 Definitions the scope statements rest on (PCI SSC Glossary, S5)

- **Account Data**: "Account data consists of cardholder data and/or sensitive authentication data."
- **Cardholder Data (CHD)**: "At a minimum, cardholder data consists of the full PAN. Cardholder data may also appear in the form of the full PAN plus any of the following: cardholder name, expiration date and/or service code."
- **Sensitive Authentication Data (SAD)**: "Security-related information used to authenticate cardholders and/or authorize payment card transactions. This information includes, but is not limited to, card verification codes, full track data (from magnetic stripe or equivalent on a chip), PINs, and PIN blocks."
- **Truncation**: "Method of rendering a full PAN unreadable by removing a segment of PAN data. Truncation relates to protection of PAN when electronically stored, processed, or transmitted."
- **Service Provider**: "Business entity that is not a payment brand, directly involved in the processing, storage, or transmission of cardholder data (CHD) and/or sensitive authentication data (SAD) on behalf of another entity. This includes payment gateways, payment service providers (PSPs), and independent sales organizations (ISOs). This also includes companies that provide services that control or could impact the security of CHD and/or SAD."
- **Merchant**: "any entity that accepts payment cards bearing the logos of any PCI SSC Participating Payment Brand as payment for goods and/or services. A merchant that accepts payment cards as payment for goods and/or services can also be a service provider, if the services sold result in storing, processing, or transmitting cardholder data on behalf of other merchants or service providers."

### 4.2 Outsourcing does not remove the entity from PCI DSS (PCI SSC FAQ, S6)

Question: "Does PCI DSS apply to merchants who outsource all payment processing operations and never store, process or transmit cardholder data?" Answer, verbatim:

> "Yes. PCI DSS is intended for any entity that stores, processes, or transmits cardholder data — regardless of whether these activities are conducted directly or by a third-party service provider. When a merchant outsources its payment processing to a third party and does not store, process, or transmit cardholder data, many PCI DSS requirements may not apply directly to the merchant's environment. However, this does not remove the merchant's responsibility to ensure account data is properly protected by the third party."

The FAQ then lists what merchants "remain responsible for": "Ensuring the provider is PCI DSS compliant for the services offered", "Maintaining written agreements with the provider that include acknowledgment of their responsibilities (Requirement 12.8.2)", "Monitoring the provider's compliance status at least annually (Requirement 12.8.4)", "Clearly defining and understanding any shared responsibilities", and closes: "Merchants are still required to validate PCI DSS compliance, typically through a Self-Assessment Questionnaire (such as SAQ A). Merchants should confirm their compliance obligations with the organization(s) that manage their compliance program—such as their acquirer or payment brand—also referred to as compliance-accepting entities." (The page shows no article number or date.)

### 4.3 Scoping principle and third parties (Information Supplement, S7)

"Guidance for PCI DSS Scoping and Network Segmentation", v1.1, May 2017:

> "When it comes to scoping for PCI DSS, the best practice approach is to start with the assumption that everything is in scope until verified otherwise." (section 1)

> "Other methods may also be effective at reducing the number of systems to which PCI DSS controls apply and/or the size of the CDE (such as outsourcing to a third-party service provider or using a PCI-listed P2PE solution). However, these methods are not the subject of this paper." (section 1)

> "Similarly, if an entity outsources in-scope functions or facilities to a third party, or utilizes a third-party service that impacts how it meets PCI DSS requirements, the entity will need to work with the third party to ensure the applicable aspects of the service are included in scope for PCI DSS--either for the entity or the service provider. It is also important for both parties to clearly understand which PCI DSS requirements are being provided by the service provider and which are the responsibility of the entity using the service. See PCI DSS Requirement 12.8." (section 2.1)

The document states on every page: "The intent of this document is to provide supplemental information. Information provided here does not replace or supersede requirements in any PCI SSC Standard." PCI SSC has since published a further supplement on modern network architectures (announced on its blog, S7a); its text was not retrieved and is `UNVERIFIED`.

### 4.4 Embedded page versus redirect (FAQ 1588, February 2025, S8)

"How does an e-commerce merchant meet the SAQ A eligibility criteria for scripts?" The FAQ quotes the SAQ A r1 criterion "The merchant has confirmed that their site is not susceptible to attacks from scripts that could affect the merchant's e-commerce system(s)." and states:

> "The above SAQ A eligibility criteria only applies to e-commerce merchants with a webpage that includes a TPSP's/payment processor's embedded payment page/form (for example, one or more inline frame(s) (iframes))."

> "The above SAQ A eligibility criteria does not apply to e-commerce merchants with a webpage that redirects customers from the merchant's webpage to a TPSP/payment processor (for example, including but not limited to, with an HTTP 30x redirect, a meta redirect tag, or a JavaScript redirect) or e-commerce merchants that fully outsource payment functions to a TPSP/payment processor (for example, by providing customers with an email with a link to a TPSP's website to pay)."

It ends: "Merchants should continue to consult with their compliance-accepting entity ... to determine if the merchant is required to submit an SAQ, and if so, which SAQ is appropriate for the merchant's environment."

### 4.5 What may sit in a reconciliation record: truncated PAN (FAQ 1117, September 2021, S8a)

"Are truncated Primary Account Numbers (PAN) required to be protected in accordance with PCI DSS?"

> "Systems that store, process, or transmit only truncated PANs (where a segment of PAN data has been permanently removed) may be considered out of scope for PCI DSS if those systems are adequately segmented from the cardholder data environment, and do not otherwise store, process, or transmit cardholder data or sensitive authentication data. This applies to any truncation that meets the acceptable PAN truncation formats specified in FAQ 1091. However, the system performing the truncation of the PANs, as well as any connected systems and networks, would be in scope for PCI DSS."

and: "If the same PAN is truncated using more than one truncation format ... additional controls should be in place to ensure that the truncated versions cannot be correlated to reconstruct additional digits of the original PAN." FAQ 1091 (acceptable truncation formats) was not retrieved; its current table is `UNVERIFIED`.

### 4.6 What these statements do and do not settle

They settle that (a) a platform whose PSP holds the card data is not thereby outside PCI DSS, (b) the platform's own obligations are at minimum the Requirement 12.8 items and a validation route agreed with its compliance-accepting entity, (c) the way the card form reaches the customer (iframe, redirect, emailed link) changes the SAQ A criteria that apply, and (d) a record holding only a properly truncated PAN, segmented from any CDE, "may be considered out of scope". They do not settle which SAQ BizTrust must file, whether BizTrust is a merchant, a service provider or both for a given tenant, or whether a particular reconciliation store is "adequately segmented"; those are the acquirer's, the payment brand's or an assessor's calls. No PCI DSS standard text itself (v4.0.1) was retrieved, because the document library serves it behind a licence acknowledgement; every quotation above is from the FAQ, glossary or an information supplement.

## 5. Lao payment rails

### 5.1 Instruments already located under #100 (cite, do not repeat)

The Lao research pack at `docs/research/arch-001a/lao-insurance-regulation.md` on branch `research/lao-insurance-regulation` (S10) already locates, as its items S20 to S22, the Law on Payment System (Amended) No. 45/NA of 20 November 2023 (BOL unofficial English translation), the Law on Foreign Exchange Management (Amended) No. 15/NA and the AML/CFT Law (Amended) No. 64/NA, and quotes from the Payment System Law its Art. 16 (electronic money "shall be in KIP"), Art. 29 to 30 (payment service providers and agents) and Art. 39 (records kept "at least for a period of Ten years"). This file adds only the articles of the same BOL translation that bear on rails and standards:

- Art. 3(3): "Interoperability means the interlinking between payment systems of the similar or different features to facilitate payment service and enable interoperable operation;" Art. 3(9) defines "Outsourcing Service Provider" as "a legal entity hired by Retail Payment System Operator or Payment Service Provider to support in payment services operation and to partially manage the services on their behalf, such as information and technology system, operation, and key services." Art. 3(10): "Payment Business Operator means Retail Payment System Operator and Payment Service Provider authorized by the Bank of the Lao PDR". (S11)
- Art. 15 (card): "Standards, principles, scope of use, and supervision of card payment service are provided in a specific regulation." Art. 17 (payment channel): "Standards of each payment channel are provided in a specific regulation." (S11)
- Art. 39 (information keeping) as quoted in #100; Art. 40 (audit): "In every year, Payment business operator shall be audited by an external audit firm to certify the accuracy and completeness of accounting, financial reports, internal control system, and effectiveness of operation". (S11)
- The 2023 English translation's Art. 3 does not carry a QR-code definition. The superseded 2017 Law on Payment System (BOL English, S12) did: "QR code (Quick Response Code) means a symbol or code certifying the identity for conducting electronic financial transaction". Whether the Lao text of the 2023 law defines it is `UNVERIFIED`.

Whether BizTrust, a tenant broker, or neither is a "Payment Business Operator" under this law is a question for the legal seat; #100 section 5 already lists it.

### 5.2 What BOL itself publishes on Lao QR (first-party, bol.gov.la)

| Item | What it says (verbatim or close paraphrase) | Source |
|---|---|---|
| Launch notice, 29 January 2020 | "On 29 January 2020, the Bank of the Lao PDR has held an official launch of Lao QR Code ... The official launch of Lao QR code is of particular significance in the development of domestic payment in the country to ensure the modes of payment convenient, safe and secure and also in line with pace of international payment development. It is also intended to implement the financial sector development strategy towards a cashless society in Laos". Names Union Pay and the World Bank Group among attendees. | S13 |
| Mobile money transfer application, 8 December 2020 | "The mobile money transfer in the form of QR Code will be implemented by two major banks - Lao Development Bank (LDB) and ST Bank - Whereas the mobile money transfer in the form of Account Fund Transfer will be implemented by five major banks"; the switch is "National Payment Network Co., Ltd. (LAPNet) under the supervision of Bank of the Lao PDR (BOL)". | S14 |
| Cross-border QR with Cambodia, 18 August 2023 | "Official Launch of Cross-Border QR Payment: KHQR scan LAOQR which the payment system that will use local currencies (Lao Kip and Khmer Riel) to pay for goods and services via QR code." "The cross-border QR payment linkages Laos and Cambodia through a switching (LAPNet) to sponsoring bank (ACLEDA Cambodia) model." Eight Lao service banks are named for phase one; phase two (LAOQR scan KHQR) was "planning to launch". | S15 |
| "Lao Payment Standards" page (Lao-language site) | Lists three BOL decisions, each dated 27-01-2026: (1) ຂໍ້ຕົກລົງວ່າດ້ວຍ ມາດຕະຖານລາວຄິວອາ ເພື່ອການຊໍາລະ, "Decision on the Lao QR standard for payment" (agent's translation of the title); (2) a decision on the Bank Identification Number standard for card issuers ("Bank Identification Number:BIN for Card Issuer" in the page's own English); (3) ຂໍ້ຕົກລົງວ່າດ້ວຍການຮັບຮອງ ແລະ ປະກາດນຳໃຊ້ມາດຕະຖານຂໍ້ຄວາມດ້ານການຊຳລະຂອງ ສປປ ລາວ, in the page's own English "the Standard of Message Specification for Payment Systems". The English-language page of the same name shows an empty table. | S16, S16a |
| Lao QR standard decision (PDF, 48 pages) | Scanned; the PDF has no text layer, so its content beyond the title and date is `UNVERIFIABLE` by this research. A Lao reader with the file can extract the QR payload specification it presumably contains. | S17 |
| Lao payment message standard (PDF, 340 pages, cover "ທັນວາ 2023", December 2023) | Section I.2 states, in Lao, that the Lao payment message standard is the development and use of payment transaction messages that follow the international standard (ISO 20022) and the specifications of the Bank of the Lao PDR; section I.3(1) defines "ມາດຕະຖານ ISO 20022" as the international standard for exchanging electronic payment transaction data between financial institutions, payment service users and other payment-system participants, in XML form. Section V lists "BankToCustomer AccountReport = camt.052.001.02", "BankToCustomerStatement = camt.053.001.02" and "BankToCustomerDebitCredit Notification = camt.054.001.02", and describes the camt.052 structure as GroupHeader, Report (with Identification, ElectronicSequenceNumber, FromToDate, Account, Balance, TransactionSummary, Entry with Status and BankTransactionCode ...) The document also covers pacs.002/003/004/007/008/009 and pain.001/002/007/008. The paraphrases of the Lao text are the agent's; treat them as `UNVERIFIED` until a Lao reader confirms. | S18 |
| Licensed payment service types | The BOL page "Licensed payment Service Providers and types of Payment Service" lists four types: "Card Payment", "Electronic Money", "Electronic Acceptance", "Electronic Money Transfer Services". | S19 |

The BOL English pages "Retail Payment Systems", "Systemic Importance Payment Systems", "Domestic Payment Systems Development" and "Payment Channels" each rendered an empty table on 2026-09-06 (S16b). LAPNet's own site was not consulted because it is not the Bank of the Lao PDR; any LAPNet-published QR or switch specification is `UNVERIFIED` for this file. No BOL page found names EMVCo or an EMV QR merchant-presented specification as the basis of Lao QR; that basis is `UNVERIFIABLE` from bol.gov.la text (it may be inside S17).

## 6. Statuses and sources

The operator's roadmap (`BIZTRUST-ROADMAP-001`, to be imported as `docs/research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md` by the first record ticket) is not on any branch of the repository as of 2026-09-06, so its section 6 status names cannot be quoted here. The statuses below are the repository's current ones: the reconciliation dimension and the neighbouring dimensions of `FLOWS.md` section 12A, and the payment states of section 12. #168 maps the roadmap's names onto these.

| Status (FLOWS.md) | Dimension | Defined by which source | Note |
|---|---|---|---|
| matched | Reconciliation (12A) | BizTrust-defined | ISO 20022 supplies the keys, not the verdict: `EndToEndId` "can be used for reconciliation", `AcctSvcrRef`, `NtryRef`, `Amt`, `CdtDbtInd` (S1). |
| timing difference | Reconciliation (12A) | BizTrust-defined | The facts it rests on are standard: camt.053 carries "booked entries only", camt.052/054 may "report pending and booked items"; each entry carries `BookgDt` and `ValDt` separately and a `Sts` code (S1). |
| unexplained difference | Reconciliation (12A) | BizTrust-defined | No source defines it; ARCH-001 section 13 requires the ledger to distinguish "unexplained differences" and forbids settlement completion "while required differences remain unowned". |
| resolved | Reconciliation (12A) | BizTrust-defined | Evidence-bound by 12A's "Reconciliation owner and evidence". |
| initiated | External movement (12A) | BizTrust-defined | Corresponds to a payment instruction (pain.001 in ISO 20022 terms, not read for this file). |
| authorized, captured | External movement (12A); AUTHORIZED, CAPTURED in section 12 | PSP / card-scheme vocabulary, `UNVERIFIED` | Not defined by any of the three publishers read; PCI SSC uses "authorize" only inside its SAD definition (S5). |
| cleared | External movement (12A); SETTLED "external settlement confirmed" in section 12 | ISO 20022 (booked entry) as evidence; the status name is BizTrust-defined | A camt.053 entry with a booked `Sts` and its `BookgDt` is the bank-side fact (S1). |
| reversed | External movement (12A); REFUNDED, CHARGEBACK in section 12 | ISO 20022 `RvslInd` for the bank-side fact; refund and chargeback names are PSP / card-scheme vocabulary, `UNVERIFIED` | "Indicates whether or not the entry is the result of a reversal." (S1) |
| CREATED, PENDING, FAILED, EXPIRED, CANCELLED, REFUND_PENDING, PARTIALLY_REFUNDED | Payment state (12) | BizTrust-defined (provider-facing) | 12 says "Provider state, BizTrust operational state, allocation state and ledger state remain separately attributable." |
| not due, due, submitted, confirmed, disputed | Insurer remittance (12A) | BizTrust-defined | Insurer statement / account-current formats are outside all three publishers; no source. |
| unallocated, partially allocated, fully allocated, reallocated | Allocation (12A) | BizTrust-defined | Ledger rule; no external source. |
| unearned, earned, accrued, received, paid, clawed back | Commission (12A) | BizTrust-defined (agreement version) | No external source. |
| client risk, insurer risk, office money | Custody/risk class (12A) | Governing law and agreement (ADR-014) | See #100; not this file. |

PCI DSS defines no reconciliation status; it constrains the content of the record that carries any of them (section 4). The Bank of the Lao PDR defines no reconciliation status; it defines the message versions a Lao bank may use to report the facts (S18) and the retention horizon for payment business operators (Art. 39, via #100).

## 7. Decision-relevant facts for the P2 manual

- **The bank-versus-ledger control anchors on camt.053 (or the bank's equivalent statement), not on notifications.** camt.053 "contains information on booked entries only" and carries balances; camt.052 and camt.054 may "report pending and booked items", and camt.054 "does not contain balance information" (S1). A reconciliation that closes on a camt.054 credit notice is closing on a pending fact; the P2 manual should say which message closes a period and which merely advances a status.
- **Every outgoing instruction carries an `EndToEndId` and every expected credit is keyed on it; the bank's own key is `AcctSvcrRef`.** The end-to-end identification "is passed on, unchanged, throughout the entire end-to-end chain" and "can be used for reconciliation"; the account servicer reference is the bank's unique key for the entry (S1). Both belong on `BANK_TRANSACTION` in the domain model. Timing difference can be defined on `BookgDt` versus `ValDt` versus the ledger's effective date, all of which the entry carries separately.
- **Outsourcing card capture to a PSP does not take the platform out of PCI DSS, and how the card form is delivered changes which criteria apply.** PCI SSC: "this does not remove the merchant's responsibility"; obligations include written agreements (12.8.2) and annual monitoring (12.8.4) (S6). SAQ A's script criterion applies to an embedded iframe and "does not apply" to a redirect or a fully outsourced link (S8). The reconciliation record may carry a PSP reference and a truncated PAN in an acceptable format; a store holding only truncated PANs "may be considered out of scope" if segmented, while the truncating system stays in scope (S8a). Which SAQ and which classification apply is the compliance-accepting entity's call, not the manual's.
- **Lao bank reporting, where it follows the BOL standard, is ISO 20022 at version 001.02, not the current catalogue version.** BOL's December 2023 message standard, published as a decision dated 27-01-2026, lists camt.052.001.02, camt.053.001.02 and camt.054.001.02 alongside pacs and pain messages (S18). A parser written to V09 element names will need version negotiation with each bank; whether a given Lao bank actually delivers camt files to corporate customers is `UNVERIFIABLE` from BOL pages.
- **Lao QR is a BOL scheme with a published standard the platform cannot yet read, switched by LAPNet under BOL supervision.** Launch 29 January 2020 (S13); LAPNet is "under the supervision of Bank of the Lao PDR" (S14); the KHQR-LAOQR link runs "through a switching (LAPNet) to sponsoring bank" model (S15); the Lao QR standard decision exists as a 48-page scanned PDF (S17). If the platform accepts Lao QR, the settlement evidence chain runs merchant bank to LAPNet to payer bank, and the P2 manual should name the bank statement, not the QR acknowledgement, as the reconciled fact. Retention of ten years (Art. 39) and annual external audit (Art. 40) apply to payment business operators; whether that class includes BizTrust is #100's open question.

## 8. Unverified or unverifiable items

| # | Item | Status | Why |
|---|---|---|---|
| U1 | Wording of the finally published camt.052/053/054 V09, and the existence and content of later versions in the live catalogue | `UNVERIFIED` | iso20022.org catalogue pages timed out or reset on every attempt on 2026-09-06 (`iso-20022-message-definitions?search=camt.053`, `catalogue-messages/iso-20022-messages-archive`, with and without query, via two fetch paths and IPv4-only); the MDR PDF on the same host was retrievable. |
| U2 | ISO 20022 external code sets for entry status and balance type (current values) | `UNVERIFIED` | Not retrieved; only BOL's rendering of OPBD and CLBD was seen (S18). |
| U3 | PCI DSS v4.0.1 standard text and SAQ A r1 text | `UNVERIFIED` | Document library serves them behind a licence acknowledgement; quotations are from FAQ, glossary and an information supplement instead. |
| U4 | FAQ 1091 acceptable truncation formats; the "Modern Network Architectures" scoping supplement | `UNVERIFIED` | Not retrieved. |
| U5 | The article number and date of the outsourcing FAQ (S6) | `UNVERIFIABLE` | The page shows neither. |
| U6 | Content of the BOL Lao QR standard decision (S17) and the BIN standard decision | `UNVERIFIABLE` by text | Scanned PDFs without a text layer; Lao reader needed. |
| U7 | Agent's paraphrases of the Lao text of S18 (message standard) and S16 titles | `UNVERIFIED` | Machine-extracted Lao; a Lao reader should confirm before the manual quotes them. |
| U8 | Whether Lao QR is EMVCo merchant-presented QR based; LAPNet's own specifications | `UNVERIFIABLE` from bol.gov.la text; LAPNet is not first-party for this ticket | See section 5.2. |
| U9 | "authorized", "captured", "refund", "chargeback" as defined terms | `UNVERIFIED` | Card-scheme and PSP vocabulary; none of the three publishers defines them. |
| U10 | The roadmap's own reconciliation status names | `UNVERIFIABLE` in-repo | `BIZTRUST-ROADMAP-001` not on any branch on 2026-09-06 (see #154). |
| U11 | Whether the 2023 Payment System Law (Lao text) defines "QR code" | `UNVERIFIED` | The BOL English translation's Art. 3 does not; the 2017 law's did (S12). |
| U12 | Whether BizTrust or a tenant is a "Payment Business Operator" or "Outsourcing Service Provider" under the 2023 law | Question of law, not answered here | Belongs to #100 section 5 and ADR-014. |

## 9. Sources

All checked 2026-09-06.

- S1 ISO 20022 Registration Authority. "Bank-to-Customer Cash Management - Maintenance 2020 - 2021, Message Definition Report - Part 2, For evaluation by the Payments SEG", December 2020 (camt.052.001.09, camt.053.001.09, camt.054.001.09, camt.060.001.06). https://www.iso20022.org/sites/default/files/2020-12/ISO20022_MDRPart2_BankToCustomerCashManagement_2020_2021_v1_ForSEGReview.pdf
- S2 ISO 20022 message definitions catalogue (not retrievable on the date checked; see U1). https://www.iso20022.org/iso-20022-message-definitions?search=camt.053
- S3 ISO 20022 messages archive (not retrievable on the date checked; see U1). https://www.iso20022.org/catalogue-messages/iso-20022-messages-archive
- S5 PCI Security Standards Council, Glossary. https://www.pcisecuritystandards.org/glossary/
- S6 PCI SSC FAQ, "Does PCI DSS apply to merchants who outsource all payment processing operations and never store, process or transmit cardholder data?" https://www.pcisecuritystandards.org/faqs/does-pci-dss-apply-to-merchants-who-outsource-all-payment-processing-operations-and-never-store-process-or-transmit-cardholder-data/
- S7 PCI SSC, Information Supplement "Guidance for PCI DSS Scoping and Network Segmentation", v1.1, May 2017. https://listings.pcisecuritystandards.org/documents/Guidance-PCI-DSS-Scoping-and-Segmentation_v1_1.pdf
- S7a PCI SSC blog, "New Information Supplement: PCI DSS Scoping and Segmentation Guidance for Modern Network Architectures" (announcement only; supplement not retrieved). https://blog.pcisecuritystandards.org/new-information-supplement-pci-dss-scoping-and-segmentation-guidance-for-modern-network-architectures
- S8 PCI SSC FAQ 1588, "How does an e-commerce merchant meet the SAQ A eligibility criteria for scripts?", February 2025. https://www.pcisecuritystandards.org/faqs/1588/
- S8a PCI SSC FAQ 1117, "Are truncated Primary Account Numbers (PAN) required to be protected in accordance with PCI DSS?", September 2021. https://www.pcisecuritystandards.org/faqs/1117/ (reached via https://www.pcisecuritystandards.org/faq/articles/Frequently_Asked_Question/Are-truncated-Primary-Account-Numbers-PAN-required-to-be-protected-in-accordance-with-PCI-DSS/)
- S10 BizTrust research pack, "Lao PDR insurance intermediary regulation and client-money rules: public-source pack for the legal seat", `docs/research/arch-001a/lao-insurance-regulation.md` on branch `research/lao-insurance-regulation` (issue #100); its S20 to S22 are the BOL payment, foreign-exchange and AML instruments. https://github.com/bstBizEra/biztrust_guide/blob/research/lao-insurance-regulation/docs/research/arch-001a/lao-insurance-regulation.md
- S11 Bank of the Lao PDR, Law on Payment System (Amended) No. 45/NA, 20 November 2023, "Unofficial Translation" (same file as #100's S20). https://www.bol.gov.la/en/fileupload/18-12-2025_1766051569.pdf (index https://www.bol.gov.la/en/law)
- S12 Bank of the Lao PDR, Law on Payment System 2017 (Presidential Decree No. 292/P, 15 December 2017), English, superseded by S11. https://www.bol.gov.la/en/fileupload/14-06-2019_1560480775.pdf
- S13 Bank of the Lao PDR, "BOL officially launches Lao QR Code for domestic payment" (29 January 2020). https://www.bol.gov.la/en/fileupload/02-04-2020_1585800369.pdf
- S14 Bank of the Lao PDR, "Commercial Banks Jointly Launched Mobile Money Transfer App." (8 December 2020). https://www.bol.gov.la/en/fileupload/14-12-2020_1607936576.pdf
- S15 Bank of the Lao PDR, "The 13th Annual Bilateral Meeting between the Bank of the Lao PDR and National Bank of Cambodia and Official Launch of Cross-Border QR Payment: KHQR scan LAOQR" (18 August 2023). https://www.bol.gov.la/en/fileupload/24-08-2023_1692847075.pdf
- S16 Bank of the Lao PDR, "Lao Payment Standards" page, Lao-language site, three decisions dated 27-01-2026. https://www.bol.gov.la/Payment_Standards
- S16a Bank of the Lao PDR, "Lao Payment Standards" page, English site (empty table on the date checked). https://www.bol.gov.la/en/Payment_Standards
- S16b Bank of the Lao PDR, English pages with empty tables on the date checked: https://www.bol.gov.la/en/Retail_Payment , https://www.bol.gov.la/en/Systemic_Importance , https://www.bol.gov.la/en/Payment_Development , https://www.bol.gov.la/en/Payment_Channels ; Payment Systems Department page https://www.bol.gov.la/en/Payment_Systems
- S17 Bank of the Lao PDR, decision on the Lao QR standard for payment (ຂໍ້ຕົກລົງວ່າດ້ວຍ ມາດຕະຖານລາວຄິວອາ ເພື່ອການຊໍາລະ), listed 27-01-2026, 48-page scanned PDF. https://www.bol.gov.la/fileupload/27-01-2026_1769500648.pdf
- S17a Bank of the Lao PDR, decision on the BIN standard for card issuers, listed 27-01-2026, 6-page scanned PDF. https://www.bol.gov.la/fileupload/27-01-2026_1769500560.pdf
- S18 Bank of the Lao PDR, "ມາດຕະຖານຂໍ້ຄວາມດ້ານການຊໍາລະ ຂອງ ສປປ ລາວ" (Lao payment message standard; the listing page's English: "the Standard of Message Specification for Payment Systems"), cover dated ທັນວາ 2023 (December 2023), listed 27-01-2026, 340 pages. https://www.bol.gov.la/fileupload/27-01-2026_1769500739.pdf
- S19 Bank of the Lao PDR, "Licensed payment Service Providers and types of Payment Service". https://www.bol.gov.la/en/Licensed_payment_Service_H
- Repository: `docs/architecture/FLOWS.md` sections 12 and 12A; `docs/architecture/BIZTRUST-ARCH-001.md` section 13; `docs/architecture/DOMAIN_MODEL.md` section 2.3; issues #153, #154, #163, #168.

<!-- agent: researcher (2026-09-06) -->
