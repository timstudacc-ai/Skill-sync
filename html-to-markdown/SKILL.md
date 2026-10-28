---
name: html-to-markdown
description: Converts HTML-based documentation sites (Doxygen, MkDocs, Docusaurus, Sphinx, plain HTML) into Markdown (.md) files — one .md per documentation section containing the full text of all its child pages, with site chrome and boilerplate stripped and headings, links, code blocks, tables, and images preserved as proper Markdown. Falls back to plain .txt output (the old html-docs-to-txt behavior) when the Markdown libraries are unavailable or the user explicitly wants text files. Use whenever the user asks to download/convert/scrape/dump an online documentation site into Markdown, .md, or plain-text files — e.g. "I need full documentation of library X in markdown", "convert this docs site to .md", "1 file per section with all child pages", "save this documentation locally so I can read it offline" — even if the user never says the word "markdown".
---

# HTML Docs → Markdown (.md) Files

Convert an HTML documentation site into a set of Markdown files. The
default deliverable (the "definition of done" pattern most users mean):

> **One .md file per documentation section (Overview, Design,
> Configuration, …), each containing the full text of all its child
> pages.**

The conversion tool is `scripts/html_docs_to_md.py`. It produces real
Markdown — fenced code blocks, `#` headings, `[link](url)` references,
pipe tables — not just stripped text.

## Dependencies (one-time setup)

The Markdown path uses two external libraries — **html2text** and
**beautifulsoup4** — installed in the skill's private venv, *not* the
system Python:

```bash
bash scripts/ensure_venv.sh   # creates scripts/.venv, installs both libs
```

The tool handles the rest itself: when asked for Markdown output
(default), it re-executes itself with the venv interpreter, so running
plain `python3 scripts/html_docs_to_md.py …` just works. If the venv is
missing (fresh checkout, offline machine), the tool automatically
degrades to the **txt fallback** — stdlib-only plain-text output,
identical to the original html-docs-to-txt behavior — and prints a
warning telling you to run `ensure_venv.sh`. Explicit txt output is also
available anytime via `--format txt` / `--txt`.

## Workflow

### 1. Recon the site (never skip)

Fetch the index URL and determine what generator produced the docs:

- **Doxygen** (e.g. freertos.github.io/coreMQTT): the nav sidebar is
  rendered by JavaScript, so the visible HTML contains *no* nav links.
  The source of truth is `navtreedata.js` — fetch it and look for
  `var NAVTREE`. Tool mode `doxygen` handles this automatically.
- **MkDocs / Docusaurus / Sphinx / plain HTML**: real `<a href>` links
  exist in the HTML. Tool mode `crawl` does a same-host BFS over `.html`
  links.

Ask the user (or infer) the output layout if not stated:
- default: one .md **per section** (child pages appended under
  `---` / `> Source:` separators)
- `--flat`: everything in one `ALL_DOCS.md`
- `--per-page`: one .md per page

### 2. Run the tool

```bash
python3 scripts/html_docs_to_md.py <BASE_URL> \
    --out <output_dir>          # e.g. ./docs/<LibName>_<version>
# useful flags:
#   --format md|txt             md is the default; txt = plain-text fallback
#   --txt                       shorthand for --format txt
#   --mode doxygen|crawl|auto   (auto is default and detects Doxygen)
#   --flat                      everything in one ALL_DOCS.md
#   --per-page                  one .md per page
#   --max-pages 200             crawl limit for big sites
#   --delay 0.2                 politeness delay (seconds) between fetches
#   --index-min 1500            "index page" threshold (see below)
#   --strip '^Footer text$'     extra per-line boilerplate regex (repeatable)
```

The tool prints a summary (`[mode] … N sections`, per-file writes,
totals). Markdown conversion details you can rely on:

- code blocks come out as ``` fences (html2text's `[code]` markers are
  rewritten to fences and the common indent is stripped)
- relative links and image URLs are rewritten to absolute URLs, so the
  .md files stay usable when read offline
- each page in a combined file is separated by `---` with a
  `> Source: <url>` provenance line

**Index-page expansion** (automatic): a fetched page whose extracted
text is shorter than `--index-min` (default 1500 chars) is treated as an
*index page* (e.g. Doxygen's "Functions" or "Data types" listings) and
its same-site `.html` children are pulled into the same section file.
This is what makes "full text of all its child pages" true for
group-style sections. Common Doxygen chrome pages (`files.html`,
`globals.html`, `annotated.html`, …) are excluded from expansion by
name. Sections that end up with zero pages (their pages were already
pulled into an earlier section) are skipped rather than written empty.

### 3. Verify the output (never skip)

Boilerplate leakage, unbalanced fences, and missing pages are the three
failure modes. Check:

```bash
# a) no leftover chrome lines in any output file (expect zero matches)
grep -ricE 'Loading|Searching|No Matches|Generated by [0-9]' <output_dir> | grep -v ':0'

# b) balanced code fences: the count per file must be EVEN
grep -c '^```' <output_dir>/*.md

# c) coverage: number of unique pages fetched vs. pages listed in the
#    site navtree / nav links (spot-check section and child page titles)
grep -c '^#' <output_dir>/*.md ; head -30 <output_dir>/*.md
```

If boilerplate lines remain, note the exact line, re-run with
`--strip '<regex>'`. (Version banners like `LibName v2.3.1` are
site-specific — add them with `--strip`.)

### 4. Report to the user

A short table: file name → sections/pages covered → size; plus total
size, page count, output format (md or txt), and the source URL. State
any pages that failed to fetch (reported on stderr as
`WARN: fetch failed …`). If the txt fallback fired (venv missing), say
so and mention that `bash scripts/ensure_venv.sh` enables Markdown.

## How it works (and why it is built this way)

- **Two conversion paths.** The Markdown path (default) extracts the
  main content container with beautifulsoup4 and converts it with
  html2text; the txt fallback path is the original stdlib-only extractor.
  Keeping the fallback means the tool never hard-fails on a machine
  without the venv — it still delivers readable plain text.
- **Content-container detection happens before conversion** — text is
  taken from `#doc-content`, `<main>`, `<article>`, or common
  content-class divs; if none exist, it falls back to `<body>` minus
  `nav/header/footer/aside/script/style`. Without this, every output
  file would start with menus and search boxes, and the Markdown
  converter would faithfully convert all that chrome into junk Markdown.
- **html2text is configured with `body_width = 0`** — no hard line
  wrapping. Hard wrapping would break long URLs in links and mangle
  table rows; zero-width keeps headings and links intact.
- **Doxygen navtree parsing** — Doxygen sites load navigation via
  `navtreedata.js`, so scraping HTML links misses the entire menu.
  Parsing `var NAVTREE` gives the exact section tree (note: cut the
  token stream at NAVTREE's closing `];` — the file also contains
  `NAVTREEINDEX` after it, which otherwise gets mis-parsed as sections).
  Child entries that are just anchors (`page.html#fragment`) are
  deliberately *skipped*: their text is already inside the parent page,
  and fetching them again would duplicate it.
- **Non-breaking spaces are normalized FIRST** (lesson learned the hard
  way): Doxygen emits `\xa0` inside banner lines like `coreMQTT v5.0.2`,
  which silently defeats exact-match boilerplate stripping.
- **Zero-width joiners** (`\u200c`, `\u200d`) are stripped — they are
  invisible but corrupt plain-text search and diffing.
- **Venv re-exec, guarded by `sys.prefix`** — venv interpreters are
  symlinks to the system python, so comparing *executable paths* would
  false-negative and skip the hop; comparing `sys.prefix` is the robust
  guard and cannot loop.

## Limitations / edge cases

- **Tables** become GitHub-style pipe tables in Markdown (cells joined
  with `|`); cells that themselves contain block markup (lists, nested
  tables) degrade to plain `cell | cell` lines — content is preserved,
  layout is not. Mention this to the user if the docs are table-heavy.
- JavaScript-rendered docs (React SPA with no static HTML, e.g. some
  GitBook sites) cannot be crawled — only server-rendered HTML works. If
  `crawl` finds <5 pages, suspect this and tell the user.
- SPAs that use hash routing (`docs.com/#/page`) are not supported by
  the crawler (it only follows real `.html` hrefs).
- Huge sites: raise `--max-pages`, but consider `--delay 1` to stay
  polite.
- Auth-protected docs are not supported (no cookie/session handling).
- Local directories: `file://` URLs work for Doxygen-mode (navtree) and
  direct page URLs; for crawl mode over a local tree, serve it first
  (`python3 -m http.server 8000 --directory <dir>`), because crawling
  needs to fetch the directory index.
