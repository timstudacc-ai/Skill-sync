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
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

__all__ = [
    "new_document", "save", "verify_integrity",
    "add_heading", "add_paragraph", "add_caption",
    "add_table_caption", "add_figure_caption",
    "add_bullet_list", "add_numbered_list", "add_table",
    "add_glossary_table", "add_page_break",
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
            # scripts/ and assets/ are siblings inside the skill directory
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "CD_Report_template.docx",
        )
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"template not found: {template_path}\n"
            "Expected the original CD_Report_(Horiz) .docx in the skill's assets/ "
            "directory (sibling of scripts/)."
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
    """Add a section heading using the template's Heading{level} style.

    Corporate review comment #2 — heading numbering convention: every level
    of the manual number ends with a dot, e.g. ``5.``, ``5.1.``, ``5.1.2.``
    (``5.1`` without the trailing dot is incorrect). Callers pass the full
    numbered text; verify numbering style before delivery.
    """
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
    """Add a plain body paragraph (template 'Normal' style).

    Corporate formatting rule (Canyon verification / AL Handbook): body text is
    JUSTIFIED by default so both edges are even. Pass ``alignment="left"`` or
    ``"center"`` to override (e.g. for centered figure placeholders).
    """
    p = doc.add_paragraph(text)
    if alignment:
        p.alignment = getattr(WD_ALIGN_PARAGRAPH, alignment.upper(), None)
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
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


def add_table_caption(doc: Document, label: str, text: str | None = None) -> object:
    """Caption for a data table — LEFT-aligned (corporate review comment #5).

    Renders as ``Table N. - Description``. The label part (``Table N.``) is
    BOLD + italic, the description is italic (review round 2).
    """
    return _add_caption(doc, label, text, WD_ALIGN_PARAGRAPH.LEFT)


def add_figure_caption(doc: Document, label: str, text: str | None = None) -> object:
    """Caption for a figure — CENTER-aligned (corporate review comment #4).

    Renders as ``Figure N. - Description``. The label part (``Figure N.``) is
    BOLD + italic, the description is italic (review round 2).
    """
    return _add_caption(doc, label, text, WD_ALIGN_PARAGRAPH.CENTER)


def _add_caption(doc: Document, label: str, text: str | None, alignment) -> object:
    """Shared caption renderer: bold-italic label, italic description."""
    p = doc.add_paragraph()
    run = p.add_run(label)
    run.bold = True
    run.italic = True
    if text is not None:
        rest = p.add_run(f" - {text}")
        rest.italic = True
    p.alignment = alignment
    return p


# ──────────────────────────────────────────────────────────────────────────────
# List helpers — REAL Word lists (numPr), not fake bullet-prefix text
# ──────────────────────────────────────────────────────────────────────────────

_NUM_FMT = {0: "bullet", 1: "decimal"}
_NUM_TEXT = {0: "\u2022", 1: "%1."}


def _get_numbering_part(doc: Document):
    """Return the document's numbering part, creating it if missing.

    ``NumberingPart.new()`` is not implemented in python-docx, so a part is
    built manually via the OPC layer: a bare ``<w:numbering>`` element plus a
    package relationship of type ``NUMBERING`` — the standard part Word and
    Google Docs expect, only constructed by hand.
    """
    try:
        return doc.part.numbering_part
    except Exception:
        from docx.opc.constants import CONTENT_TYPE as CT, RELATIONSHIP_TYPE as RT
        from docx.opc.packuri import PackURI
        from docx.parts.numbering import NumberingPart

        el = OxmlElement("w:numbering")
        part = NumberingPart(
            PackURI("/word/numbering.xml"), CT.WML_NUMBERING, el, doc.part.package
        )
        doc.part.relate_to(part, RT.NUMBERING)
        return part


def _ensure_list_numbering(doc: Document, kind: int) -> int:
    """Ensure a numbering definition exists for kind (0=bullet, 1=decimal).

    Returns the ``w:numId`` to reference. The CD template already carries a
    numbering part with unrelated definitions, so we only append our own
    (tagged via ``w:tplc`` for reuse) — never touch existing ones. Schema
    order inside ``<w:numbering>`` is ``abstractNum*`` then ``num*``, so the
    ``abstractNum`` is inserted before the first existing ``w:num``.
    """
    numbering = _get_numbering_part(doc).element
    fmt = _NUM_FMT.get(kind, "bullet")
    tag = f"ourlist{kind:04d}"
    for an in numbering.findall(qn("w:abstractNum")):
        # w:tplc is set as an ATTRIBUTE on abstractNum (see below), not a child.
        if an.get(qn("w:tplc")) == tag:
            # By construction our w:num carries numId == abstractNumId.
            return int(an.get(qn("w:abstractNumId")))
    abs_id = 90
    used_abs = {int(a.get(qn("w:abstractNumId"))) for a in numbering.findall(qn("w:abstractNum"))}
    used_num = {int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))}
    while abs_id in used_abs or abs_id in used_num:
        abs_id += 1
    an = OxmlElement("w:abstractNum")
    an.set(qn("w:abstractNumId"), str(abs_id))
    an.set(qn("w:tplc"), tag)
    lvl = OxmlElement("w:lvl")
    lvl.set(qn("w:ilvl"), "0")
    # Review round 2: without an explicit w:start Google Docs starts the
    # decimal counter at 0. Word defaults to 1, GDocs does not — set it.
    st = OxmlElement("w:start"); st.set(qn("w:val"), "1"); lvl.append(st)
    nf = OxmlElement("w:numFmt"); nf.set(qn("w:val"), fmt); lvl.append(nf)
    lt = OxmlElement("w:lvlText"); lt.set(qn("w:val"), _NUM_TEXT[kind]); lvl.append(lt)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "720"); ind.set(qn("w:hanging"), "360")
    lvl.append(ind)
    an.append(lvl)
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(abs_id))
    aref = OxmlElement("w:abstractNumId"); aref.set(qn("w:val"), str(abs_id)); num.append(aref)
    existing_nums = numbering.findall(qn("w:num"))
    if existing_nums:
        existing_nums[0].addprevious(an)
    else:
        numbering.append(an)
    numbering.append(num)
    return abs_id


def _add_list_item(
    doc: Document,
    text: str,
    *,
    bullet: bool,
    level: int = 0,
    number: int | None = None,
) -> object:
    """Add one list item as a REAL Word list paragraph (``w:numPr``).

    Corporate review comment #6: lists rendered as manual ``• ``/``1. `` text
    prefixes do not survive the .docx → Google Doc conversion as list objects
    — Google Docs reads them as plain paragraphs. The only reliable way to
    produce a native list is a numbering definition (``w:abstractNum``/``w:num``
    in numbering.xml) referenced from the paragraph via ``w:numPr``.
    """
    num_id = _ensure_list_numbering(doc, 0 if bullet else 1)
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0"); numPr.append(ilvl)
    id_el = OxmlElement("w:numId"); id_el.set(qn("w:val"), str(num_id)); numPr.append(id_el)
    pPr.append(numPr)
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
    """Add a data table with a bold header row and visible single-line borders.

    Corporate data-table rules (Canyon "Verification of documents" / AL
    Handbook):
      * header row is bold on a subtle background fill, visually separating
        column names from data;
      * ALL cells are left-aligned;
      * the header row repeats on every page the table spans (the .docx
        equivalent of "pin the header row" for multi-page tables).

    Column widths are set explicitly so the table never exceeds the section's
    text area.  By default each column gets an equal share of the usable width.
    Override with ``col_widths`` (list of EMU values, one per column) if needed.
    """
    if caption:
        add_table_caption(doc, "Table", caption)

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

    # Corporate rules: every cell left-aligned, header repeats across pages
    _left_align_table(tbl)
    _repeat_header_row(tbl.rows[0])
    return tbl


def _left_align_table(tbl) -> None:
    """Normalize every cell paragraph (corporate review comments #1 and #7).

    * left-align all text inside tables (rule #7);
    * strip inherited indents: cell paragraphs copy the 'Normal' style's
      first-line indent, which renders as a redundant leading gap inside
      every cell (rule #1). Word tables are already inset by cell margins,
      so cell paragraphs must carry zero left/first-line indent.
    """
    for row in tbl.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.left_indent = Pt(0)
                p.paragraph_format.first_line_indent = Pt(0)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)


def _repeat_header_row(row) -> None:
    """Mark the first table row to repeat on every page the table spans.

    Implements the Canyon rule "закрепить шапку таблицы" for multi-page tables:
    in Word/.docx this is the ``w:tblHeader`` row property.
    """
    tr_pr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def add_glossary_table(
    doc: Document,
    rows,
    *,
    col_widths: list[int] | None = None,
) -> object:
    """Add a corporate glossary table (Abbreviations 4.1 / Definitions 4.2).

    Glossary style — deliberately distinct from data tables:
      * NO header row: rows start directly at the data;
      * NO borders: the section reads as a definition list, not a grid;
      * the first column (abbreviation / defined term) is bold;
      * all cells are left-aligned.

    ``rows`` is a list of lists (or tuples); the first element of each row is
    rendered bold. For a 2-column table the first column defaults to ~28% of
    the usable width.
    """
    n_cols = len(rows[0])
    if col_widths is None:
        usable_w = _section_usable_width(doc)
        if n_cols == 2:
            col_widths = [int(usable_w * 0.28), usable_w - int(usable_w * 0.28)]
        else:
            col_widths = [usable_w // n_cols] * n_cols
    tbl = doc.add_table(rows=len(rows), cols=n_cols)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = str(val)
            cell.width = col_widths[j]
            if j == 0:
                for run in cell.paragraphs[0].runs:
                    run.bold = True
    _left_align_table(tbl)
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