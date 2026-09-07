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

### Step 1. Collect the work's data
From the user (or the methodical guide / code in the working directory): work
number, topic, purpose («мета роботи»), body text in **third person**, program
code, conclusions, and title-page data (group, student name, teacher position
and name, faculty, department, year). Ask when data is missing — never invent.

### Step 2. Write the generation script
Create a script (e.g. `report_lab3.py`) importing the skill's module:

```python
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

### Step 3. Run and verify
```bash

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
* Skill path: `~/.agents/skills/lab-report/template/lab_report.py`
  (import via `sys.path.insert(0, ...)` or run from that directory).
* Test example: `~/.agents/skills/lab-report/template/test_report.py`.
source ~/.venvs/lab-report/bin/activate
python report_lab3.py
```
Verify the PDF with `pypdf` (title = page 1, description from page 2) and hand
both files to the user for review.
