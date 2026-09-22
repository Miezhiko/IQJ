#!/usr/bin/env python3
"""
Builds index.html from ../README.md.

The manifesto's markdown is hand-authored in a very regular shape, so this
parses it directly (no generic markdown engine) to get full control over the
HTML structure the scroll animations hook into. Re-run after any edit to
README.md:

    python3 build.py
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT.parent / "README.md"
TEMPLATE = ROOT / "template.html"
OUT = ROOT / "index.html"


def inline(text: str) -> str:
    """Convert the small inline markdown vocabulary used in the manifesto."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"§(\d+)", r'<span class="ref">§\1</span>', text)
    return text


def parse(md: str):
    lines = md.split("\n")
    doc = {"title": "", "preamble": [], "books": []}
    i = 0
    n = len(lines)

    # Title
    while i < n and not lines[i].startswith("# "):
        i += 1
    doc["title"] = lines[i][2:].strip()
    i += 1

    # Preamble paragraphs until first "## "
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

    # Books / Заключение / Словарь
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
            # title looks like "🜁 Книга Первая. Исток и Русло" or "🜁 Заключение"
            glyph, _, rest = title.partition(" ")
            current_book = {"glyph": glyph, "title": rest, "sections": [], "kind": "book"}
            if rest.startswith("Заключение"):
                current_book["kind"] = "conclusion"
            elif rest.startswith("Словарь"):
                current_book["kind"] = "glossary"
            elif "Аксиоматика" in rest:
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

        if stripped == "" :
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
            # glossary bullet: "- **Term** — definition"
            flush_para()
            flush_list()
            item = stripped[2:]
            m = re.match(r"\*\*(.+?)\*\*\s*—\s*(.+)", item)
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

        if stripped.startswith("🜁 *") :
            # closing invocation line in conclusion
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


BOOK_NUM_WORDS = {
    "Первая": "I", "Вторая": "II", "Третья": "III", "Четвёртая": "IV",
    "Пятая": "V", "Шестая": "VI", "Седьмая": "VII", "Восьмая": "VIII",
}


def render_blocks(blocks):
    out = []
    for kind, payload in blocks:
        if kind == "p":
            out.append(f'<p class="reveal">{payload}</p>')
        elif kind == "ol":
            items = "".join(f'<li class="reveal">{it}</li>' for it in payload)
            out.append(f'<ol class="passage-list">{items}</ol>')
        elif kind == "dt":
            term, definition = payload
            out.append(
                f'<div class="gloss-entry reveal"><dt>{term}</dt><dd>{definition}</dd></div>'
            )
        elif kind == "axiom":
            out.append(f'<li class="axiom reveal"><span class="axiom-glyph">△</span>{payload}</li>')
        elif kind == "invocation":
            out.append(f'<p class="invocation reveal">{payload}</p>')
    return "\n".join(out)


BOOK_MOODS = {
    1: "source",
    2: "flow",
    3: "flow",
    4: "murk",
    5: "flow",
    6: "network",
    7: "flow",
}


def render_book(book, book_index):
    if book["kind"] == "book":
        m = re.match(r"Книга (\S+)\.\s*(.+)", book["title"])
        roman = BOOK_NUM_WORDS.get(m.group(1), str(book_index))
        book_title = m.group(2)
        mood = BOOK_MOODS.get(book_index, "flow")
        sections_html = []
        for sec in book["sections"]:
            if sec["num"] is None and not sec["blocks"]:
                continue
            header = (
                f'<h3 class="reveal"><span class="sec-num">§{sec["num"]}</span> {sec["title"]}</h3>'
                if sec["num"]
                else ""
            )
            sections_html.append(
                f'<article class="passage" id="p{sec["num"] or ""}">{header}{render_blocks(sec["blocks"])}</article>'
            )
        return f"""
<section class="book" id="book-{book_index}" data-book="{book_index}" data-mood="{mood}">
  <div class="book-divider">
    <span class="book-roman">{roman}</span>
    <h2 class="book-title reveal-title">{book_title}</h2>
    <span class="glyph-line" aria-hidden="true">△</span>
  </div>
  <div class="book-body">
    {''.join(sections_html)}
  </div>
</section>
"""
    elif book["kind"] == "axioms":
        axioms = []
        for sec in book["sections"]:
            for kind, payload in sec["blocks"]:
                if kind == "axiom":
                    axioms.append(payload)
        items = "".join(
            f'<li class="axiom reveal"><span class="axiom-glyph">△</span>{a}</li>' for a in axioms
        )
        return f"""
<section class="book axioms-book" id="axioms" data-book="{book_index}" data-mood="crystal">
  <div class="book-divider">
    <span class="book-roman">VIII</span>
    <h2 class="book-title reveal-title">Аксиоматика</h2>
    <span class="glyph-line" aria-hidden="true">△</span>
  </div>
  <ul class="axioms-list">{items}</ul>
</section>
"""
    elif book["kind"] == "conclusion":
        blocks = []
        for sec in book["sections"]:
            blocks.append(render_blocks(sec["blocks"]))
        return f"""
<section class="conclusion" id="conclusion" data-mood="calm">
  <div class="book-divider">
    <span class="glyph-line" aria-hidden="true">△</span>
    <h2 class="book-title reveal-title">Заключение</h2>
  </div>
  <div class="book-body">{''.join(blocks)}</div>
</section>
"""
    elif book["kind"] == "glossary":
        blocks = []
        for sec in book["sections"]:
            blocks.append(render_blocks(sec["blocks"]))
        return f"""
<section class="glossary" id="glossary" data-mood="still">
  <div class="book-divider">
    <span class="glyph-line" aria-hidden="true">△</span>
    <h2 class="book-title reveal-title">Словарь терминов</h2>
  </div>
  <dl class="gloss-grid">{''.join(blocks)}</dl>
</section>
"""
    return ""


def render_nav(doc):
    items = []
    bi = 0
    for book in doc["books"]:
        if book["kind"] != "book":
            continue
        bi += 1
        m = re.match(r"Книга (\S+)\.\s*(.+)", book["title"])
        roman = BOOK_NUM_WORDS.get(m.group(1), str(bi))
        items.append(
            f'<a href="#book-{bi}" class="nav-dot" data-target="book-{bi}" title="{html.escape(m.group(2))}"><span>{roman}</span></a>'
        )
    items.append('<a href="#conclusion" class="nav-dot" data-target="conclusion" title="Заключение"><span>◆</span></a>')
    return "\n".join(items)


def main():
    md = SRC.read_text(encoding="utf-8")
    doc = parse(md)

    preamble_html = "\n".join(f'<p class="reveal">{p}</p>' for p in doc["preamble"])

    books_html = []
    bi = 0
    for book in doc["books"]:
        if book["kind"] == "book":
            bi += 1
            books_html.append(render_book(book, bi))
        else:
            books_html.append(render_book(book, bi))

    nav_html = render_nav(doc)

    tpl = TEMPLATE.read_text(encoding="utf-8")
    out = tpl.replace("<!--TITLE-->", html.escape(doc["title"]))
    out = out.replace("<!--PREAMBLE-->", preamble_html)
    out = out.replace("<!--BOOKS-->", "\n".join(books_html))
    out = out.replace("<!--NAV-->", nav_html)

    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT} ({len(out)} bytes), {bi} books")


if __name__ == "__main__":
    main()
