# -*- coding: utf-8 -*-
"""
Шаблонний модуль скіла lab-report-for-pc-arch («Архітектура комп'ютера»).
Титульний аркуш за зразком «Титульний лист лабораторних робіт.docx»:
  шапка — лише «Міністерство науки і освіти України» (центр, жирний), БЕЗ
  університету/факультету/кафедри; назва роботи та дисципліна жирним по
  центру; тема ВЕРХНІМ регістром; блок виконавця з відступом 11.25 см
  праворуч; «м. Дніпро» / «2020 рік» внизу по центру.
Основний текст — за правилами НТУ «Дніпровська політехніка» (A4, TNR 14,
інтервал 1.5, відступ 1.25 см, по ширині, код — моно 10, рисунки — центр).

Скрипти працюють ЛИШЕ у venv ~/.venvs/lab-report (модуль сам перевіряє).

Використання (скрипт генерації у робочій директорії):
    import os, sys
    sys.path.insert(0, os.path.expanduser(
        "~/.agents/skills/lab-report-for-pc-arch/template"))
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
                 ministry="Міністерство науки і освіти України",
                 discipline="Архітектура комп'ютера",
                 student_label="Виконала студентка групи",   # стать виконавця!
                 student_group, student_name,
                 teacher_label="Перевірив",                  # стать викладача!
                 teacher_position, teacher_name,
                 city="Дніпро", year=None):
        import datetime
        self.work_number = work_number
        self.topic = topic
        self.purpose = purpose
        self.variant = variant
        self.ministry = ministry
        self.discipline = discipline
        self.student_label = student_label
        self.student_group = student_group
        self.student_name = student_name
        self.teacher_label = teacher_label
        self.teacher_position = teacher_position
        self.teacher_name = teacher_name
        self.city = city
        self.year = year or datetime.date.today().year
        self.body = []            # список блоків
        self.conclusions = []     # список абзаців висновків

    # --- конструктори блоків (викликаються скриптом генерації) -------------
    def _p(self, text):
        self.body.append(("p", text))

    def _f(self, text, number):
        self.body.append(("f", text, number))

    def _img(self, path, caption):
        n = sum(1 for b in self.body if b[0] == "img") + 1
        self.body.append(("img", path, caption, n))
        return n

    def _code(self, text):
        self.body.append(("code", text))

    def _table(self, headers, rows):
        self.body.append(("table", headers, rows))


def add_paragraph(r, text):
    """Абзац ходу роботи (justify, відступ 1.25 см)."""
    r._p(text)


def add_formula(r, text, number):
    """Формула по центру з номером «(number)» праворуч."""
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

    # --- титульний аркуш (за зразком docx, ВІДМІННИЙ від «Програмування») --
    _docx_p(doc, r.ministry, c, bold=True, indent=False, space_after=48)
    _docx_p(doc, f"Звіт з лабораторної роботи №{r.work_number}", c,
            bold=True, indent=False, space_after=6)
    _docx_p(doc, f"З дисципліни «{r.discipline}»", c, bold=True,
            indent=False, space_after=6)
    _docx_p(doc, f"Тема: “{r.topic.upper()}”", c, bold=True, indent=False,
            space_after=48)
    # блок виконавця/викладача: відступ 11.25 см праворуч (відступ зліва)
    right = doc.add_paragraph()
    right.paragraph_format.left_indent = Cm(11.25)
    right.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    for run_text in (f"{r.student_label} {r.student_group}",
                     r.student_name,
                     f"{r.teacher_label} {r.teacher_position} "
                     f"{r.teacher_name}"):
        run = right.add_run(run_text + "\n")
        run.font.name = MAIN_FONT
        run.font.size = Pt(14)
        run.bold = True
    _docx_p(doc, "", c, indent=False, space_after=60)
    _docx_p(doc, f"м. {r.city}", c, bold=True, indent=False)
    _docx_p(doc, f"{r.year} рік", c, bold=True, indent=False)
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
            par.add_run().add_picture(img_path, width=Cm(14.0))
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
    blocks = []
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
    .indent {{ text-indent: 0; font-weight: bold;
               margin-left: 11.25cm; }}
    .formula {{ text-align: center; text-indent: 0; }}
    .fnum {{ float: right; margin-right: 8mm; }}
    .fig {{ text-align: center; page-break-inside: avoid; margin: 6pt 0; }}
    .fig img {{ max-width: 14cm; }}
    .fig .cap {{ text-align: center; text-indent: 0; }}
    .code {{ font-family: "{MONO_FONT}", monospace; font-size: 10pt;
             text-align: left; text-indent: 0; line-height: 1.2; }}
    table {{ border-collapse: collapse; margin: 6pt auto; }}
    th, td {{ border: 1px solid #000; padding: 2pt 6pt;
              font-size: 12pt; text-align: center; }}
    th {{ font-weight: bold; }}
    .pb {{ page-break-after: always; }}
    </style></head><body>
    <p class="c" style="margin-bottom:48pt">{esc(r.ministry)}</p>
    <p class="c">Звіт з лабораторної роботи №{r.work_number}</p>
    <p class="c">З дисципліни «{esc(r.discipline)}»</p>
    <p class="c gap">Тема: “{esc(r.topic.upper())}”</p>
    <p class="indent gap">{esc(r.student_label)} {esc(r.student_group)}</p>
    <p class="indent">{esc(r.student_name)}</p>
    <p class="indent gap">{esc(r.teacher_label)} {esc(r.teacher_position)}
       {esc(r.teacher_name)}</p>
    <p class="c" style="margin-top:90pt">м. {esc(r.city)}</p>
    <p class="c">{r.year} рік</p>
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

