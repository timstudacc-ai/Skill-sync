---
name: google-docs-report-v2
description: Creates and formats corporate reports directly in Google Docs through Google Workspace. Use it whenever the user asks to create a report, corporate document, or formal write-up (создать отчет на тему...), when data from CSVs, logs, or measurements must be aggregated into a document, or when any document must follow the standard corporate structure, formatting, and writing style — even if the user does not explicitly say "report". Covers document structure, formatting, styling, and writing guidelines; the execution environment provides the document-creation tools.
---

# Google Docs Report Creation (formatting and writing standard)

Create corporate reports in Google Workspace following the company's report architecture and formatting standard. This skill defines **what the document must contain and how it must be formatted and written**. It is deliberately tool-agnostic: the environment provides Google Workspace access and the ability to create documents, so apply these rules with whatever document-creation tools are available.

Read `references/writing_guidelines.md` before drafting body text — it governs voice, tense, casing, punctuation, units, and paragraph roles.

## When to use

- User asks to create a report, corporate document, or formal write-up in Google Docs/Drive
- Data comes from CSVs, logs, Sheets, or measurement results that need aggregation into a document
- A report must follow the standard corporate structure (Document history → Verification → Contents → Introduction → Purpose → References → Abbreviations → Report results → Conclusions)
- An existing corporate document must be extended or brought up to standard

## Core principles

### 1. Build on the company template — never rebuild the front page

All documents start from the corporate template (CD_* / AL_*) located on Google Drive. Find it, copy it (or open the unfinished document), and fill in its fields: Document name, Project, Version, Author, Date, Designed by, Document type. Never rebuild or restyle the front page — replace or extend **body content only**, from the first Heading 1 onward.

The template carries the approved page setup (orientation, margins, page size, fonts). Inheriting it is the only way to guarantee consistency with every other corporate document without restyling anything by hand.

### 2. Prepare content before writing

Never paste raw multi-thousand-row data into a report, and never hold it in working memory while drafting. Aggregate first — compute means, min/max, spread, build summary tables with the data tools at hand — then write the document from the summaries. A report contains analyzed results, not raw dumps; bulky details belong in an appendix or a linked spreadsheet.

### 3. Use native document features, never visual imitations

Headings, lists, and tables must be real document objects, not text that merely looks like them:

- **Headings** — apply the template's Heading styles. This is what drives the auto-generated table of contents and document navigation. Never fake a heading with bold body text.
- **Lists** — use real list functionality, never typed `•` or `1.` prefixes. Typed prefixes do not renumber when items are inserted, cannot be extended by later editors, and break outline navigation. Numbered lists for sequences; bulleted lists for enumerations.
- **Tables** — insert native tables with a header row that repeats across page breaks. Never align text with tabs or spaces to imitate a table.

### 4. Prefer few large operations over many small ones

Build content in big structured steps — insert a whole table at once, write a whole section at once — instead of cell-by-cell or sentence-by-sentence construction. Many tiny operations are slow, and an interrupted sequence of them leaves the document in a half-built state.

## Report architecture (mandatory)

The standard corporate report structure:

```
Document history
Verification
Contents
1. Introduction
2. Purpose
3. References
4. Abbreviations/Definitions
5. Report results
6. Conclusions
    6.1. Verification conclusions
```

Section guidelines:

- **Document history** — version, date, author, description of change; a small table.
- **Verification** — table of verification/approval roles (Author, Verified by, Approved by) with names and dates.
- **Contents** — auto-generated from headings; no manual work.
- **Introduction** — 2–3 sentences: what the document is about, for whom, what problem it solves.
- **Purpose** — the clear goal of the document.
- **References** — mandatory link to the Hubstaff task; internal resources as chips/short named links with a description; remove internal links from client-facing documents. No raw URLs anywhere: use a meaningful short label plus a link. If the exact target document is not known at creation time, leave a placeholder (`Short label - [link]`) instead of inventing full official titles.
- **Abbreviations/Definitions** — glossary of specific terms used. Render as a **glossary table**: borderless (transparent), no header row, bold first column, left-aligned, **no caption above it** — the section heading is the only label it gets. Do not use a bordered data table with a header row here.
- **Report results** — the main body: methodology, results, analysis, visualization. Prefer prose over tables for descriptive content; use tables only for genuinely tabular data.
- **Conclusions** — what the data means, recommendations, limitations.

## Document formatting rules (mandatory)

Sources: **Canyon "Verification of documents"** (22 Aug 2023) and **AL Handbook по написанию отчетов** (Jan 29, 2025), both in the `docs_refference` folder on Drive.

Several rules below were flagged by reviewers in past document reviews — they are marked **[reviewed]** and are the items most often gotten wrong.

### Templates and front matter
- All documents are built on company templates (CD_* / AL_*); never rebuild or restyle the front page — only fill its fields.
- The **Document history** table records every change: what changed (with section/table/figure numbers), author, date, version, and verification status.
- Verification status values (dropdown): `Not verified` / `In progress` / `Under review` / `Verified`.

### Text
- One font only — the template's font; consistent, readable sizes; never mix fonts in one document.
- **Headings only via the template's Heading styles** **[reviewed]**, numbered with a **trailing dot on every level**: `5.`, `5.1.`, `5.1.2.` — never `5.1` or `5.1)`. Verify every heading before delivery.
- Body paragraphs **justified**; captions follow their own alignment rules (tables left, figures center); short standalone lines and placeholders may be centered.
- Bold = key emphasis only; italic = explanations; monospace = code/identifiers.
- Uniform paragraph format (identical indents and spacing) throughout the document.
- **Numbered lists for sequences, bulleted lists for enumerations** — always real list objects **[reviewed]**, never typed prefixes.

### Tables
- **Data tables**: bold header row on a subtle background fill; header row repeats on every page; compact — details go to an appendix/Sheet; no merged cells. Captioned **above** the table.
- **Glossary tables** (Abbreviations, Definitions): borderless, no header row, bold first column, left-aligned, **no caption** **[reviewed]**.
- **All text inside tables is left-aligned with zero indent** **[reviewed]** — body-paragraph indents must not leak into cells; a stray first-line indent shows as a gap in every cell.
- Every data table and figure is captioned and numbered sequentially (`Table N.`, `Figure N.`), referenced from the body text:
  - **Table captions are LEFT-aligned; figure captions are CENTER-aligned** **[reviewed]**.
  - In both, the **label part (`Table N.` / `Figure N.`) is bold + italic**, the description is italic **[reviewed]**.
  - **Captions carry zero first-line and left indentation** **[reviewed]** — an inherited paragraph indent pushes a left caption off the margin and shifts a centered caption off the page centre.
- Prefer prose paragraphs over tables for descriptive content.

### Links and references
- No raw URLs. Internal resources → chips/named links with a short description; external → named link with description. In client-facing documents remove internal links, keeping names and descriptions.
- Unknown targets at creation time → placeholder `Short label - [link]`; never invent full official document titles.
- Images/tables/graphs are centered on the page with equal side margins; readers must understand what is shown (captions, markers).

### Reviewer checklist

Proofread before delivery and verify each of these — they are the exact items reviewers flagged:

1. Trailing dot on every heading level (`5.`, `5.1.`, `5.1.2.`)
2. Headings use real Heading styles (table of contents builds correctly)
3. Table captions left-aligned, figure captions centered
4. Caption labels bold + italic, descriptions italic
5. Captions have zero paragraph indent
6. No captions above glossary tables
7. Glossary tables borderless, no header row, bold first column
8. All lists are real list objects, no typed prefixes
9. All table cells left-aligned, zero indent
10. Data tables have repeating header rows and captions

## Workflow

### Step 1. Reconnaissance
1. Search Google Drive for the corporate template or the unfinished document the user mentioned.
2. Read the current content of anything found.
3. If the user references the AL Handbook or report examples, locate and consult them in the `docs_refference` folder.

### Step 2. Prepare content
1. Aggregate all source data into summaries before writing — never work from raw dumps.
2. Build the summary tables.
3. Draft the text of every section, following `references/writing_guidelines.md`.

### Step 3. Create the document
1. Start from the company template (a copy of it); fill the front-page fields.
2. Build the body section by section with native features: Heading styles, real lists, native tables, correctly aligned and styled captions.
3. Apply the formatting rules above as you go — do not draft "rough" formatting to fix later; every later edit is another chance to miss a reviewed rule.

### Step 4. Verification
1. Read the finished document back and verify structure and formatting against the reviewer checklist.
2. Pass the document to the user for review.

## Notes

- **Never rebuild the title page.** Extend body content from the first Heading 1 onward only.
- The document then goes through the Google Docs **approval request** flow: approval locks the file; re-request approval after any post-approval edit.
- **Document language**: the writing guidelines are written for English documentation. When the user's request, an existing template, or the document being continued requires another language, apply every non-language-specific rule (structure, formatting, English technical-term casing, units, caption conventions) unchanged.
- Anti-patterns: per-cell table construction; typed bullet/number prefixes; bold-text pseudo-headings; raw URLs; bordered header-row tables used as glossaries; inventing official titles for unknown reference targets.
