#!/usr/bin/env python3
"""Test: generate a sample CD Report with all element types."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_report import (
    new_document, add_heading, add_paragraph, add_bullet_list,
    add_numbered_list, add_table, add_caption, add_page_break,
    save, verify_integrity,
)

OUT = "/tmp/CD_Report_Test.docx"

doc = new_document()

# ── Section 1: Introduction ────────────────────────────────────────
add_heading(doc, "1. Introduction", level=1)
add_paragraph(doc,
    "This document verifies that the template generates a .docx"
    " matching the CD_Report_(Horiz) corporate style.  It covers"
    " tables, bulleted and numbered lists, and formatted text"
    " in a single pass.")

# ── Section 2: Purpose ─────────────────────────────────────────────
add_heading(doc, "2. Purpose of the document", level=1)
add_paragraph(doc,
    "The purpose is to validate font sizes, heading styles, table"
    " formatting, and list rendering against the corporate template.")

# ── Section 3: References ──────────────────────────────────────────
add_heading(doc, "3. References", level=1)
add_paragraph(doc,
    "References to external resources and internal documents:")
add_numbered_list(doc, [
    ("Hubstaff task", " - internal tracking link"),
    ("CD_Report_(Horiz) template", " - Google Drive docs_refference"),
])

# ── Section 4: Abbreviations ───────────────────────────────────────
add_heading(doc, "4. Abbreviations, acronyms and definitions", level=1)

add_heading(doc, "4.1. Abbreviations and acronyms", level=2)
add_bullet_list(doc, [
    ("CD", " - Corporate Document"),
    ("HTML", " - HyperText Markup Language"),
])

add_heading(doc, "4.2. Definitions", level=2)
add_paragraph(doc,
    "Template: a pre-formatted document defining layout and structure"
    " for consistent report generation.")

# ── Section 5: Report results ──────────────────────────────────────
add_heading(doc, "5. Report results", level=1)
add_paragraph(doc,
    "The template supports tables, bulleted lists, numbered lists,"
    " and formatted text.")
add_caption(doc, "Table 1.", "Output format comparison")
add_table(doc,
    headers=["Format", "Convertible", "Notes"],
    rows=[
        [".docx",  "Yes", "Primary output"],
        [".pdf",   "Yes", "Via export"],
        [".html",  "No",  "Not supported"],
    ])
add_paragraph(doc, "Key capabilities:", bold=True)
add_bullet_list(doc, [
    "Automatic heading outline levels for TOC",
    "Styled table headers with bold text",
    "Native bullet and numbered lists via Word numbering",
])
add_paragraph(doc, "Generation steps:", bold=True)
add_numbered_list(doc, [
    ("Load the template .docx file", 0),
    ("Strip placeholder content from section 1 onwards", 0),
    ("Append user sections with content blocks", 0),
])

# ── Section 6: Conclusions ─────────────────────────────────────────
add_heading(doc, "6. Conclusions", level=1)
add_paragraph(doc,
    "All formatting elements render correctly in the generated file.")
add_heading(doc, "6.1. Verification conclusions", level=2)
add_paragraph(doc,
    "Pending review by the document verifier.")

# ── Save & verify ──────────────────────────────────────────────────
save(doc, OUT)
print(f"Saved: {OUT} ({os.path.getsize(OUT):,} bytes)")

checks = verify_integrity(OUT)
for key, val in checks.items():
    status = "PASS" if val else "FAIL"
    print(f"  [{status}] {key}")

if all(checks.values()):
    print("\nAll checks passed — ready for upload.")
else:
    print("\nFAILED — see above.")
    sys.exit(1)
