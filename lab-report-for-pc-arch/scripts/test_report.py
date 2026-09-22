# -*- coding: utf-8 -*-
"""Тестовий приклад для скіла lab-report-for-pc-arch.
Запуск: source ~/.venvs/lab-report/bin/activate && python test_report.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab_report import (
    Report, add_paragraph, add_code, add_figure, add_formula, add_table,
    render_docx, render_pdf,
)

r = Report(
    work_number=1,
    topic="Збирання системного блоку персонального комп'ютера",
    purpose="ознайомитися з компонентами системного блоку та опанувати "
            "послідовність збирання персонального комп'ютера.",
    student_label="Виконала студентка групи",   # або "Виконав студент групи"
    student_group="124-20-2",
    student_name="Голоденко Аріадна Олексіївна",
    teacher_label="Перевірив",
    teacher_position="Доц.",
    teacher_name="Ткаченко С.М.",
    city="Дніпро",
    year=2020,
)
add_paragraph(r, "В ході роботи вивчено призначення основних компонентів …")
add_code(r, "CPU: Intel Core i5-10400\nRAM: 16 GB DDR4\nSSD: 512 GB")
add_table(r, ["Компонент", "Модель"], [["CPU", "i5-10400"]])
r.conclusions.append("В роботі розглянуті основні компоненти системного "
                     "блоку. …")

out = "/tmp/test_report_pcarch"
os.makedirs(out, exist_ok=True)
render_docx(r, os.path.join(out, "test.docx"))
render_pdf(r, os.path.join(out, "test.pdf"))
