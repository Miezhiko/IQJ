#!/usr/bin/env python3
"""
Builds IQJ-manifest.pdf from ../README.md via the shared parser in
../tools/manifesto.py — no pip packages, no venv: stdlib + a system
google-chrome-stable/chromium doing the HTML -> PDF conversion headless.

    python3 build.py

(or just run ../rebuild.sh, which rebuilds the site and the PDF together)
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "tools"))
import manifesto  # noqa: E402

TEMPLATE = ROOT / "template.html"
OUT_PDF = ROOT.parent / "IQJ-manifest.pdf"

CHROME_CANDIDATES = [
    "google-chrome-stable",
    "google-chrome",
    "chromium-browser",
    "chromium",
]


def find_chrome() -> str:
    for name in CHROME_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    sys.exit(
        "No headless-capable Chrome/Chromium found on PATH "
        f"(tried: {', '.join(CHROME_CANDIDATES)}). Install one, or edit "
        "CHROME_CANDIDATES in pdf/build.py to point at yours."
    )


def render_blocks(blocks) -> list[str]:
    """Flat HTML for one section's blocks — <p>/<ol> only; axioms and the
    closing invocation lines are collected separately by the caller so they
    can be joined into the single <p> the print CSS keys off of."""
    out = []
    for kind, payload in blocks:
        if kind == "p":
            out.append(f"<p>{payload}</p>")
        elif kind == "ol":
            items = "".join(f"<li>{it}</li>" for it in payload)
            out.append(f"<ol>{items}</ol>")
        elif kind == "dt":
            term, definition = payload
            out.append(f"<li><strong>{term}</strong> — {definition}</li>")
        # "axiom" / "invocation" handled by render_book() directly.
    return out


def book_heading(book) -> str:
    """Reassemble the original '## <glyph> <title>' heading line, e.g.
    '🜁 Книга Первая. Исток и Русло' or '🜁 Словарь терминов'."""
    return f"{book['glyph']} {book['title']}"


def render_book(book, book_index) -> str:
    parts = []
    if book["kind"] == "book":
        parts.append(f"<h2>{book_heading(book)}</h2>")
        for sec in book["sections"]:
            if sec["num"] is None and not sec["blocks"]:
                continue
            if sec["num"]:
                parts.append(f"<h3>§{sec['num']}. {sec['title']}</h3>")
            parts.extend(render_blocks(sec["blocks"]))

    elif book["kind"] == "axioms":
        parts.append(f"<h2>{book_heading(book)}</h2>")
        lines = []
        for sec in book["sections"]:
            for kind, payload in sec["blocks"]:
                if kind == "axiom":
                    lines.append(f"△ {payload}")
        parts.append("<p>" + "<br />\n".join(lines) + "</p>")

    elif book["kind"] == "conclusion":
        parts.append(f"<h2>{book_heading(book)}</h2>")
        invocation_lines = []
        for sec in book["sections"]:
            for kind, payload in sec["blocks"]:
                if kind == "p":
                    parts.append(f"<p>{payload}</p>")
                elif kind == "invocation":
                    invocation_lines.append(f"△ <em>{payload}</em>")
        if invocation_lines:
            parts.append("<p>" + "<br />\n".join(invocation_lines) + "</p>")

    elif book["kind"] == "glossary":
        parts.append(f"<h2>{book_heading(book)}</h2>")
        items = []
        for sec in book["sections"]:
            items.extend(render_blocks(sec["blocks"]))
        parts.append("<ul>" + "".join(items) + "</ul>")

    return "\n".join(parts)


def build_html(doc) -> str:
    parts = [f"<h1>{doc['title']}</h1>"]
    for p in doc["preamble"]:
        parts.append(f"<p>{p}</p>")

    bi = 0
    for book in doc["books"]:
        if book["kind"] == "book":
            bi += 1
        parts.append(render_book(book, bi))
        parts.append("<hr />")
    if parts and parts[-1] == "<hr />":
        parts.pop()

    body = "\n".join(parts)
    tpl = TEMPLATE.read_text(encoding="utf-8")
    out = tpl.replace("<!--TITLE-->", doc["title"])
    out = out.replace("<!--BODY-->", body)
    # The alchemical-air glyph (🜁) isn't covered by the serif fonts print
    # uses and falls back to an ugly glyph in most PDF viewers; the plain
    # triangle renders correctly everywhere and reads the same.
    out = out.replace("🜁", "△")
    return out


def main():
    chrome = find_chrome()
    doc = manifesto.load()
    html_out = build_html(doc)

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "manifesto.html"
        html_path.write_text(html_out, encoding="utf-8")

        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                f"--print-to-pdf={OUT_PDF}",
                "--print-to-pdf-no-header",
                f"file://{html_path}",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    size_kb = OUT_PDF.stat().st_size // 1024
    print(f"wrote {OUT_PDF} ({size_kb} KB)")


if __name__ == "__main__":
    main()
