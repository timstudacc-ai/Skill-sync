#!/usr/bin/env python3
"""Generate a corporate CD_Report_(Horiz)-style .docx.

Strategy (the correct one):
  * OPEN the original corporate template .docx as the base. This preserves the
    exact front page (Document name, Document history / Verification tables,
    Contents) which is fragile to rebuild by hand.
  * STRIP only the placeholder body from the first Heading 1 ("1. Introduction")
    onward, then APPEND the report's real content using the template's built-in
    styles (Heading 1 / Heading 2 / Normal).

This module is deliberately FLAT (module-level functions, no class wrapper).
The template's style list has NO built-in list or table styles ("List Bullet",
"Table Grid", etc.), so lists and table borders are rendered manually as a
fallback and the model keeps the original font/size styling.

API (import as `from generate_report import ...`):
    new_document(template_path=None) -> Document   # opens + strips placeholder
    save(doc, path)
    verify_integrity(path) -> dict of bool checks
    add_heading(doc, text, level=1)
    add_paragraph(doc, text='', *, bold=False, italic=False, alignment=None)
    add_caption(doc, label, text=None)              # "Table 1. - Description"
    add_bullet_list(doc, items)                     # items: list[str]
    add_numbered_list(doc, items)                   # items: list[(text, appendix)]
    add_table(doc, headers, rows, *, caption=None)  # manual borders, bold header
    add_page_break(doc)
"""

from __future__ import annotations

import os

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

__all__ = [
    "new_document", "save", "verify_integrity",
    "add_heading", "add_paragraph", "add_caption",
    "add_bullet_list", "add_numbered_list", "add_table", "add_page_break",
]

# Headings map straight onto the template's built-in styles.
_SECTION_HEADINGS = {
    0: "Title",
    1: "Heading 1",
    2: "Heading 2",
    3: "Heading 3",
}
# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle
# ──────────────────────────────────────────────────────────────────────────────

def new_document(template_path: str | None = None, *, start_marker: str | None = None) -> Document:
    """Open the corporate template and discard its placeholder body.

    Title page (through "Contents") stays untouched. Everything from the first
    Heading-1 onwards — paragraphs AND tables — is removed so the caller can
    append fresh section content.

    Args:
        start_marker: Optional override. If given, the first paragraph whose
            text starts with this string becomes the body start (replacing the
            default "first Heading 1" detection).
    """
    if template_path is None:
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "CD_Report_template.docx",
        )
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"template not found: {template_path}\n"
            "Expected the original CD_Report_(Horiz) .docx alongside this module."
        )
    doc = Document(template_path)
    _strip_body(doc, start_marker=start_marker)
    return doc


def save(doc: Document, path: str) -> str:
    """Serialize the document to `path`, creating parent dirs if needed."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    doc.save(path)
    return path


def verify_integrity(path: str) -> dict[str, bool]:
    """Smoke-test a saved .docx: reopen it and confirm the essentials."""
    reopened = Document(path)
    return {
        "openable": True,
        "front_matter_intact": _count_front_paragraphs(reopened) >= 8,
        "intro_section": any(
            "Introduction" in p.text for p in reopened.paragraphs
        ),
        "has_tables": len(reopened.tables) >= 2,
    }


def _strip_body(doc: Document, *, start_marker: str | None = None) -> None:
    """Remove placeholder body from the first Heading-1 paragraph to the end.

    Preserves the final <w:sectPr> element so the body section's page setup
    (landscape, portrait, margins, page size) is retained.

    Args:
        start_marker: Optional override. If given, the first paragraph whose
            text starts with this string becomes the body start. When ``None``
            the first ``Heading 1`` paragraph is used.
    """
    start_el = None
    if start_marker is not None:
        for p in doc.paragraphs:
            if p.text.strip().startswith(start_marker):
                start_el = p._element
                break
    if start_el is None:
        for p in doc.paragraphs:
            if p.style.name == "Heading 1":
                start_el = p._element
                break
    if start_el is None:
        return  # nothing to strip

    body = doc.element.body
    children = list(body)
    try:
        idx = next(i for i, c in enumerate(children) if c is start_el)
    except StopIteration:
        return
    # Remove only <w:p> and <w:tbl> — keep any <w:sectPr> at the end so the
    # body section's page setup (size, orientation, margins) is preserved.
    for child in children[idx:]:
        if child.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(child)


def _count_front_paragraphs(doc: Document) -> int:
    """Count paragraphs before the first Heading 1 (i.e. the locked front)."""
    n = 0
    for p in doc.paragraphs:
        if p.style.name == "Heading 1":
            break
        n += 1
    return n


# ──────────────────────────────────────────────────────────────────────────────
# Content blocks
# ──────────────────────────────────────────────────────────────────────────────


def add_heading(doc: Document, text: str, level: int = 1) -> object:
    """Add a section heading using the template's Heading{level} style."""
    style_name = _SECTION_HEADINGS.get(level, f"Heading {level}")
    # Fall back gracefully if the template lacks the exact Heading style.
    if style_name not in doc.styles:
        style_name = "Heading 1"
    p = doc.add_paragraph(text)
    p.style = doc.styles[style_name]
    return p


def add_paragraph(
    doc: Document,
    text: str = "",
    *,
    bold: bool = False,
    italic: bool = False,
    alignment: str | None = None,
) -> object:
    """Add a plain body paragraph (template 'Normal' style)."""
    p = doc.add_paragraph(text)
    if alignment:
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        p.alignment = getattr(WD_ALIGN_PARAGRAPH, alignment.upper(), None)
    for run in p.runs:
        if bold:
            run.bold = True
        if italic:
            run.italic = True
    return p


def add_caption(doc: Document, label: str, text: str | None = None) -> object:
    """Add a small caption line, e.g. ``add_caption(doc, "Table 1.", "Output")``.

    Renders as ``Table 1. - Output`` (single italic paragraph). The template's
    own examples use a space around the dash.
    """
    full = label if text is None else f"{label} - {text}"
    p = doc.add_paragraph()
    run = p.add_run(full)
    run.italic = True
    return p


# ──────────────────────────────────────────────────────────────────────────────
# List helpers
# ──────────────────────────────────────────────────────────────────────────────


def _add_list_item(
    doc: Document,
    text: str,
    *,
    bullet: bool,
    level: int = 0,
    number: int | None = None,
) -> object:
    """Add one list item, using the template's list style if it exists.

    The corporate template ships WITHOUT list styles, so we fall back to a
    manual indent + bullet / number prefix. This keeps the original fonts and
    still renders a proper-looking list.
    """
    candidates = (
        ["List Bullet", "List Bullet 2", "List Bullet 3"]
        if bullet
        else ["List Number", "List Number 2", "List Number 3"]
    )
    p = doc.add_paragraph()
    applied = False
    if level < len(candidates):
        try:
            p.style = doc.styles[candidates[level]]
            applied = True
        except Exception:
            applied = False
    if not applied:
        prefix = "• " if bullet else f"{number or 1}. "
        indent = Pt(24 * (level + 1) * (0.5 if bullet else 1))
        p.paragraph_format.left_indent = indent
        p.add_run(prefix)
    p.add_run(text)
    return p


def add_bullet_list(doc: Document, items) -> list:
    """Add a bulleted list.  ``items`` = list of str, or list of
    ``(text, suffix)`` tuples where suffix is a string appended to the
    bullet text (e.g. ``("CD", " - Corporate Document")``)."""
    added = []
    for item in items:
        if isinstance(item, tuple):
            # Merge tuple elements into one bullet string, don't iterate
            # over characters of a string suffix.
            text = "".join(str(x) for x in item)
        else:
            text = item
        added.append(_add_list_item(doc, text, bullet=True, level=0))
    return added


def add_numbered_list(doc: Document, items) -> list:
    """Add a numbered list.  ``items`` = list of ``(text, appendix)``
    tuples where appendix is 0 (nothing) or a string suffix."""
    added = []
    for idx, item in enumerate(items, start=1):
        if isinstance(item, tuple):
            text = item[0]
            appendix = item[1] if len(item) > 1 else 0
            suffix = "" if appendix == 0 else str(appendix)
            added.append(_add_list_item(doc, text + suffix, bullet=False, number=idx))
        else:
            added.append(_add_list_item(doc, item, bullet=False, number=idx))
    return added


# ──────────────────────────────────────────────────────────────────────────────
# Tables — manual borders (template has no "Table Grid" style)
# ──────────────────────────────────────────────────────────────────────────────


def _section_usable_width(doc: Document) -> int:
    """Return the usable text width (EMU) of the last section in the doc.

    Usable width = page_width − left_margin − right_margin.
    This is the space available for tables and body text.
    """
    sec = doc.sections[-1]
    return sec.page_width - sec.left_margin - sec.right_margin


def add_table(
    doc: Document,
    headers,
    rows,
    *,
    caption: str | None = None,
    col_widths: list[int] | None = None,
) -> object:
    """Add a table with a bold header row and visible single-line borders.

    Column widths are set explicitly so the table never exceeds the section's
    text area.  By default each column gets an equal share of the usable width.
    Override with ``col_widths`` (list of EMU values, one per column) if needed.
    """
    if caption:
        add_caption(doc, "Table", caption)

    n_cols = len(headers)
    usable_w = _section_usable_width(doc)
    if col_widths is None:
        col_widths = [usable_w // n_cols] * n_cols

    tbl = doc.add_table(rows=1 + len(rows), cols=n_cols)

    # Set the table's total width to the usable width (EMU value).
    tblPr = tbl._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:type"), "pct")        # percentage of page content width
    tblW.set(qn("w:w"), "5000")          # 5000 = 100%

    # Header row
    for j, hdr in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = str(hdr)
        cell.width = col_widths[j]
        _set_borders(cell)
        _set_fill(cell, "D9D9D9")
        for run in cell.paragraphs[0].runs:
            run.bold = True

    # Body rows
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(val)
            cell.width = col_widths[j]
            _set_borders(cell)
    return tbl


def _set_borders(cell) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")  # 0.5 pt
        el.set(qn("w:color"), "000000")
        tc_borders.append(el)
    tc_pr.append(tc_borders)


def _set_fill(cell, hex_fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


# ──────────────────────────────────────────────────────────────────────────────
# Misc
# ──────────────────────────────────────────────────────────────────────────────


def add_page_break(doc: Document) -> None:
    """Append a page break."""
    doc.add_page_break()