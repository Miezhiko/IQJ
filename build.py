#!/usr/bin/env python3
"""
Builds index.html / index.en.html / index.th.html from README.md /
README.en.md / README.th.md via the shared parser in tools/manifesto.py.

Re-run after any edit to any of the three source files:

    python3 build.py

(or just run ./rebuild.sh, which rebuilds the site and the PDF together)
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "tools"))
import manifesto  # noqa: E402

TEMPLATE = ROOT / "template.html"

# Everything that differs between languages lives here: the source file,
# the output file, and every bit of UI copy that template.html doesn't get
# from parsing the manifesto itself (meta description, button labels, the
# hero banner, the footer line...).
LANGS = {
    "ru": {
        "readme": ROOT / "README.md",
        "out": ROOT / "index.html",
        "lang_attr": "ru",
        "desc": "Имперский Квадроберский Джайнизм — трактат о Свабхаве, Хридае и Пути Служения.",
        "hero_title": "Имперский<br>Квадроберский<br>Джайнизм",
        "hero_subtitle": "Трактат о Свабхаве, Хридае и Пути Служения",
        "scroll_cue": "прокрутите, чтобы войти в русло",
        "footer": "Имперский Квадроберский Джайнизм",
        "nav_aria": "Книги трактата",
        "sound_aria": "Переключить фоновый звук", "sound_title": "Звук",
        "tts_aria": "Слушать трактат вслух", "tts_title": "Слушать",
        "tts_voice_aria": "Выбрать голос чтеца", "tts_voice_title": "Голос",
        "pdf_aria": "Скачать PDF", "pdf_title": "Скачать PDF",
        "dec_aria": "Уменьшить размер текста", "dec_title": "Меньше текста",
        "inc_aria": "Увеличить размер текста", "inc_title": "Больше текста",
        "font_links": "",
    },
    "en": {
        "readme": ROOT / "README.en.md",
        "out": ROOT / "index.en.html",
        "lang_attr": "en",
        "desc": "Imperial Quadrobic Jainism — a treatise on Svabhava, Hridaya, and the Path of Service.",
        "hero_title": "Imperial<br>Quadrobic<br>Jainism",
        "hero_subtitle": "A treatise on Svabhava, Hridaya, and the Path of Service",
        "scroll_cue": "scroll to enter the riverbed",
        "footer": "Imperial Quadrobic Jainism",
        "nav_aria": "Books of the treatise",
        "sound_aria": "Toggle ambient sound", "sound_title": "Sound",
        "tts_aria": "Listen to the treatise", "tts_title": "Listen",
        "tts_voice_aria": "Choose reader voice", "tts_voice_title": "Voice",
        "pdf_aria": "Download PDF", "pdf_title": "Download PDF",
        "dec_aria": "Decrease text size", "dec_title": "Smaller text",
        "inc_aria": "Increase text size", "inc_title": "Larger text",
        "font_links": "",
    },
    "th": {
        "readme": ROOT / "README.th.md",
        "out": ROOT / "index.th.html",
        "lang_attr": "th",
        "desc": "ไจนนิยมสี่เท้าแห่งจักรวรรดิ — คัมภีร์ว่าด้วยสวภาวะ หฤทัย และวิถีแห่งการรับใช้",
        "hero_title": "ไจนนิยม<br>สี่เท้า<br>แห่งจักรวรรดิ",
        "hero_subtitle": "คัมภีร์ว่าด้วยสวภาวะ หฤทัย และวิถีแห่งการรับใช้",
        "scroll_cue": "เลื่อนลงเพื่อเข้าสู่สายน้ำ",
        "footer": "ไจนนิยมสี่เท้าแห่งจักรวรรดิ",
        "nav_aria": "บรรดาเล่มของคัมภีร์",
        "sound_aria": "เปิด/ปิดเสียงพื้นหลัง", "sound_title": "เสียง",
        "tts_aria": "ฟังคัมภีร์", "tts_title": "ฟัง",
        "tts_voice_aria": "เลือกเสียงผู้อ่าน", "tts_voice_title": "เสียง",
        "pdf_aria": "ดาวน์โหลด PDF", "pdf_title": "ดาวน์โหลด PDF",
        "dec_aria": "ลดขนาดตัวอักษร", "dec_title": "ตัวอักษรเล็กลง",
        "inc_aria": "เพิ่มขนาดตัวอักษร", "inc_title": "ตัวอักษรใหญ่ขึ้น",
        "font_links": (
            '\n<link href="https://fonts.googleapis.com/css2?'
            'family=Noto+Serif+Thai:ital,wght@0,400;0,500;0,600;0,700;1,500'
            '&display=swap" rel="stylesheet">'
        ),
    },
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
    6: "murk",
    7: "network",
    8: "flow",
    9: "murk",
}


def render_sections(sections):
    """Shared by "book" and "practices": a list of .passage articles, each
    with an optional heading (numbered "§N. Title" or, for a titled-but-
    unnumbered subsection, just "Title") and its blocks."""
    sections_html = []
    for sec in sections:
        if sec["num"] is None and sec["title"] is None and not sec["blocks"]:
            continue
        if sec["num"]:
            header = f'<h3 class="reveal"><span class="sec-num">§{sec["num"]}</span> {sec["title"]}</h3>'
        elif sec["title"]:
            header = f'<h3 class="reveal">{sec["title"]}</h3>'
        else:
            header = ""
        id_attr = f' id="p{sec["num"]}"' if sec["num"] else ""
        sections_html.append(
            f'<article class="passage"{id_attr}>{header}{render_blocks(sec["blocks"])}</article>'
        )
    return "".join(sections_html)


def render_book(book, book_index, lang):
    if book["kind"] == "book":
        roman = manifesto.book_roman(book, book_index, lang)
        book_title = manifesto.book_name(book, lang)
        mood = BOOK_MOODS.get(book_index, "flow")
        return f"""
<section class="book" id="book-{book_index}" data-book="{book_index}" data-mood="{mood}">
  <div class="book-divider">
    <span class="book-roman">{roman}</span>
    <h2 class="book-title reveal-title">{book_title}</h2>
    <span class="glyph-line" aria-hidden="true">△</span>
  </div>
  <div class="book-body">
    {render_sections(book["sections"])}
  </div>
</section>
"""
    elif book["kind"] == "practices":
        book_title = manifesto.book_name(book, lang)
        return f"""
<section class="book practices-book" id="practices" data-mood="still">
  <div class="book-divider">
    <span class="glyph-line" aria-hidden="true">△</span>
    <h2 class="book-title reveal-title">{book_title}</h2>
  </div>
  <div class="book-body">
    {render_sections(book["sections"])}
  </div>
</section>
"""
    elif book["kind"] == "axioms":
        # Not a numbered "Книга" (it's a crystallization of the preceding
        # books, not a narrated one) - no roman-numeral badge, same as
        # conclusion/glossary/practices.
        book_title = manifesto.book_name(book, lang)
        axioms = []
        for sec in book["sections"]:
            for kind, payload in sec["blocks"]:
                if kind == "axiom":
                    axioms.append(payload)
        items = "".join(
            f'<li class="axiom reveal"><span class="axiom-glyph">△</span>{a}</li>' for a in axioms
        )
        return f"""
<section class="book axioms-book" id="axioms" data-mood="crystal">
  <div class="book-divider">
    <span class="glyph-line" aria-hidden="true">△</span>
    <h2 class="book-title reveal-title">{book_title}</h2>
  </div>
  <ul class="axioms-list">{items}</ul>
</section>
"""
    elif book["kind"] == "conclusion":
        book_title = manifesto.book_name(book, lang)
        blocks = []
        for sec in book["sections"]:
            blocks.append(render_blocks(sec["blocks"]))
        return f"""
<section class="conclusion" id="conclusion" data-mood="calm">
  <div class="book-divider">
    <span class="glyph-line" aria-hidden="true">△</span>
    <h2 class="book-title reveal-title">{book_title}</h2>
  </div>
  <div class="book-body">{''.join(blocks)}</div>
</section>
"""
    elif book["kind"] == "glossary":
        book_title = manifesto.book_name(book, lang)
        blocks = []
        for sec in book["sections"]:
            blocks.append(render_blocks(sec["blocks"]))
        return f"""
<section class="glossary" id="glossary" data-mood="still">
  <div class="book-divider">
    <span class="glyph-line" aria-hidden="true">△</span>
    <h2 class="book-title reveal-title">{book_title}</h2>
  </div>
  <dl class="gloss-grid">{''.join(blocks)}</dl>
</section>
"""
    return ""


#  kind         id            glyph  (conclusion/practices/glossary aren't
#                                      numbered "books", so each gets a
#                                      fixed glyph instead of a roman numeral)
TRAILING_NAV = {
    "conclusion": ("conclusion", "◆"),
    "practices": ("practices", "✦"),
    "glossary": ("glossary", "§"),
}


def render_nav(doc, lang):
    items = []
    bi = 0
    trailing = {}
    for book in doc["books"]:
        if book["kind"] in TRAILING_NAV:
            trailing[book["kind"]] = manifesto.book_name(book, lang)
            continue
        if book["kind"] != "book":
            continue
        bi += 1
        roman = manifesto.book_roman(book, bi, lang)
        name = manifesto.book_name(book, lang)
        items.append(
            f'<a href="#book-{bi}" class="nav-dot" data-target="book-{bi}" title="{html.escape(name)}"><span>{roman}</span></a>'
        )
    for kind, (target, glyph) in TRAILING_NAV.items():
        title = trailing.get(kind, target)
        items.append(
            f'<a href="#{target}" class="nav-dot" data-target="{target}" title="{html.escape(title)}"><span>{glyph}</span></a>'
        )
    return "\n".join(items)


def build(lang: str, tpl: str):
    meta = LANGS[lang]
    doc = manifesto.load(meta["readme"], lang=lang)

    preamble_html = "\n".join(f'<p class="reveal">{p}</p>' for p in doc["preamble"])

    books_html = []
    bi = 0
    for book in doc["books"]:
        if book["kind"] == "book":
            bi += 1
        books_html.append(render_book(book, bi, lang))

    nav_html = render_nav(doc, lang)

    out = tpl.replace("<!--TITLE-->", html.escape(doc["title"]))
    out = out.replace("<!--PREAMBLE-->", preamble_html)
    out = out.replace("<!--BOOKS-->", "\n".join(books_html))
    out = out.replace("<!--NAV-->", nav_html)
    out = out.replace("<!--LANG_ATTR-->", meta["lang_attr"])
    out = out.replace("<!--DESC-->", html.escape(meta["desc"]))
    out = out.replace("<!--HERO_TITLE-->", meta["hero_title"])
    out = out.replace("<!--HERO_SUBTITLE-->", html.escape(meta["hero_subtitle"]))
    out = out.replace("<!--SCROLL_CUE-->", html.escape(meta["scroll_cue"]))
    out = out.replace("<!--FOOTER-->", html.escape(meta["footer"]))
    out = out.replace("<!--NAV_ARIA-->", html.escape(meta["nav_aria"]))
    out = out.replace("<!--SOUND_ARIA-->", html.escape(meta["sound_aria"]))
    out = out.replace("<!--SOUND_TITLE-->", html.escape(meta["sound_title"]))
    out = out.replace("<!--TTS_ARIA-->", html.escape(meta["tts_aria"]))
    out = out.replace("<!--TTS_TITLE-->", html.escape(meta["tts_title"]))
    out = out.replace("<!--TTS_VOICE_ARIA-->", html.escape(meta["tts_voice_aria"]))
    out = out.replace("<!--TTS_VOICE_TITLE-->", html.escape(meta["tts_voice_title"]))
    out = out.replace("<!--PDF_ARIA-->", html.escape(meta["pdf_aria"]))
    out = out.replace("<!--PDF_TITLE-->", html.escape(meta["pdf_title"]))
    out = out.replace("<!--DEC_ARIA-->", html.escape(meta["dec_aria"]))
    out = out.replace("<!--DEC_TITLE-->", html.escape(meta["dec_title"]))
    out = out.replace("<!--INC_ARIA-->", html.escape(meta["inc_aria"]))
    out = out.replace("<!--INC_TITLE-->", html.escape(meta["inc_title"]))
    out = out.replace("<!--FONT_LINKS-->", meta["font_links"])

    meta["out"].write_text(out, encoding="utf-8")
    print(f"wrote {meta['out']} ({len(out)} bytes), {bi} books")


def main():
    tpl = TEMPLATE.read_text(encoding="utf-8")
    for lang in LANGS:
        build(lang, tpl)


if __name__ == "__main__":
    main()
