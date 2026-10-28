# Improvement Plan — `google-docs-report` skill

Handoff artifact for the next agent. Carries all context: user goals, evidence, root causes, and the ordered implementation steps. This planning session was **read-only**: the skill was not edited.

- **Created:** 2026-10-24
- **Skill path:** `/home/tim/skills/Skill-sync/google-docs-report/`
- **Scope of this plan:** define the improvement work. **Out of scope:** performing the improvement (next agent), authoring the writing-guidelines content (user, concurrent).
- **Constraint carried over:** do not edit the skill before this plan is approved.

---

## 1. User goals (why this work exists)

The skill generates corporate reports as local `.docx` (python-docx) and uploads them to Google Drive. Three drawbacks were reported:

1. **Table names (captions) are indented.** They must be flush left, with no indentation at all. Reference comparison: `tmp/table intendation/current intendation.png` (wrong) vs `tmp/table intendation/expected intendation.png` (correct).
2. **Template coverage is incomplete.** The skill does not feature all company templates; the user perceives the bundled set as vertical-only (see correction in §4.1).
3. **No writing guidelines.** Generated prose does not match the user's human writing style. The user is authoring the guidelines content **concurrently** with this plan; therefore this plan defines only the *integration point*, never the content, and contains no step to read or draft guidelines.

Acceptance for the whole improvement: a regenerated sample report shows flush-left table captions; every company template in the Drive template location is bundled and selectable; SKILL.md points at the user-supplied writing guidelines.

---

## 2. Inputs and reference material

### Local (skill directory)
| Path | Role |
|---|---|
| `SKILL.md` | Current skill revision (183 lines) |
| `scripts/generate_report.py` | Generation module (flat API, template-open → strip → append) |
| `scripts/test_report.py`, `scripts/test_report_al.py` | Sample generators per template |
| `assets/AL_Report_template.docx` | Bundled template, **portrait** |
| `assets/CD_Report_template.docx` | Bundled template, **landscape** |
| `tmp/table intendation/*.png` | Caption-indentation comparison (expected vs current) |
| `tmp/prompt` | Original task prompt |

### Google Drive — template location (folder `0AHDM7kWWG3cbUk9PVA`, root listing) and `docs_refference` (`1RsSoRKCHRRUZsVMfV1i_n_ofVIjcsFyA`)
| Document | Drive ID | Folder | Notes |
|---|---|---|---|
| `AL: Report_(Vert) template` | `18pQXhSaDp5KFZA2bSwCQ4i2li5yKFHTYwclhT-xBHBs` | root | canonical AL portrait template (source of bundled AL asset) |
| `AL_Report_(Horiz)` | `1fQtu_toUU0QS_XD6ZCXuHbTICr7z4zdYM09nG840uDQ` | docs_refference | AL landscape template — **not bundled** |
| `CD_Report_(Horiz) template` | `1IdtkrIBNYxnoMbS6PSKFvhAA0rbmu8kNS1Dd09DMWVQ` | docs_refference | source of bundled CD asset |
| `Alnicko_Report_Horiz` | `1riNPPVKtfFB9riTrd-ufMl85_CVa84SCjtCiMokYdko` | root | verify: template or filled report? |
| `AL_QA_Test procedure_(Vert)` | `1x4APWBV5ruIowvq5FdLF8DC-VEvVWhAUe64Fo6m7BNY` | root | separate document type (QA test procedure), portrait |
| `QA tets plan document example` | `1JzB-eIJ3HeGleLLNKhXOOkosYojIPRudD8JusHuuLPc` | root | filled example, reference only |
| `Руководство по работе с шаблонами (1).pdf` | `1RwVbF755hjWDC50Jo4T6-tee9gPKSa-S` | docs_refference | template-usage guide — consult when writing template-selection rules |
| `Copy of AL_Handbook по написанию отчетов_Jan 29, 2025` | `1ypYlZ-63q5mcP6zZmhawy11ICG4mBBaeMdrNwvK6p6Q` | docs_refference | existing style source already cited by SKILL.md |
| `Copy Canyon_Verification of documents_22 Aug 2023.pdf` | `1DvMwfW5uC1tF6tBR0aQRsjw8V6pBCuuA` | docs_refference | existing style source already cited by SKILL.md |

---

## 3. Defect 1 — indented table captions: root cause

### 3.1 Symptom
In `current intendation.png` the line `Table 1. - Risks of the device` starts ~1 cm right of the left margin (same offset as a body paragraph's first line). In `expected intendation.png` the same line starts flush at the left margin. Everything else (heading indents, body first-line indent, justification) is identical in both images — only the caption indent differs.

### 3.2 Mechanism (verified against the bundled templates)
Both `assets/*.docx` carry, in `word/styles.xml`:

```xml
<w:docDefaults><w:pPrDefault><w:pPr>
  <w:spacing w:line="276" w:lineRule="auto"/>
  <w:ind w:firstLine="566.9291338582675"/>   <!-- 566.93 twips = 1.0 cm first-line indent -->
  <w:jc w:val="both"/>                        <!-- justified -->
</w:pPr></w:pPrDefault></w:docDefaults>
```

- `docDefaults` (document defaults) is the fallback paragraph formatting applied to **every paragraph that does not override it**. The `Normal` style in both templates has *no* `<w:pPr>` of its own, so plain paragraphs inherit the 1 cm first-line indent and justification from `docDefaults`.
- That inheritance is **desired for body text** (corporate rule: justified body with first-line indent) and `add_paragraph()` correctly relies on it.
- `_add_caption()` (`generate_report.py` lines 239–249, the shared renderer behind `add_table_caption`/`add_figure_caption`) creates a plain paragraph and sets **only `p.alignment`**. Alignment (`w:jc`) and indentation (`w:ind`) are independent paragraph properties: overriding alignment does not remove the inherited first-line indent. The caption paragraph therefore ships to Google Docs with no `w:ind` override and renders with the 1 cm first-line offset — exactly the "current" screenshot.
- Headings are unaffected because the template's `Heading 1` style explicitly sets `w:ind w:firstLine="0"` (and `Heading 2` intentionally sets `firstLine="283.46"` for the sub-level offset visible as `5.1.` in both screenshots).
- Table *cells* had the identical inherited-indent problem and were already fixed by direct per-paragraph overrides in `_left_align_table()` (lines 469–485: `left_indent = Pt(0)`, `first_line_indent = Pt(0)`). The caption helpers simply never received the same treatment. Review rule #1 in SKILL.md documents the cell case; the caption case is the same bug class in a different code path.

### 3.3 Contributing factor: the deprecated helper is still demonstrated
`add_caption()` (lines 208–218) sets neither alignment nor indent (caption inherits justified + 1 cm indent — doubly wrong), yet both bundled test scripts still call it for table captions (`test_report.py:58`, `test_report_al.py:67`). Any agent copying the test scripts reproduces the wrong caption path despite SKILL.md marking it deprecated.

### 3.4 Fix direction (for the implementing agent)
1. In `_add_caption()`: zero the inherited indent on the caption paragraph — `p.paragraph_format.first_line_indent = Pt(0)` and `p.paragraph_format.left_indent = Pt(0)` — mirroring `_left_align_table()`. This fixes table captions (flush left) and figure captions (true centering: a first-line indent also shifts a CENTER-aligned line off the page center).
2. Either apply the same override in `add_caption()` or delete it from `__all__` and the module; then migrate both test scripts to `add_table_caption()` / `add_figure_caption()` so the demonstrated pattern matches SKILL.md.
3. Update SKILL.md review-rule checklist with the caption-indent rule ("captions carry zero first-line indent") so a hand-built caption cannot regress.
4. Acceptance: regenerate `test_report_al.py` output; the `Table 1.` line must start at the left margin (pixel-compare against `expected intendation.png`); figure captions centered on the page center.

### 3.5 Why the alternatives do not work
- **Editing `docDefaults` in the templates** (removing `w:ind`) would strip the first-line indent from *every* body paragraph, breaking the corporate body-text rule the templates encode; the indent must stay global and be cancelled per paragraph type.
- **Setting alignment only** cannot fix it: `w:jc` and `w:ind` are separate properties in OOXML; Google Docs honours both independently.
- **Instructing the model to fix indent manually** is unreliable and contradicts the skill's design (formatting enforced in the module, not remembered by the caller).

---

## 4. Defect 2 — template coverage

### 4.1 Correction to the stated drawback
Evidence from `word/document.xml` `<w:pgSz>`: bundled `AL_Report_template.docx` is **portrait**, bundled `CD_Report_template.docx` is **landscape** (`w:orient="landscape"`, 16834×11909). So "current templates are vertical only" is not literally true of the bundled assets. The real gaps are:
- the **AL family lacks its landscape variant** (`AL_Report_(Horiz)` on Drive, not bundled);
- **other document types** (QA test procedure, test plan) have no bundled template;
- there is **no registry/selection mechanism**: `new_document()` takes a raw path and defaults to the CD template, and SKILL.md never tells the agent which template fits which document type/orientation.

### 4.2 Download mechanism — same pattern as AL/CD assets
Yes, templates can be pulled into the skill following the existing pattern (template `.docx` lives in `assets/`, opened by `new_document(template_path=...)`):

1. `google-drive_downloadFile` with `fileId` = template doc ID, `localPath` = `<skill>/assets/<Name>_template.docx`, and `exportMimeType` = `application/vnd.openxmlformats-officedocument.wordprocessingml.document`. The Drive items are native Google Docs, so the MCP server exports them to `.docx` and streams to disk (no JSON-argument size limit, same reason the skill uploads via file stream).
2. If a source ever turns out to be an already-uploaded `.docx` (not a native Google Doc), download without `exportMimeType` to get original bytes.
3. Naming convention follows existing assets: `<FAMILY>_<ORIENTATION>_template.docx` (e.g. `AL_Report_Horiz_template.docx`, `AL_QA_TestProcedure_Vert_template.docx`).

### 4.3 Per-template validation checklist (before registering)
The pipeline depends on specific template internals; each new asset must be inspected (unzip `word/styles.xml`, `word/document.xml`) and confirmed to have:
- `Heading 1` / `Heading 2` paragraph styles (`_strip_body` locates the body start at the first Heading 1; `add_heading` maps onto these styles);
- a placeholder body from the first Heading 1 onward that `_strip_body` may delete without touching the front page;
- `<w:sectPr>` page setup with the expected orientation/margins (`_section_usable_width` sizes tables from it);
- `docDefaults` body rule (justify + first-line indent) — the module assumes it exists for body text and cancels it for captions/cells;
- front matter intact (`verify_integrity` expects ≥ 8 paragraphs before the first Heading 1 and ≥ 2 tables);
- numbering part optional — `_get_numbering_part()` creates one when absent.
Then generate one sample per template (copy of the test-script pattern) and run `verify_integrity`.

### 4.4 Registry and selection
- Add a small template registry in `generate_report.py` (e.g. `TEMPLATES = {"al_vert": ..., "al_horiz": ..., "cd_horiz": ..., "qa_vert": ...}` resolved against `assets/`) and let `new_document(template="al_vert")` select by key, keeping `template_path` for overrides.
- SKILL.md gains a template table: key, file, orientation, document type it serves, and the selection rule (report vs test procedure vs test plan; portrait vs landscape). Source the selection rules from `Руководство по работе с шаблонами` (Drive ID above) during implementation.
- Keep one parameterized test script (template key as CLI arg) instead of one script per template.

---

## 5. Defect 3 — writing guidelines: integration contract only

The user authors the guidelines content concurrently; this plan deliberately contains **no step to read, draft, or fetch that content**. The implementing agent only wires the integration point:

1. Reserved location: `<skill>/references/writing_guidelines.md` (new `references/` layer keeps SKILL.md lean; progressive disclosure — loaded only when body text is drafted).
2. SKILL.md gains a short "Writing style" section: before drafting any section prose, read `references/writing_guidelines.md` and follow it for tone, phrasing, and sentence structure; the guidelines override the skill's generic style advice where they conflict.
3. When the user's artifact arrives, store it at the reserved path **verbatim** (it encodes the user's personal voice; paraphrasing it would defeat its purpose), adding only a header if needed.
4. Acceptance: SKILL.md references the file; the file exists with user-supplied content; a generated sample's prose follows it.

---

## 6. Ordered implementation steps (next agent)

| # | Step | Acceptance |
|---|---|---|
| 1 | Fix `_add_caption()` indent override (§3.4.1); handle `add_caption()` deprecation/removal; migrate both test scripts to the dedicated caption helpers | regenerated sample caption flush left, matches `expected intendation.png`; figure captions truly centered |
| 2 | Add caption-indent rule to SKILL.md review checklist | checklist mentions zero first-line indent for captions |
| 3 | Download missing templates via §4.2 (`AL_Report_(Horiz)`, `AL_QA_Test procedure_(Vert)`; verify `Alnicko_Report_Horiz` nature first) | new `.docx` files in `assets/` |
| 4 | Run §4.3 validation per new asset; fix naming | validation checklist passes per template |
| 5 | Add template registry + `new_document(template=...)`; parameterized test script | `new_document("al_horiz")` etc. opens correct asset; sample generates per template |
| 6 | SKILL.md template table + selection rules (consult `Руководство по работе с шаблонами`) | SKILL.md documents every bundled template and when to use it |
| 7 | Wire writing-guidelines integration point (§5) once the user's content is delivered | `references/writing_guidelines.md` exists verbatim; SKILL.md points at it |
| 8 | End-to-end check: generate one report per bundled template, upload one to Drive, verify via `readGoogleDoc` against the review checklist | uploaded doc shows flush-left captions, correct orientation, native lists |

Steps 1–2 are independent of 3–6; step 7 waits on the user; step 8 closes the loop.

## 7. Out of scope
- Editing the skill in the planning session (done: none).
- Authoring or sourcing writing-guidelines content (user-owned, concurrent).
- Changing the upload path (.docx → `uploadFile(convertToGoogleFormat:true)`) — it works and is not among the drawbacks.

## 8. Open questions for the user
1. Is `Alnicko_Report_Horiz` a blank template or a filled report? (Determines whether it becomes an asset or only a style reference.)
2. Should QA test procedures/test plans reuse the report architecture (sections 1–6) or get their own section skeleton?
3. Confirm the bundled-templates perception: CD asset is landscape; is the felt "vertical-only" gap actually the missing AL landscape variant?
