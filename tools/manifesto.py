#!/usr/bin/env python3
"""
Shared parser for ../README.md — the one source of truth both the web page
(site/build.py) and the PDF (pdf/build.py) are generated from.

Pure standard library, no dependencies. The manifesto's markdown is
hand-authored in a very regular shape (see the docstring in parse() below),
so this reads it directly instead of pulling in a generic markdown engine —
that keeps both build scripts dependency-free and the parsing logic in one
place instead of duplicated between them.

If README.md's formatting ever changes shape (a new kind of block), this is
the only file that needs to learn about it — both build.py scripts consume
the same `parse()` output and stay untouched.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"

# Russian book headings spell the ordinal out ("Книга Девятая"), so they need
# a word -> roman numeral lookup. English/Thai headings embed the roman
# numeral directly ("Book IX." / "เล่ม IX.") and so need no lookup table —
# see BOOK_HEADING_RE below.
BOOK_NUM_WORDS = {
    "Первая": "I", "Вторая": "II", "Третья": "III", "Четвёртая": "IV",
    "Пятая": "V", "Шестая": "VI", "Седьмая": "VII", "Восьмая": "VIII",
    "Девятая": "IX", "Десятая": "X",
}

BOOK_HEADING_RE = {
    "ru": re.compile(r"Книга (\S+)\.\s*(.+)"),
    "en": re.compile(r"Book\s+([IVXLCDM]+)\.\s*(.+)"),
    "th": re.compile(r"เล่ม\s+([IVXLCDM]+)\.\s*(.+)"),
}

KIND_WORDS = {
    "ru": {"conclusion": "Заключение", "glossary": "Словарь", "axioms": "Аксиоматика", "practices": "Практики"},
    "en": {"conclusion": "Conclusion", "glossary": "Glossary", "axioms": "Axiomatics", "practices": "Practices"},
    "th": {"conclusion": "บทส่งท้าย", "glossary": "อภิธานศัพท์", "axioms": "สูตรสัจธรรม", "practices": "การฝึกฝน"},
}


def inline(text: str) -> str:
    """Convert the small inline markdown vocabulary used in the manifesto."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"§(\d+)", r'<span class="ref">§\1</span>', text)
    return text


def parse(md: str, lang: str = "ru") -> dict:
    """
    Parses the manifesto into:
      {"title": str, "preamble": [html, ...], "books": [book, ...]}

    Each book is:
      {"glyph": "🜁", "title": "Книга Первая. ...", "kind": "book"|"conclusion"|"glossary"|"axioms",
       "sections": [section, ...]}

    Each section is:
      {"num": "1"|None, "title": str|None,
       "blocks": [("p", html), ("ol", [html,...]), ("dt", (term_html, def_html)),
                  ("axiom", html), ("invocation", html), ...]}

    Recognised line shapes:
      # Title                      -> doc title
      ## 🜁 Книга X. Название       -> new book (glyph + rest)
      ### §N. Название              -> new section within the current book
      1. text                       -> numbered list item (accumulated into "ol")
      - **Term** — definition       -> glossary entry ("dt")
      △ text                        -> axiom line
      🜁 *text*                     -> closing invocation line (Заключение)
      --- / blank line              -> block separator
      anything else                 -> accumulated into a paragraph ("p")
    """
    kind_words = KIND_WORDS.get(lang, KIND_WORDS["ru"])
    lines = md.split("\n")
    doc = {"title": "", "preamble": [], "books": []}
    i = 0
    n = len(lines)

    while i < n and not lines[i].startswith("# "):
        i += 1
    doc["title"] = lines[i][2:].strip()
    i += 1

    buf = []
    while i < n and not lines[i].startswith("## "):
        line = lines[i]
        if line.strip() == "" or line.strip() == "---":
            if buf:
                doc["preamble"].append(inline(" ".join(buf)))
                buf = []
        else:
            buf.append(line.strip())
        i += 1
    if buf:
        doc["preamble"].append(inline(" ".join(buf)))

    current_book = None
    current_section = None
    para_buf = []
    list_buf = []

    def flush_para():
        nonlocal para_buf
        if para_buf and current_section is not None:
            current_section["blocks"].append(("p", inline(" ".join(para_buf))))
        para_buf = []

    def flush_list():
        nonlocal list_buf
        if list_buf and current_section is not None:
            current_section["blocks"].append(("ol", [inline(t) for t in list_buf]))
        list_buf = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("## "):
            flush_para()
            flush_list()
            title = stripped[3:].strip()
            glyph, _, rest = title.partition(" ")
            current_book = {"glyph": glyph, "title": rest, "sections": [], "kind": "book"}
            if rest.startswith(kind_words["conclusion"]):
                current_book["kind"] = "conclusion"
            elif rest.startswith(kind_words["glossary"]):
                current_book["kind"] = "glossary"
            elif rest.startswith(kind_words["practices"]):
                current_book["kind"] = "practices"
            elif kind_words["axioms"] in rest:
                current_book["kind"] = "axioms"
            doc["books"].append(current_book)
            current_section = {"num": None, "title": None, "blocks": []}
            current_book["sections"].append(current_section)
            i += 1
            continue

        if stripped.startswith("### "):
            flush_para()
            flush_list()
            heading = stripped[4:].strip()
            m = re.match(r"§(\d+)\.\s*(.+)", heading)
            current_section = {
                "num": m.group(1) if m else None,
                "title": m.group(2) if m else heading,
                "blocks": [],
            }
            current_book["sections"].append(current_section)
            i += 1
            continue

        if stripped == "":
            flush_para()
            flush_list()
            i += 1
            continue

        if stripped == "---":
            i += 1
            continue

        if re.match(r"^\d+\.\s", stripped):
            flush_para()
            item = re.sub(r"^\d+\.\s", "", stripped)
            list_buf.append(item)
            i += 1
            continue

        if stripped.startswith("- "):
            flush_para()
            flush_list()
            item = stripped[2:]
            m = re.match(r"\*\*(.+?)\*\*\s*-\s*(.+)", item)
            if m:
                current_section["blocks"].append(("dt", (inline(m.group(1)), inline(m.group(2)))))
            else:
                current_section["blocks"].append(("dt", (inline(item), "")))
            i += 1
            continue

        if stripped.startswith("△"):
            flush_para()
            flush_list()
            current_section["blocks"].append(("axiom", inline(stripped[1:].strip())))
            i += 1
            continue

        if stripped.startswith("🜁 *"):
            flush_para()
            flush_list()
            txt = stripped[2:].strip()
            txt = txt.strip("*")
            current_section["blocks"].append(("invocation", inline(txt)))
            i += 1
            continue

        para_buf.append(stripped)
        i += 1

    flush_para()
    flush_list()
    return doc


def load(path: Path = README, lang: str = "ru") -> dict:
    """Convenience: parse a manifesto source file directly."""
    return parse(path.read_text(encoding="utf-8"), lang=lang)


def book_roman(book: dict, fallback: int, lang: str = "ru") -> str:
    """'Книга Первая. ...' -> 'I' / 'Book IX. ...' -> 'IX' (falls back to the
    1-based book index if the heading doesn't match the expected shape)."""
    heading_re = BOOK_HEADING_RE.get(lang, BOOK_HEADING_RE["ru"])
    m = heading_re.match(book["title"])
    if not m:
        return str(fallback)
    token = m.group(1)
    if lang == "ru":
        return BOOK_NUM_WORDS.get(token, str(fallback))
    return token  # en/th headings already spell the roman numeral out


def book_name(book: dict, lang: str = "ru") -> str:
    """'Книга Первая. Исток и Русло' -> 'Исток и Русло'."""
    heading_re = BOOK_HEADING_RE.get(lang, BOOK_HEADING_RE["ru"])
    m = heading_re.match(book["title"])
    return m.group(2) if m else book["title"]
