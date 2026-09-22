# -*- coding: utf-8 -*-
"""Тестовий приклад для скіла lab-report («Програмування»).
Запуск: source ~/.venvs/lab-report/bin/activate && python test_report.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lab_report import (
    Report, add_paragraph, add_code, add_figure, add_formula, add_table,
    render_docx, render_pdf,
)

r = Report(
    work_number=3,
    topic="Тестова тема роботи",
    purpose="перевірка роботи шаблонного модуля.",
    variant=10,
    student_group="КІ-26-1",
    student_name="Т.М. Фролов",
    teacher_position="доцент каф. ІТКІ",
    teacher_name="І.М. Гаркуша",
)
add_paragraph(r, "В ході роботи перевірено роботу шаблонного модуля.")
add_formula(r, "S = 2x + 5y")
add_code(r, "print('test')\nprint('ok')")
add_table(r, ["x", "y"], [[1, 2], [3, 4]])
r.conclusions.append("В роботі перевірено роботу шаблонного модуля.")

out = "/tmp/test_report_prog"
os.makedirs(out, exist_ok=True)
render_docx(r, os.path.join(out, "test.docx"))
render_pdf(r, os.path.join(out, "test.pdf"))
