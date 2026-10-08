#!/usr/bin/env python3
"""
Builds index.html from ../README.md via the shared parser in ../tools/manifesto.py.

Re-run after any edit to README.md:

    python3 build.py

(or just run ../rebuild.sh, which rebuilds the site and the PDF together)
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "tools"))
import manifesto  # noqa: E402

TEMPLATE = ROOT / "template.html"
OUT = ROOT / "index.html"


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
    8: "murk",
}


def render_book(book, book_index):
    if book["kind"] == "book":
        roman = manifesto.book_roman(book, book_index)
        book_title = manifesto.book_name(book)
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
        roman = manifesto.book_roman(book, bi)
        name = manifesto.book_name(book)
        items.append(
            f'<a href="#book-{bi}" class="nav-dot" data-target="book-{bi}" title="{html.escape(name)}"><span>{roman}</span></a>'
        )
    items.append('<a href="#conclusion" class="nav-dot" data-target="conclusion" title="Заключение"><span>◆</span></a>')
    return "\n".join(items)


def main():
    doc = manifesto.load()

    preamble_html = "\n".join(f'<p class="reveal">{p}</p>' for p in doc["preamble"])

    books_html = []
    bi = 0
    for book in doc["books"]:
        if book["kind"] == "book":
            bi += 1
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
