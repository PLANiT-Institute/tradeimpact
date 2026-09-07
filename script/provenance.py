"""Check that a quoted sentence is really in the page or document it is cited from.

A register row that carries a source link and a quote is only as good as the quote: a paraphrase
reads like evidence and is not. These helpers read the saved file's own text and confirm every
substantial fragment of the quote appears in it, so a sentence cannot be reworded into a register
or invented outright. The check is used by the power role register
(``script/power/roles/extract_company_ir_roles.py``) and by the national emission-factor register
(``script/power/emission_factors/extract_emission_factors.py``).

A quote may elide the middle of a long sentence with ``...`` or ``…``; each remaining fragment is
checked separately. Fragments shorter than ``MIN_FRAGMENT`` characters are too weak to prove
anything and are only checked when the whole quote is short.
"""

from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

#: Elision markers a hand-written quote may use.
ELLIPSIS = re.compile(r"\.\.\.|…")
#: Below this many characters a fragment is not evidence on its own.
MIN_FRAGMENT = 24


def normalise(text: str) -> str:
    """Text with compatibility forms, curly quotes and runs of whitespace flattened."""
    text = unicodedata.normalize("NFKC", text)
    for curly, straight in (("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(curly, straight)
    return re.sub(r"\s+", " ", text).strip()


def page_text(path: Path) -> str:
    """The readable text of a saved page or document: tags and scripts out, whitespace collapsed."""
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        text = " ".join((page.extract_text() or "") for page in PdfReader(path).pages)
    else:
        raw = path.read_text(errors="replace")
        raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
        text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return normalise(text)


def quote_is_on_the_page(quote: str, text: str) -> bool:
    """Whether every substantial fragment of the quote appears in the document's own text."""
    fragments = [f.strip() for f in ELLIPSIS.split(normalise(quote))]
    substantial = [f for f in fragments if len(f) >= MIN_FRAGMENT]
    return all(f in text for f in substantial or fragments)
