# Scheme source register

Reviewed against the listed official sources on **2026-11-14**. This is a manually curated dataset of ten schemes: five Central Government schemes and five West Bengal schemes. Some facts are historical or unresolved; this is not an exhaustive current rulebook or eligibility decision service. No personal applicant data is included.

## Data contract

- [Dataset](../data/processed/schemes.json), [JSON Schema](../schemas/schemes.schema.json).
- `scheme_id` is an AdhikarAI-local stable identifier, not a claimed official database code.
- `government_level` describes the sponsoring government; `state: all_india` describes national scope, including West Bengal, not guaranteed individual eligibility.
- Eligibility, exclusions, benefits, documents and application process are evidence objects with `status`, `items`, `source_ids`, and `note`.
- `verified` means the listed statements are supported by the cited source, not that every possible condition has been captured. `partial` means known details coexist with explicitly described gaps. `unknown` requires empty items and references and an explanation; it never means no requirements.
- `effective_date` means original scheme commencement (YYYY-MM-DD), never website update, launch celebration or amendment date. Use the literal `unknown` when not established.
- `verification_date` and each source's `accessed_on` record this research date; they do not guarantee that a portal is fully up to date.
- `source_passage` is a short verbatim excerpt from `official_source_url`. Other fields paraphrase the sources; `source_ids` resolve within the same record and `sections` locate the evidence.
- Category labels are project taxonomy. The schema rejects unexpected fields and invalid dates when used with a format checker.

## Official sources and limitations

### Pradhan Mantri Suraksha Bima Yojana (IN-PMSBY)

- [DFS PMSBY FAQ](https://financialservices.gov.in/pmsby) — Eligibility; benefits; enrolment; termination; documents; suicide and hospitalisation FAQs.

Exact scheme commencement date not established from the reviewed FAQ; effective_date is unknown. Published entry age and termination wording are both retained; no age-boundary eligibility is inferred.

### Pradhan Mantri Jeevan Jyoti Bima Yojana (IN-PMJJBY)

- [DFS PMJJBY FAQ](https://financialservices.gov.in/pmjjby) — Benefits; eligibility; enrolment; termination; bank role.

Exact commencement date not established from reviewed FAQ; effective_date is unknown. Entry age and continuation age are distinct.

### Atal Pension Yojana (IN-APY)

- [PFRDA APY FAQ](https://pfrda.org.in/hi/w/faqs/atal-pension-yojana) — Who can subscribe; income-tax rule; benefits; Aadhaar; nomination; 40th birthday.
- [DFS APY FAQ](https://financialservices.gov.in/atal-pension-yojana) — Contribution frequency; age-boundary wording.

Scheme commencement date: unknown in this record. 2022-10-01 is the tax-rule change date, not scheme commencement. Age conflict: DFS says below completed 40; PFRDA explicitly includes the 40th birthday. PFRDA clarification retained; no eligibility engine implemented.

### Pradhan Mantri Shram Yogi Maandhan (IN-PM-SYM)

- [PIB PM-SYM explainer](https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=153849&lang=2&reg=48) — Key features; eligibility; documents; contributions; enrolment.
- [PIB PM-SYM parliamentary reply, 3 August 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2293891&lang=1&reg=48) — Eligibility; pension; contribution range.

Exact commencement day not established; effective_date is unknown. Source summaries differ in NPS wording, retained as an unresolved limitation.

### Pradhan Mantri Kisan Samman Nidhi (IN-PM-KISAN)

- [NIC PM-KISAN project](https://www.nic.gov.in/project/pm-kisan/) — Scheme overview; portal features; process flow.
- [PIB PM-KISAN first anniversary, 22 February 2020](https://www.pib.gov.in/newsite/PrintRelease.aspx?lang=2&reg=48&relid=199491) — Effective date; expansion; exclusions; registration.
- [PM-KISAN portal (search-indexed official text)](https://pmkisan.gov.in/?open_in_new_tab=true) — Mandatory eKYC; suspected cases pending physical verification.

effective_date is original scheme commencement, not the 2019 expansion date. Portal could not be directly fetched; its limited eKYC/verification facts were checked in indexed official text. Other details use opened NIC and PIB pages. This partially documented record is not a complete current rulebook.

## Phase 2B — West Bengal records

Added exactly five state records; total **10 = 5 Central + 5 West Bengal**. The original five records and JSON Schema version 1.0.0 are preserved. State records use `government_level: state` and `state: West Bengal`. Lakshmir Bhandar is retained under the requested identity with historical qualifications, not represented as a confirmed current open scheme.

### Evidence convention

Each new record's `source_passage` is an exact excerpt from its primary URL. Secondary-source excerpts are stored as `Exact evidence: "..."` in the existing `sources[].sections` string, together with a section/page locator and `Access:` retrieval mode. This reuses the schema without adding fields. Excerpts are short anchors, not the entire evidentiary record; paraphrased facts cite local `source_ids`. PDF whitespace may be normalised by the source text extractor. No claim that every live rule has been captured is made.

`opened` means readable page/PDF content was returned. `search-indexed official` means only text indexed from the government URL could be inspected; direct-fetch failures are disclosed. This is weaker evidence than an inspected current operative notification. Verification dates record review on 2026-11-14, not publication dates or a guarantee of current availability. Full source files are not archived.

### Lakshmir Bhandar (IN-WB-LAKSHMIR-BHANDAR)

- [North 24 Parganas: beneficiary migration notice, 21–23 May 2026](https://north24parganas.gov.in/notice/kyc-of-existing-lakshmir-bhandar-beneficiaries-who-have-been-migrated-to-annapurna-bhandar/) — Notice heading and description; opened.
- [WCDSW notification 1790-WCD/12099/5/2021, 31 March 2023](https://socialsecurity.wb.gov.in/lokkhiBhandar/storage/app/public_doc/Guidelines%20of%20Lakshmir%20Bhandar%2031.03.2023.pdf) — Opening; sections 1–3; search-indexed official PDF; direct fetch timed out.
- [WCDSW guidelines, 30 July 2021 (superseded)](https://socialsecurity.wb.gov.in/lokkhiBhandar/storage/app/public_doc/Guidelines%20of%20Lakshmir%20Bhandar%2030.07.2021.pdf) — Section 3(c), documents; section 4, verification; search-indexed official PDF.
- [South 24 Parganas: Lakshmir Bhandar](https://s24pgs.gov.in/lakshmir-bhandar/) — Scheme table; application column; opened.
- [West Bengal interim Budget Speech 2026–27](https://finance.wb.gov.in/writereaddata/Budget_Speech/2026-2027_English_I.pdf) — Paragraph 21, printed page 178; search-indexed official PDF; direct fetch timed out.
- [WCDSW administrative notices](https://wcdsw.wb.gov.in/notice/administrative_notice/) — Notification dated 20 May 2026; opened.

Current status: migration documented; continuation under the original name and full statewide transition terms are unknown. The requested scheme is retained as a historical record, not silently renamed.

31 March 2023 notification supersedes 30 July 2021 guidelines. South 24 Parganas still mentions Swasthya Sathi and INR 1200/month for SC/ST and INR 1000 for others; these are not accepted as current rates.

Interim Budget 2026–27 paragraph 21 proposes an additional INR 500/month from February 2026. A proposal is not proof of implemented entitlement.

WCDSW lists an Annapurna notification dated 20 May 2026, but its linked PDF was inaccessible. North 24 Parganas directly documents beneficiary migration; exact legal scope and current Lakshmir terms remain unknown.

Original commencement date is unknown; neither the 2023 modification nor the 2026 migration is used as effective_date.

### Kanyashree Prakalpa (IN-WB-KANYASHREE)

- [Purba Medinipur: Kanyashree](https://purbamedinipur.gov.in/kanyashree/) — K1/K2 benefits; qualifications; documents; institution forms; opened.
- [Kanyashree portal FAQ](https://kanyashree.wb.gov.in/faq) — Conditions / Eligibilties; opened.
- [West Bengal Administrative Calendar 2019](https://cm.wb.gov.in/ncmo/publication/Administrative_Calender_Total_Book_2019.pdf) — Achievements: Women & Child Development and Social Welfare; search-indexed official PDF; direct fetch timed out.

Scope is K1 and K2 only; postgraduate K3 is not merged into this record.

The primary district page is dated 25 May 2022. Current portal FAQ agrees on K1/K2 amounts but conflicts with the government's reported income-ceiling waiver. No latest operative amendment resolving that conflict was retrieved.

Primary district wording says K2 more than 18 and under 19; portal gives 18–19. Exact birthday inclusivity remains unknown.

Original commencement date is unknown in this evidence set.

### Rupashree Prakalpa (IN-WB-RUPASHREE)

- [WCDSW Rupashree Duare Sarkar SOP and FAQ](https://www.wb.gov.in/duare_sarkar/Rupashree.pdf) — PDF pages 1–2 and 6–7: eligibility, documents, benefit, submission; opened.
- [Alipurduar: Rupashree](https://alipurduar.gov.in/rupashree/) — About the Sections; commencement and exclusions; opened.
- [Darjeeling: Rupashree](https://darjeeling.gov.in/rupashree/) — Application submission and processing; search-indexed official page; direct fetch timed out.
- [WCDSW administrative notices](https://wcdsw.wb.gov.in/notice/administrative_notice/) — Application form dated 24 July 2025; opened.

State SOP requires bride age 18 at application; Alipurduar says at marriage. The stricter state-SOP wording is retained; whether amended is unknown.

Income boundary follows the state SOP: not greater than INR 150000, rather than summaries saying less than.

WCDSW lists a Rupashree application form dated 24 July 2025; the Google Drive attachment was not inspected. No confirmed benefit amendment found in the official material reviewed.

Commencement 1 April 2018 is explicitly supported by Alipurduar; 1 April 2019 refers to processing, not scheme commencement.

### Krishak Bandhu (Natun) (IN-WB-KRISHAK-BANDHU)

- [Cooch Behar: Krishak Bandhu](https://coochbehar.gov.in/krishak-bandhu/) — Brief description; death benefit eligibility; opened.
- [Agriculture Department: Krishak Bandhu (Natun)](https://agriculture.wb.gov.in/krishak-bandhu-natun-) — Assistance scale and two seasonal instalments; search-indexed official page; direct fetch timed out.
- [Krishak Bandhu Duare Sarkar SOP (pre-Natun rates)](https://www.wb.gov.in/duare_sarkar/Krishak_Bandhu.pdf) — Assured income FAQ Q1–Q6; ADA verification; search-indexed official PDF; direct fetch timed out.
- [West Bengal Economic Review 2021](https://finance.wb.gov.in/writereaddata/Economic_Review/Economic_Review21.pdf) — Highlights, printed page v: Krishak Bandhu (Natun); search-indexed official PDF; direct fetch timed out.
- [Separate landless agricultural labourers scheme FAQ](https://krishakbandhu.wb.gov.in/agricultural-labour/SOP_ENG.pdf) — Q2 eligibility; distinction from Krishak Bandhu; search-indexed official PDF; direct fetch timed out.

Natun launch on 17 June 2021 doubled earlier assistance; pre-Natun SOP rates of INR 5000 maximum/2000 minimum are obsolete and are not used.

Original scheme began in January 2019 according to Economic Review; exact original day is unknown, so effective_date remains unknown rather than using the Natun relaunch date.

Current Agriculture page, economic review and legacy SOP were accessible through indexed official text only. Cooch Behar page was opened but is dated June 2022 and mixes income/death material.

Official 2026 landless-labourer scheme is distinct. No confirmed later Natun benefit amendment was found; this does not establish that none exists.

### Swasthya Sathi (IN-WB-SWASTHYA-SATHI)

- [Cooch Behar: Swasthya Sathi](https://coochbehar.gov.in/swasthya-sathi/) — Eligibility; Form B; documents; opened.
- [Dakshin Dinajpur: Swasthya Sathi](https://ddinajpur.nic.in/swasthya-sathi/) — Main features; opened.
- [Finance notification 1104-F(P), 25 February 2016](https://finance.wb.gov.in/writereaddata/1104-F%28P%29.pdf) — Paragraph 6: original effective date; search-indexed official PDF; direct fetch timed out.
- [PIB: PM-JAY operationalised at AIIMS Kalyani, 18 August 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2300852&lang=2&reg=48) — Coexistence at AIIMS Kalyani; opened.
- [Akashvani: announced PM-JAY transition](https://newsonair.gov.in/ayushman-bharat-scheme-to-be-launched-in-west-bengal-from-july-2026/) — May 2026 announcement; search-indexed official government news.

Original notification's effective date is 1 April 2016; December 2016 launch is a different event. Original INR 150000 basic/INR 500000 critical-care wording is not substituted for later published family cover.

Akashvani reported planned PM-JAY incorporation from July 2026, but PIB confirmed both schemes operating at AIIMS Kalyani on 18 August 2026. Statewide migration completion, closure and fresh enrolment status are unknown.

The district sources predate transition. Retained as source-backed published terms with partial status; no claim of fully current statewide entitlement.

Full original notification was not retrieved; effective-date evidence is indexed official text.

### Unresolved issues and amendment decisions

| Scheme | Decision / remaining unknown |
| --- | --- |
| Lakshmir Bhandar | 2023 supersession is recorded. District rates, the February 2026 proposal and May migration evidence are not conflated. Current benefit is `unknown`; fresh application, current checklist and complete migration terms are unknown. Historical requirements are explicitly labelled. The linked Annapurna notification could not be read, so its terms are not inferred. |
| Kanyashree | Current FAQ retains an income ceiling, while the 2019 calendar reports waiver. Current income requirement/exclusion is unknown; K1/K2 amounts are supported. Exact birthday boundaries, renewal deadlines and all special-category documents are unresolved. |
| Rupashree | State SOP age-at-application differs from district age-at-marriage wording. SOP wording is retained with conflict disclosed. The listed 2025 form was not inspected; checklist updates and public online application route remain unknown. |
| Krishak Bandhu | 2021 Natun revision supersedes old 5000/2000 rates; income and death components stay separate. Updated documents, death-claim procedure, unrecorded tenancy and later operative amendments remain unknown. Most detailed evidence was indexed official text only. |
| Swasthya Sathi | Original effective date differs from later launch. Planned PM-JAY incorporation is not treated as proof of complete closure: August 2026 PIB confirms coexistence at one institution. Statewide migration, current enrolment and package exclusions remain unknown. |

Amendment checks covered government department pages, district guidance, the WCDSW notice index (including 2025 forms and 2026 notifications), available Finance budget/economic-review material, scheme FAQs and relevant 2026 government releases. Budget allocations and proposals do not themselves establish individual entitlements. A search returning no amendment is not evidence that no amendment exists. Unofficial search hits were not used as evidence. No successor scheme was added as an eleventh record.

### Phase boundary

Only the dataset, documentation and tests change. No UI, RAG, NLP, eligibility engine, commits or deployment are part of Phase 2B. Offline validation checks structure and evidence consistency, not policy truth. Regression tests fingerprint the complete original five records, check the exact five state IDs, source evidence/date conventions, explicit unknowns and invalid provenance rejection.

## Phase 2A review method (original records)

Read official ministry/regulator FAQs and government portal explanations; retain explicit constraints and exceptions, and distinguish original effective dates from rule amendments. Primary-source pages were opened except the PM-KISAN portal notice, which was available only as search-indexed official text after direct fetch failure. No unofficial scheme aggregator was used as evidence. Full page snapshots were not archived; the excerpts and section locators support later manual review.

PFRDA's explicit birthday clarification takes precedence in the descriptive APY record over the conflicting DFS FAQ. Its tax restriction is retained even though the DFS overview omits it. PM-SYM's NPS wording remains a marked uncertainty. PM-KISAN's exclusions are explicitly partial and its complete document checklist is unknown; this is not suitable for automatic screening.

## Validation and maintenance

Install `python -m pip install -r requirements-dev.txt` after the editable package installation, then run `python -m unittest discover -s tests -v`. Tests validate the schema, ten records (5+5), preservation of the original five, unique IDs, source references, official URL hosts, dates, evidence locators and unknown semantics; malformed-record tests exercise rejection paths. Offline tests cannot prove factual accuracy or detect future policy changes. Re-open the sources before updating records, preserve qualifications, and update the verification date only after review.

Only this curated public seed dataset is allowed through Git ignore rules; other local data remains ignored. The application does not load these records yet.
