---
name: google-docs-report
description: Creates content for corporate documentation, use it when the user asks to create a report (создать отчет на тему...)
---

# Google Docs Report Creation

Create corporate reports and documents through the Google Drive MCP server, following the company's report architecture and minimizing the number of MCP calls.

## When to use

- User asks to create a report, corporate document, or formal write-up in Google Docs/Drive
- Data comes from CSVs, logs, or measurement results that need aggregation
- A report must follow the standard corporate structure (Document history → Verification → Contents → Introduction → Purpose → References → Abbreviations → Report results → Conclusions)

## Core principles

### 1. The working path: generate .docx locally, then upload (critical)

**`createDocFromHTML` and `createGoogleDoc` are unreliable for real reports.** They fail with `Invalid JSON argument` when the content exceeds roughly 1750–1900 characters — the MCP bridge cannot parse a large JSON argument.

**The reliable path is:**
1. Generate a `.docx` file **locally** (python-docx) with proper headings, tables, and formatting.
2. Upload it to Google Drive with `uploadFile(convertToGoogleFormat:true)` — the content streams from disk, bypassing the JSON argument limit entirely.

This produces a properly formatted Google Doc with native headings and real tables.

### 2. Prepare data locally

Never load raw 5000-row CSVs into the model context. Aggregate locally first:

- Use `awk`, `python`, or simple shell pipelines to compute means, min/max, stddev from CSV logs
- Build a summary table of averaged values
- Write all section text locally
- Only then generate the document

### 3. Generate the .docx with python-docx (template-based)

**The correct approach: open the original corporate template, then append body content only.**

The bundled `scripts/generate_report.py` module does this (the corporate `.docx` templates it opens live in `assets/`). It:
1. Opens the original `.docx` template — preserving the exact front page (title, Document history table, Verification table, Contents) **and** the body section's page setup (landscape/portrait, margins, page size).
2. Strips the placeholder body from the first Heading 1 onward (or from a custom `start_marker` paragraph).
3. Appends the report's real sections using the template's built-in styles (Heading 1, Heading 2, Normal).
4. Tables auto-fit to the section's usable text area (page width − left − right margins), never overflowing.

**API (flat functions — no class wrapper):**

```python
from generate_report import (
    new_document, save, verify_integrity,
    add_heading, add_paragraph,
    add_table_caption, add_figure_caption,
    add_bullet_list, add_numbered_list, add_table, add_glossary_table,
    add_page_break,
)

doc = new_document()  # opens template, strips placeholder body
add_heading(doc, "1. Introduction", level=1)        # trailing dot on every level!
add_paragraph(doc, "Body text here.")               # justified by default (corporate rule)
add_bullet_list(doc, ["Item 1", "Item 2"])          # REAL Word lists (numPr)
add_numbered_list(doc, [("Step 1", 0), ("Step 2", 0)])
add_table_caption(doc, "Table 1.", "Description")   # LEFT-aligned caption
add_table(doc, headers=["Col A", "Col B"], rows=[["val1", "val2"]])
add_glossary_table(doc, [["API", "Application Programming Interface"]])  # no caption!
add_figure_caption(doc, "Figure 1.", "Description") # CENTER-aligned caption
save(doc, "/tmp/Report.docx")
```

`add_caption` still exists for generic caption lines but is deprecated for tables/figures — use the two dedicated helpers, which enforce the correct alignment.

### 4. Review comments implemented in `generate_report.py` (document-review revision)

These rules came from a document review round; the module now enforces them, and the model must not undo them:

1. **No redundant indents inside table cells.** Cell paragraphs inherit the `Normal` style's first-line indent, which shows as a stray gap in every cell. `_left_align_table()` now zeroes `left_indent`, `first_line_indent`, and cell paragraph spacing. If you build a table by hand, do the same.
2. **Heading numbering convention: a trailing dot on EVERY level.** Correct: `5.`, `5.1.`, `5.1.2.` — Incorrect: `5.1` (no dot), `5.1)`. Verify every heading before delivery.
3. **Glossary/definition tables (Abbreviations, Definitions) are transparent (borderless) tables and must NOT carry a caption/name above them.** Never call `add_table_caption` before `add_glossary_table`; the section headings 4.1/4.2 are the only label they get. Data tables DO get captions.
4. **Figure captions are CENTER-aligned** — use `add_figure_caption()`. In both caption helpers the **label part (`Table N.` / `Figure N.`) is bold + italic**, the description is italic (review round 2).
5. **Table captions are LEFT-aligned** — use `add_table_caption()`.
6. **Lists must be REAL Word lists, not fake text prefixes.** A manual `• item` or `1. item` string in a plain paragraph does not survive the .docx → Google Doc conversion as a list object — Google Docs imports it as plain text, so the list can't be extended and doesn't renumber. `generate_report.py` now creates true lists by adding a numbering definition (`w:abstractNum` + `w:num` in `numbering.xml`) and referencing it from each item paragraph via `w:numPr`. python-docx has NO high-level list API and `NumberingPart.new()` raises `NotImplementedError`, so the module constructs the numbering part manually via the OPC layer when the template lacks one (the CD template already has one — the module only appends its own definitions, tagged with a custom `w:tplc`, never touching existing ones). **The decimal level definition must include `<w:start w:val="1"/>`** — Word defaults the counter to 1 but Google Docs starts at 0 when `w:start` is absent (review round 2). Never regress to text-prefix "lists".
7. **All text inside tables is left-aligned** — enforced by `_left_align_table()` for both data and glossary tables.

## Report architecture (mandatory)

The standard corporate report structure. **The model language of the document body is Russian** (unless the user specifies otherwise); title-page fields in English.

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

- **Document history**: version, date, author, description of change — often as a small table.
- **Verification**: table of verification/approval roles (Author, Verified by, Approved by) with names and dates.
- **Contents**: auto-generated by Google Docs from headings — no manual work needed.
- **Introduction** — 2-3 sentences: what the document is about, for whom, what problem it solves.
- **Purpose** — the clear goal of the document.
- **References** — mandatory link to the Hubstaff task; internal resources as chips with description; remove internal links from client-facing documents. No raw URLs anywhere: use a meaningful short label plus a link. If the exact target document is not known at generation time, leave a placeholder (`Short label - [link]`) instead of inventing full official titles.
- **Abbreviations/Definitions** — glossary of specific terms used. Render as a **glossary table** via `add_glossary_table()`: borderless, no header row, bold first column, left-aligned, **NO caption above it** (review rule #3). Do NOT use a bordered data table with a header row here.
- **Report results** — the main body: methodology, results, analysis, visualization. Prefer prose over tables for descriptive content; use tables only for genuinely tabular data.
- **Conclusions** — what the data means, recommendations, limitations.

## Document formatting rules (mandatory)

Sources: **Canyon "Verification of documents"** (22 Aug 2023) and **AL Handbook по написанию отчетов** (Jan 29, 2025), both in the `docs_refference` folder on Drive.

### Templates and front matter
- All documents are built on company templates (CD_* / AL_*); never rebuild or restyle the front page — only fill its fields (Document name, Project, Version, Author, Date, Designed by, Document type).
- The **Document history** table records every change: what changed (with section/table/figure numbers), author, date, version, and verification status.
- Verification status values (dropdown): `Not verified` / `In progress` / `Under review` / `Verified`.

### Text
- One font only — the template's font; consistent, readable sizes; never mix fonts in one document.
- Headings only via the template's Heading styles, numbered with a trailing dot on every level (`5.`, `5.1.`, `5.1.2.` — never `5.1`); never manual bold-as-heading. This drives the auto-generated table of contents.
- Body paragraphs **justified**; captions follow their alignment rules (tables left, figures center); short standalone lines and placeholders may be centered.
- Bold = key emphasis only; italic = explanations; monospace = code/identifiers.
- Uniform paragraph format (identical indents and spacing) throughout the document.
- **Numbered lists for sequences, bulleted lists for enumerations** — always real Word lists via the module (review rule #6).

### Tables
- **Data tables** (`add_table`): bold header row on a subtle background fill; **all cells left-aligned with zero indent**; header row repeats on every page; compact — details go to an appendix/Sheet; no merged cells. Captioned above with `add_table_caption` (left-aligned; label `Table N.` bold+italic, description italic).
- **Glossary tables** (`add_glossary_table`): borderless, no header row, bold first column, left-aligned, **no caption**.
- Every data table and figure is captioned and numbered: `Table N. - Description`, `Figure N. - Description` — sequential, referenced from the body text. The numbering label part is **bold + italic** in both table and figure captions.
- Prefer prose paragraphs over tables for descriptive content.

### Links and references
- No raw URLs. Internal resources → chips/named links with a short description; external → named link with description. In client-facing documents remove internal links, keeping names and descriptions.
- Unknown targets at generation time → placeholder `Short label - [link]`; never invent full official document titles.
- Images/tables/graphs are centered on the page with equal side margins; readers must understand what is shown (captions, markers).

### Review workflow
- Proofread before delivery; **check the review-rule checklist** (heading dots, caption alignments, no glossary captions, real lists, clean cell indents) — these are the items reviewers flagged.
- Verify structure and formatting via `readGoogleDoc` after upload.
- The document then goes through the Google Docs **approval request** flow: approval locks the file; re-request approval after any post-approval edit.

## Workflow

### Step 1. Reconnaissance
1. Search Google Drive for an existing template or unfinished document (`search`).
2. Read its current content (`readGoogleDoc`).
3. If the user references the AL Handbook or report examples, locate and consult them from the `docs_refference` folder.

### Step 2. Prepare content LOCALLY
1. Aggregate all data locally (awk/python) — never load raw CSVs into context.
2. Build summary tables.
3. Write the text of all sections.

### Step 3. Generate and upload the document
1. Create a local script (or adapt the test template) calling `new_document()`, `add_table()`, etc.
2. Run with `uv run --with python-docx` to produce the `.docx`.
3. Upload with `uploadFile`:
   ```json
   {
     "localPath": "/path/to/report.docx",
     "name": "Report title",
     "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
     "convertToGoogleFormat": true
   }
   ```
   **Always pass `mimeType` explicitly** — without it the MCP server may misdetect the type and refuse conversion.

### Step 4. Verification
- Read the result (`readGoogleDoc`) and verify structure/formatting against the review-rule checklist.
- Pass to the user for review.

## Notes

- **Never** build a long document with `createDocFromHTML` or `createGoogleDoc` — they fail on large content. Use the .docx + upload path.
- **Anti-pattern: per-cell MCP table calls.** Build the table locally with `add_table()`, then upload the `.docx` once.
- **Never rebuild the title page.** Open the template and only strip/replace content from the first Heading 1 onward.
- `uploadFile` with `convertToGoogleFormat:true` converts `.docx` → Google Doc, `.xlsx` → Google Sheet, `.pptx` → Google Slides. It does **not** convert `.html` or `.csv`.
- Document language: Russian (body), English (title-page fields) — unless the user specifies otherwise.
- Never use `deleteRange` across structural elements (tables, images) — it errors. Use one-shot content replacement instead.
