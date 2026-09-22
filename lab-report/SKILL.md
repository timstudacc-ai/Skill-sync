---
name: lab-report
description: Generates lab-work reports for the "Програмування" course (NTU «Dnipro Polytechnic») as DOCX + PDF, fully compliant with Appendix А formatting rules of the 2025 methodical guide. Use when the user asks to create/generate a lab report («створити звіт з лабораторної роботи», «зробити звіт по роботі №…», "lab report for programming", «оформи звіт»).
---

# Lab Report Generation — «Програмування», NTU «Dnipro Polytechnic»

Generates a lab-work report in **both formats at once** — `.docx` and `.pdf` —
from a single content description, strictly following **Appendix А** of
`Programming_Methodical_Recommendations_2025.pdf`.

**Language rule: generated reports are ALWAYS in Ukrainian.** This skill file
is in English (standard for skills); only the *output document* is Ukrainian.

## 1. Activation (REQUIRED, critical)

The skill's scripts run **only** inside the dedicated virtual environment.
Activate it before any run:

```bash
source ~/.venvs/lab-report/bin/activate
```

Every module self-checks `sys.prefix`: running outside the venv aborts with
an activation hint. This is intentional — `python-docx` and `weasyprint` are
guaranteed only in that venv; the system Python cannot import them.

## 2. Formatting rules (Appendix А — hard-coded in the renderers)

### Page and text parameters
| Parameter | Value |
|---|---|
| Paper | A4 |
| Main font | Times New Roman, size 14 |
| Line spacing | 1–1.5 (renderer uses 1.5) |
| Paragraph indent | 5 characters (~1.25 cm) |
| Text alignment | justified (по ширині) |
| Code font | monospace (Consolas / SF Mono / Courier New / Source Code Pro / DejaVu Sans Mono …), size 10 |
| Code alignment | strictly left |
| Figures, tables, captions, formulas | strictly centered |
| Title page | per fig. А.1/А.2: university on 2 lines, all bold no italics, «Тема роботи:» left-aligned, «Виконав/Перевірив» block right-shifted without italics, «Дніпро / year» centered at the bottom with a large gap below the reviewer block |

### Writing style — third person ONLY (critical)
Correct: «В ході роботи розроблено алгоритм...», «Під час виконання роботи
опановано використання...».
Wrong: «В ході роботи я розробив...», «...ми опанували...».
Conclusions should use phrases like «В роботі розглянуті...», «...виконані...»,
«Отриманий результат дозволив...» and analyse goal achievement, features and
difficulties of the work.

### Body structure (fig. А.3) — headings separated by a blank line ("через рядок")
```
Робота №N            ← centered, bold, top of page
Тема роботи          ← centered, bold
Мета роботи: …       ← immediately below the topic, justified
                     ← one blank line
Хід роботи           ← centered, bold
                     ← one blank line
variant + body text / formulas / code / figures / tables
                     ← one blank line
Висновки             ← centered, bold
                     ← one blank line
conclusion text (goal achievement, features, difficulties)
```
The report description always starts on the page **after** the title page.

### Variant, formulas, figures
- The assigned **variant number** must be stated at the beginning of «Хід роботи».
- A variant's **math expression** goes centered, numbered: `S = …  (1)`.
- Figures: image centered, caption **below** it in the format
  `Рисунок 1 – Код програми за пунктом 1 завдання роботи №3`.
- Every figure **must be referenced from the text** («...як представлено на
  рисунку 1») and key code fragments must be **commented with line numbers**,
  explaining the functions used and their features.
- Code screenshots (for short code): white background, clear contrasting text.
- Delivery: **PDF** for distance learning; **printed** copy for in-person.

## 3. Architecture (why this way)

* One format-independent `Report` object → `render_docx()` + `render_pdf()`.
  Single data source — the two outputs cannot diverge.
* DOCX — `python-docx`: native editable Word file.
* PDF — `WeasyPrint` (HTML+CSS → PDF). Direct DOCX→PDF conversion is
  impossible here (no LibreOffice/pandoc), so the PDF is rendered
  independently from the same data; its CSS mirrors the same Appendix А rules.
* Fonts: DOCX declares `Times New Roman` (present in the user's Word); in PDF
  WeasyPrint falls back to `Liberation Serif`, the metrically identical TNR
  substitute. Code: `Consolas` → `DejaVu Sans Mono`.

## 4. Workflow

### Step 0. Verify the assignment BEFORE generating (critical — real failure case)

A past report was generated with the **wrong work number, topic, purpose and
content set** (робота №1 was delivered with the content of a previous
report), and contained only 1 of 3 required expressions. Root cause: the
agent trusted the existing file instead of re-checking the assignment.

Before writing any script:

1. **Confirm the work number, topic and «мета роботи»** against the methodical
   guide (`Programming_Methodical_Recommendations_2025.pdf`) — query the
   NotebookLM notebook or render the relevant guide pages. Never assume that
   an existing report file in the folder corresponds to the requested work.
2. **Extract the exact assignment text** for the work and variant: what
   sections MUST be present and what is explicitly NOT required (e.g.
   робота №1 requires *only three schemes* — code listings, test tables and
   if-operator conclusions are superfluous). Include exactly the required set.
3. **Verify every math expression against the variant tables** (табл. 1.1 →
   S1, табл. 1.2 → S2, табл. 1.3 → S3 …). `pdftotext` mangles formulas
   (fractions, superscripts, big parentheses) — **render the table pages with
   `pdftoppm -png` and read them as images** instead of trusting extracted
   text. A real bug from history: «2x» was transcribed as «2» in a scheme
   block and the 11-element sum was written for 10 elements.
4. **Re-list the working directory right before referencing files.** The user
   renames/moves files mid-session (real case: screenshots renamed to
   `diagram1.png … diagram3.png`, the whole project dir moved). Check that
   every image path actually exists at render time and that conditional
   embedding is used (section 6).

### Step 1. Collect the work's data
From the user (or the methodical guide / code in the working directory): work
number, topic, purpose («мета роботи»), body text in **third person**, program
code, conclusions, and title-page data (group, student name, teacher position
and name, faculty, department, year). Ask when data is missing — never invent.


### Step 2. Write the generation script
Create the script **in the current working directory** (e.g. `./report_lab3.py`),
NOT inside the skill's directory — the skill's `scripts/` folder is
read-only reference material, user files live in the workspace. Import the
skill's module via `sys.path`:

```python
import os, sys
sys.path.insert(0, os.path.expanduser(
    "~/.agents/skills/lab-report/scripts"))
from lab_report import (
    Report, add_paragraph, add_code, add_figure, add_formula, add_table,
    render_docx, render_pdf,
)

r = Report(
    work_number=3,
    topic="Програмування алгоритмів розгалуження мовою C",
    purpose="закріпити знання та навички з розробки простих консольних "
            "програм мовою програмування C з використанням оператора if. "
            "Закріпити навички створення власних функцій.",
    variant="Варіант 12",                      # or None
    student_group="ІД.126-24-1", student_name="С.О. Вірній",
    teacher_position="доцент каф. ІТКІ", teacher_name="І.М. Гаркуша",
    faculty="Факультет інформаційних технологій",
    department="Кафедра інформаційних технологій та комп'ютерної інженерії",
)

# Variant's formula: centered, numbered (1)
add_formula(r, "S = 3,7x·√(5z³ + 21x − 3,4y²) + 7z·√(sin²2x³)", number=1)

# Body paragraphs: justified, auto paragraph indent
add_paragraph(r, "В ході роботи розроблений алгоритм розгалуження, який …")

# Program code: monospace 10 pt, left aligned
add_code(r, '''#include <stdio.h>
int main(void) {
    double x = 2.5, y = 3.1;
    if (x > y) printf("max = %f\\n", x);
    else       printf("max = %f\\n", y);
    return 0;
}''')

# Figure: caption below, auto-numbered "Рисунок N – …"
add_figure(r, "/path/to/code_screenshot.png",
           "Код програми за пунктом 1 завдання роботи №3")

# Table (optional): centered, bordered, bold header
add_table(r, headers=["x", "y", "S"], rows=[["2.5", "3.1", "12.04"]])

r.conclusions = ["В роботі розглянуті алгоритми розгалуження мовою C. …"]

render_docx(r, "/home/tim/laboratorni/звіт_робота_3.docx")
render_pdf(r,  "/home/tim/laboratorni/звіт_робота_3.pdf")
```

### Step 3. Render and run

`source ~/.venvs/lab-report/bin/activate && python report_labN.py`.

### Step 4. Post-render verification (MANDATORY — never skip)

A delivered report once had: a figure separated from its caption by a page
break, a formula rendered with a broken character («aᵢ» → «a;»), wrong figure
captions («(завдання №2)» instead of №1, duplicated «завдання завдання №3»),
and S1/S2 labels inconsistent between schemes and text. All of these are
caught by the checklist below.

1. **Verify the PDF visually, page by page** — render and *read* the images:
   ```bash
   pdftoppm -png -r 80 "звіт_робота_N.pdf" /tmp/pg && ls /tmp/pg*.png
   ```
   then read every page image. Do not trust the console output alone.

2. **Checklist (fix and re-render until all pass):**
   - [ ] Work number, topic, «мета роботи» on the title page and page 2 match
         the assignment (Step 0);
   - [ ] ALL required expressions are present (e.g. S1, S2, S3), each centered
         with a number `(N)` near the right margin; no lost factors or wrong
         sub/superscripts;
   - [ ] Every figure is immediately followed by its caption, **on the same
         page** (in the PDF renderer wrap image + caption in `KeepTogether`;
         in DOCX insert them in one block);
   - [ ] Figure captions have the correct work/task numbers, no duplicated
         words, auto-numbering matches the references in the text
         («...на рисунку N»);
   - [ ] Scheme labels are consistent with the text and code (same S-names,
         same array names, same conditions);
   - [ ] No mojibake: Cyrillic renders correctly, subscripts are real
         subscripts (`a<sub>i</sub>` in markup, not Unicode `ᵢ` which may
         render as «a;» in some fonts);
   - [ ] Third person everywhere, no «я/ми»;
   - [ ] No unexpectedly empty pages (large orphan whitespace because a
         KeepTogether block moved to the next page — shrink the image or
         reflow);
   - [ ] Content set matches the assignment: nothing missing, nothing
         superfluous (code listings / test tables only if the assignment
         requires them).

3. **PDF pipeline probe.** Do not assume the converter works. If DOCX→PDF is
   needed, first probe LibreOffice on a trivial file
   (`soffice --headless -env:UserInstallation=file:///tmp/lo_probe
   --convert-to pdf /tmp/probe.docx`); a broken install fails with
   «source file could not be loaded» for *any* file. In that case generate
   the PDF **directly** (e.g. reportlab with registered Liberation Serif
   TTFs — Cyrillic-safe, supports `<sub>/<super>` markup) instead of
   LibreOffice, and run the same Step 4 checklist on the result.


## 5. API reference

```python
Report(work_number, topic, purpose, *, variant=None,
       ministry="Міністерство освіти і науки України",
       university="Національний технічний університет "
                  "«Дніпровська політехніка»",   # auto-split into 2 lines
       faculty=..., department=...,
       student_group, student_name,
       teacher_position, teacher_name,
       city="Дніпро", year=<current year>)

add_paragraph(r, text)               # body paragraph (justified, indent)
add_code(r, text)                    # code block (mono 10 pt, left)
add_figure(r, image_path, caption)   # centered figure + "Рисунок N – caption"
                                     # images are user-provided (section 6)
add_formula(r, text, number=None)    # centered formula + "  (number)"
add_table(r, headers, rows)          # centered bordered table
render_docx(r, path) / render_pdf(r, path)
```

## 6. Images & attachments (user-provided)

**The user adds images for embedding themselves.** The agent never invents,
generates fake screenshots, or downloads figures on its own. Typical image
sets per report (real example from this skill's history):

* **Algorithm flowcharts** — exported from draw.io as clean PNG files
  (per the methodical guide: PNG export, not an IDE screenshot). File names
  may contain spaces and Cyrillic, e.g.
  `flowcharts-2. Розгалуження.png`.
* **Code screenshots** — taken by the user in VS Code/Eclipse.
  **White background and clearly readable text is REQUIRED by Appendix А**
  (dark-theme shots violate the rule — warn the user and ask to re-shoot).

### Handling pattern (proven in practice)

1. **Stage files under ASCII names** before rendering — spaces/Cyrillic in
   paths break WeasyPrint's `file://` URLs:

   ```python
   import shutil
   shots = {}
   for i, name in enumerate(sorted(os.listdir(SRC)), start=1):
       if name.endswith(".png"):
           dst = f"/tmp/diagram{i}.png"
           shutil.copy(os.path.join(SRC, name), dst)
           shots[i] = dst
   ```

2. **Embed screenshots conditionally** — the user may save them later, the
   script must not crash:

   ```python
   shot = os.path.join(OUT, "screenshot_task1.png")
   if os.path.exists(shot):
       add_figure(r, shot, "Код програми завдання 1 (знімок з екрану)")
   ```

3. **Figure order = `add_figure` call order** — numbers are assigned
   automatically (`Рисунок 1`, `Рисунок 2`, …). Insert each figure
   immediately after the paragraph that references it, otherwise the numbers
   in the text drift (a real bug from history: the cycle diagram was added
   after the test table while the text called it «рисунок 4»).
4. **Every figure needs a text reference** («...представлена на рисунку N»)
   and, for code screenshots, comments explaining key lines. If the code is
   already shown as a screenshot, do NOT duplicate it as a text `add_code`
   block — reference the figure instead.
5. Ask the user to save images under **fixed names** (e.g.
   `screenshot_task1.png`, `screenshot_task2.png`) into the report folder and
   re-run the script after saving — the conditional embedding picks them up.

## 7. Notes / anti-patterns

* **Never hand-draw the title page** (empty paragraphs, raw HTML) — the
  renderers already implement fig. А.1/А.2. Change only the `Report` fields.
* **Never write first-person text.** Before adding paragraphs, rewrite
  «я/ми зробив» → «розроблено/опановано/виконано».
* Images are **always user-provided** (see section 6). If the user gives only
  code without a screenshot — use `add_code`; never fabricate a screenshot.
  When the user supplies a screenshot, reference the figure in the text
  instead of duplicating the code as a text block.
* **Scheme content lessons (real review remarks):**
  - flowchart schemes are language-independent: terminators «Початок»/«Кінець»
    (never `START`, `return 0;`, `return -EINVAL;` inside scheme blocks),
    branch labels «Так»/«Ні» (never 1/0), Ukrainian labels only;
  - conditions must be inequality-to-zero checks (`x != 0 && y != 0 &&
    z != 0`) covering **every** denominator of the expression — including
    variables like z in `2.5y/z`; positivity checks (`x > 0`) are wrong;
  - the condition in the scheme, the report text and the code must be
    identical (a mismatch is a review remark on its own);
  - use ONE name for a variable everywhere (a real bug: `val[]` in the init
    block, `a[i]` in the condition); arrays need a visible input symbol
    (parallelogram), not just initialization;
  - scheme sizing: 11 elements for variant 10 means i = 1…11, not 10.
* **Schemes/diagrams:** light (white) background mandatory — dark themes are
  unreadable in print and violate the guide's examples. If generating
  programmatically, prefer draw.io XML (user edits/exports) or a high-DPI
  PIL render, then visually inspect the PNG before embedding.
* Skill path: `~/.agents/skills/lab-report/scripts/lab_report.py`.
  The generation script itself is created in the **current working
  directory**; import the module via `sys.path.insert(0, ...)` —
  do NOT run from, or write files into, the skill directory.
* Test example: `~/.agents/skills/lab-report/scripts/test_report.py`.
  Activate the venv before any run (run the script from the working directory):
  ```bash
  cd <working_directory>
  source ~/.venvs/lab-report/bin/activate
  python report_lab3.py
  ```
* Verify the final result with the Step 4 post-render checklist (render pages
  to PNG and read them — `pypdf` text checks alone are not enough), then hand
  both files to the user for review.
