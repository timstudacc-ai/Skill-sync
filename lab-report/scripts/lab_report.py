# -*- coding: utf-8 -*-
"""
Шаблонний модуль скіла lab-report («Програмування», НТУ «Дніпровська
політехніка»). Реалізує Додаток А методички 2025 р.:
титульний аркуш за рис. А.1/А.2, A4, Times New Roman 14, інтервал 1.5,
абзацний відступ 1.25 см, вирівнювання по ширині, код — моноширинний 10,
рисунки/підписи/формули/таблиці — по центру.

Скрипти працюють ЛИШЕ у venv ~/.venvs/lab-report (модуль сам перевіряє).

Використання (скрипт генерації у робочій директорії):
    import os, sys
    sys.path.insert(0, os.path.expanduser(
        "~/.agents/skills/lab-report/scripts"))
    from lab_report import Report, add_paragraph, add_code, add_figure,
        add_formula, add_table, render_docx, render_pdf
"""
import os
import sys

if "lab-report" not in sys.prefix:
    sys.exit("Помилка: активуйте venv:  source ~/.venvs/lab-report/bin/activate")

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from weasyprint import HTML

MAIN_FONT = "Times New Roman"
FALLBACK_SERIF = "Liberation Serif"     # метричний аналог TNR для PDF
MONO_FONT = "DejaVu Sans Mono"
FIG_CAPTION = "Рисунок {} – {}"


class Report:
    """Дані звіту (незалежні від формату) + один рендер на формат."""

    def __init__(self, work_number, topic, purpose, *, variant=None,
                 ministry="Міністерство освіти і науки України",
                 university="Національний технічний університет\n"
                            "«Дніпровська політехніка»",
                 faculty="Факультет інформаційних технологій",
                 department="Кафедра інформаційних технологій та "
                            "комп'ютерної інженерії",
                 discipline="Програмування",
                 student_label="Виконав:",
                 student_group, student_name,
                 teacher_position, teacher_name,
                 city="Дніпро", year=None):
        import datetime
        self.work_number = work_number
        self.topic = topic
        self.purpose = purpose
        self.variant = variant
        self.ministry = ministry
        self.university = university
        self.faculty = faculty
        self.department = department
        self.discipline = discipline
        self.student_label = student_label
        self.student_group = student_group
        self.student_name = student_name
        self.teacher_position = teacher_position
        self.teacher_name = teacher_name
        self.city = city
        self.year = year or datetime.date.today().year
        self.body = []            # список блоків
        self.conclusions = []     # список абзаців висновків
        self.fig_n = 0
        self.formula_n = 0

    # --- конструктори блоків (викликаються скриптом генерації) -------------
    def _p(self, text):
        self.body.append(("p", text))

    def _f(self, text, number=None):
        self.formula_n += 1
        self.body.append(("f", text, number if number is not None
                          else self.formula_n))

    def _img(self, path, caption):
        self.fig_n += 1
        self.body.append(("img", path, caption, self.fig_n))
        return self.fig_n

    def _code(self, text):
        self.body.append(("code", text))

    def _table(self, headers, rows):
        self.body.append(("table", headers, rows))


def add_paragraph(r, text):
    """Абзац ходу роботи (justify, відступ 1.25 см)."""
    r._p(text)


def add_formula(r, text, number=None):
    """Формула по центру з номером «(N)» праворуч."""
    r._f(text, number)


def add_figure(r, image_path, caption):
    """Рисунок по центру + підпис «Рисунок N – caption» знизу."""
    return r._img(image_path, caption)


def add_code(r, text):
    """Блок коду: моноширинний 10 pt, вирівнювання строго ліворуч."""
    r._code(text)


def add_table(r, headers, rows):
    """Таблиця по центру з рамками, жирний заголовок."""
    r._table(headers, rows)


def _docx_p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False,
            size=14, indent=True, space_after=0, font=None):
    par = doc.add_paragraph()
    par.alignment = align
    fmt = par.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(space_after)
    if indent:
        fmt.first_line_indent = Cm(1.25)
    if text:
        run = par.add_run(text)
        run.font.name = font or MAIN_FONT
        run.font.size = Pt(size)
        run.bold = bold
    return par


def render_docx(r, path):
    c = WD_ALIGN_PARAGRAPH.CENTER
    j = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc = Document()
    for sec in doc.sections:                     # A4, поля 30/20/30/15 мм
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        sec.top_margin, sec.bottom_margin = Cm(3.0), Cm(2.0)
        sec.left_margin, sec.right_margin = Cm(3.0), Cm(1.5)

    # --- титульний аркуш (форма рис. А.1/А.2 методички) --------------------
    _docx_p(doc, r.ministry, c, bold=True, indent=False)
    for line in r.university.split("\n"):
        _docx_p(doc, line, c, bold=True, indent=False)
    _docx_p(doc, r.faculty, c, bold=True, indent=False)
    _docx_p(doc, r.department, c, bold=True, indent=False, space_after=24)
    _docx_p(doc, "Звіт", c, bold=True, indent=False, space_after=6)
    _docx_p(doc, f"з роботи №{r.work_number}", c, bold=True, indent=False,
            space_after=6)
    _docx_p(doc, f"дисципліни “{r.discipline}”", c, bold=True, indent=False,
            space_after=6)
    _docx_p(doc, f"Тема роботи: «{r.topic}»", c, bold=True, indent=False,
            space_after=48)
    for line in (r.student_label, f"студент гр. {r.student_group}",
                 r.student_name, "Перевірив:", r.teacher_position,
                 r.teacher_name):
        _docx_p(doc, line, WD_ALIGN_PARAGRAPH.RIGHT, bold=True, indent=False,
                space_after=6)
    _docx_p(doc, "", c, indent=False, space_after=60)
    _docx_p(doc, r.city, c, bold=True, indent=False)
    _docx_p(doc, str(r.year), c, bold=True, indent=False)
    doc.add_page_break()

    # --- опис роботи --------------------------------------------------------
    _docx_p(doc, f"Робота №{r.work_number}", c, bold=True, indent=False,
            space_after=6)
    _docx_p(doc, r.topic, c, bold=True, indent=False)
    _docx_p(doc, f"Мета роботи: {r.purpose}", j)
    if r.variant is not None:
        _docx_p(doc, "Хід роботи", c, bold=True, indent=False, space_after=6)
        _docx_p(doc, f"Варіант {r.variant}", c, bold=True, indent=False)

    for block in r.body:
        kind = block[0]
        if kind == "p":
            _docx_p(doc, block[1], j)
        elif kind == "f":
            par = _docx_p(doc, "", c, indent=False)
            par.add_run(f"{block[1]}\t\t\t({block[2]})")
        elif kind == "img":
            _, img_path, caption, n = block
            par = _docx_p(doc, "", c, indent=False)
            par.add_run().add_picture(img_path, width=Cm(15.0))
            _docx_p(doc, FIG_CAPTION.format(n, caption), c, indent=False)
        elif kind == "code":
            _docx_p(doc, block[1], WD_ALIGN_PARAGRAPH.LEFT, indent=False,
                    size=10, font=MONO_FONT)
        elif kind == "table":
            _, headers, rows = block
            tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
            tbl.style = "Table Grid"
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            for col, h in enumerate(headers):
                cell = tbl.rows[0].cells[col]
                cell.text = h
                cell.paragraphs[0].runs[0].bold = True
            for row_i, row in enumerate(rows, start=1):
                for col, val in enumerate(row):
                    tbl.rows[row_i].cells[col].text = str(val)
            _docx_p(doc, "", c, indent=False)

    _docx_p(doc, "Висновки", c, bold=True, indent=False, space_after=6)
    for text in r.conclusions:
        _docx_p(doc, text, j)
    doc.save(path)
    print("DOCX:", path)



def render_pdf(r, path):
    esc = (lambda s: s.replace("&", "&amp;").replace("<", "&lt;"))
    fig_n, blocks = 0, []
    for block in r.body:
        kind = block[0]
        if kind == "p":
            blocks.append(f"<p>{esc(block[1])}</p>")
        elif kind == "f":
            blocks.append(f'<p class="formula">{esc(block[1])}'
                          f'<span class="fnum">({block[2]})</span></p>')
        elif kind == "img":
            _, img_path, caption, n = block
            blocks.append(
                '<div class="fig">'
                f'<img src="file://{os.path.abspath(img_path)}">'
                f'<p class="cap">{FIG_CAPTION.format(n, esc(caption))}'
                '</p></div>')
        elif kind == "code":
            lines = esc(block[1]).replace("\n", "<br>")
            blocks.append(f'<p class="code">{lines}</p>')
        elif kind == "table":
            _, headers, rows = block
            head = "".join(f"<th>{esc(h)}</th>" for h in headers)
            body = "".join("<tr>" + "".join(f"<td>{esc(str(v))}</td>"
                          for v in row) + "</tr>" for row in rows)
            blocks.append(f'<table><thead><tr>{head}</tr></thead>'
                          f'<tbody>{body}</tbody></table>')

    univ = "</p><p class='c'>".join(esc(r.university).split("\n"))
    concl = "".join(f"<p>{esc(x)}</p>" for x in r.conclusions)
    variant_html = ""
    if r.variant is not None:
        variant_html = ('<p class="c gap">Хід роботи</p>'
                        f'<p class="c">Варіант {r.variant}</p>')
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    @page {{ size: A4; margin: 30mm 20mm 20mm 30mm; }}
    body {{ font-family: "{MAIN_FONT}", "{FALLBACK_SERIF}", serif;
            font-size: 14pt; line-height: 1.5; text-align: justify; }}
    p {{ margin: 0; text-indent: 1.25cm; }}
    .c {{ text-align: center; text-indent: 0; font-weight: bold; }}
    .gap {{ margin-top: 24pt; }}
    .right {{ text-align: right; text-indent: 0; font-weight: bold;
              margin-left: 7.5cm; }}
    .formula {{ text-align: center; text-indent: 0; }}
    .fnum {{ float: right; margin-right: 8mm; }}
    .fig {{ text-align: center; page-break-inside: avoid; margin: 6pt 0; }}
    .fig img {{ max-width: 15cm; }}
    .fig .cap {{ text-align: center; text-indent: 0; }}
    .code {{ font-family: "{MONO_FONT}", monospace; font-size: 10pt;
             text-align: left; text-indent: 0; line-height: 1.2; }}
    table {{ border-collapse: collapse; margin: 6pt auto; }}
    th, td {{ border: 1px solid #000; padding: 2pt 6pt;
              font-size: 12pt; text-align: center; }}
    th {{ font-weight: bold; }}
    .pb {{ page-break-after: always; }}
    </style></head><body>
    <p class="c">{esc(r.ministry)}</p>
    <p class="c">{univ}</p>
    <p class="c">{esc(r.faculty)}</p>
    <p class="c gap">{esc(r.department)}</p>
    <p class="c" style="margin-top:60pt">Звіт</p>
    <p class="c">з роботи №{r.work_number}</p>
    <p class="c">дисципліни “{esc(r.discipline)}”</p>
    <p class="c gap">Тема роботи: «{esc(r.topic)}»</p>
    <p class="right gap">{esc(r.student_label)}</p>
    <p class="right">студент гр. {esc(r.student_group)}</p>
    <p class="right">{esc(r.student_name)}</p>
    <p class="right gap">Перевірив:</p>
    <p class="right">{esc(r.teacher_position)}</p>
    <p class="right">{esc(r.teacher_name)}</p>
    <p class="c" style="margin-top:90pt">{esc(r.city)}</p>
    <p class="c">{r.year}</p>
    <div class="pb"></div>
    <p class="c">Робота №{r.work_number}</p>
    <p class="c">{esc(r.topic)}</p>
    <p><b>Мета роботи:</b> {esc(r.purpose)}</p>
    {variant_html}
    {''.join(blocks)}
    <p class="c gap">Висновки</p>
    {concl}
    </body></html>"""
    HTML(string=html).write_pdf(path)
    print("PDF :", path)

