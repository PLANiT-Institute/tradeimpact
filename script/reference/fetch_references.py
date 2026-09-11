"""Download every reference that can be downloaded, so the library is on disk and openable.

Input   reference/references.csv        the register; each row's ``file_url`` is what to fetch
Output  reference/raw/<key>.<ext>       the document as served
        reference/raw/index.csv         per file: source URL, content type, bytes, SHA-256,
                                        fetch date, transport, and the licence recorded for it

A bibliography of links rots. This keeps the documents themselves beside the register, hashed,
so a reader can open what a claim rests on and check that it is the edition that was read.

What it refuses to save. A publisher that answers a robot with a bot-challenge stub or a paywall
shell returns HTTP 200 and a few kilobytes of HTML; saved blindly, that becomes a file that looks
like a reference and is not. A response is only written when it is a PDF, or HTML substantial
enough to be a real page and free of the usual challenge markers. Everything else is recorded in
``index.csv`` as ``not_saved`` with the reason, so the gap is visible rather than silent.

Licences differ per document and are carried per row from the register's ``access`` column plus
the per-file ``licence`` note: several of these are free to read and not free to redistribute.
The copies here are the working library for this research, not a republication.

Documents behind a bot wall. Several publishers refuse any automated request, and two of them
answer with a captcha, which is not something to work around. Those are fetched by hand: open
the URL in a browser, save the file into ``reference/raw/`` as ``<key>.pdf``, and run this again
- a file already sitting under a reference's key is adopted, hashed and indexed like any other.

Run from the repository root:
    .venv/bin/python script/reference/fetch_references.py [--refresh] [--key KEY ...]
"""

from __future__ import annotations

import csv
import hashlib
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import certifi

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "reference" / "references.csv"
RAW = REPO / "reference" / "raw"
INDEX = RAW / "index.csv"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 tradeimpact/1.0 (research; sanghyun@planit.institute)"
)
CURL = "/usr/bin/curl"
PAUSE_SECONDS = 1.0
#: Smaller than this, an HTML response is a redirect shell or a challenge page, not a document.
MIN_HTML_BYTES = 20_000
#: Why a reference has no file, in the words a reader needs rather than a stack trace.
GAP_REASONS = {
    "no_copy": "no open copy is published; the row carries the DOI and the publisher's terms",
    "blocked": "the publisher refuses automated requests; open it in a browser from the URL",
    "gated": "behind a registration or login gate; free to read, but the file is not served",
    "site": "a live database or search application rather than a document",
    "shell": "the URL served a redirect shell rather than the document",
}
#: Hosts whose refusal is a login or registration gate rather than a bot rule.
GATED_HOSTS = ("wbcsd.org", "ifrs.org", "ssrn.com")
#: Hosts that are an application, not a document.
SITE_HOSTS = ("unfccc.int/NDCREG", "energyfinance.org", "projectframe.how")
#: Markers of a bot challenge or a paywall gate rather than the document itself.
REFUSED = re.compile(
    rb"Incapsula|_Incapsula_Resource|Radware|captcha|Cloudflare Ray ID|"
    rb"Just a moment\.\.\.|Please enable (?:JS|JavaScript)|Access Denied",
    re.IGNORECASE,
)
INDEX_FIELDS = [
    "key",
    "file",
    "source_url",
    "content_type",
    "bytes",
    "sha256",
    "access",
    "fetched",
    "fetched_with",
    "note",
]


def register() -> list[dict[str, str]]:
    """The register rows, in file order."""
    with REGISTER.open(newline="") as f:
        return list(csv.DictReader(f))


def get(url: str, context: ssl.SSLContext) -> tuple[bytes, str, str]:
    """(body, content type, transport) for a URL, falling back to the system curl."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, context=context, timeout=180) as response:
            return response.read(), response.headers.get("Content-Type", ""), "urllib"
    except Exception:  # noqa: BLE001 - curl reaches hosts python's TLS and urllib cannot
        out = RAW / ".download"
        proc = subprocess.run(
            [
                CURL, "--silent", "--show-error", "--fail", "--location", "--max-time", "180",
                "--user-agent", USER_AGENT, "--write-out", "%{content_type}",
                "--output", str(out), url,
            ],
            capture_output=True,
            check=True,
            text=True,
        )  # fmt: skip
        body = out.read_bytes()
        out.unlink(missing_ok=True)
        return body, proc.stdout.strip(), "curl_system_trust"


def is_a_document(body: bytes, content_type: str) -> tuple[bool, str]:
    """Whether the response is the document, and which gap reason applies when it is not."""
    if body[:5] == b"%PDF-" or "pdf" in content_type.lower():
        return True, ""
    if REFUSED.search(body[:200_000]):
        return False, "blocked"
    if len(body) < MIN_HTML_BYTES:
        return False, "shell"
    return True, ""


def reason_for(url: str, kind: str) -> str:
    """The gap reason for a URL, refined by what the host is."""
    if any(h in url for h in GATED_HOSTS):
        kind = "gated"
    elif any(h in url for h in SITE_HOSTS):
        kind = "site"
    return GAP_REASONS.get(kind, GAP_REASONS["blocked"])


def extension(body: bytes, content_type: str) -> str:
    """The suffix the saved file should carry."""
    if body[:5] == b"%PDF-" or "pdf" in content_type.lower():
        return ".pdf"
    if "xlsx" in content_type or "spreadsheet" in content_type:
        return ".xlsx"
    return ".html"


def main() -> None:
    """Fetch every reference with a file URL; write the index; report what could not be saved."""
    RAW.mkdir(parents=True, exist_ok=True)
    argv = sys.argv[1:]
    refresh = "--refresh" in argv
    wanted = {argv[i + 1] for i, a in enumerate(argv) if a == "--key" and i + 1 < len(argv)}
    known = {r["key"]: r for r in csv.DictReader(INDEX.open(newline=""))} if INDEX.exists() else {}
    context = ssl.create_default_context(cafile=certifi.where())
    index: list[dict[str, object]] = []
    saved = failed = skipped = 0
    for row in register():
        key = row["key"]
        if wanted and key not in wanted:
            if key in known:
                index.append(known[key])
            continue
        previous = known.get(key)
        if previous and previous.get("file") and (RAW / previous["file"]).exists() and not refresh:
            index.append(previous)
            continue
        # A file already sitting here under the reference's key is adopted and hashed. That is
        # how a document behind a bot wall gets into the library: open it in a browser, save it
        # as <key>.pdf, run this again.
        by_hand = next((f for f in sorted(RAW.glob(f"{key}.*")) if f.name != "index.csv"), None)
        if by_hand and not refresh:
            body = by_hand.read_bytes()
            index.append(
                {
                    "key": key,
                    "file": by_hand.name,
                    "source_url": row.get("file_url", "") or row["url"],
                    "content_type": "application/pdf" if body[:5] == b"%PDF-" else "text/html",
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "access": row["access"],
                    "fetched": date.today().isoformat(),
                    "fetched_with": "by_hand",
                    "note": "saved from a browser: the publisher refuses automated requests",
                }
            )
            saved += 1
            continue
        url = row.get("file_url", "").strip()
        record: dict[str, object] = {
            "key": key,
            "file": "",
            "source_url": url,
            "content_type": "",
            "bytes": "",
            "sha256": "",
            "access": row["access"],
            "fetched": date.today().isoformat(),
            "fetched_with": "",
            "note": "",
        }
        if not url:
            record["note"] = f"not_saved: {GAP_REASONS['no_copy']}"
            index.append(record)
            skipped += 1
            continue
        try:
            body, content_type, transport = get(url, context)
        except Exception:  # noqa: BLE001 - one refusal must not stop the library
            record["note"] = f"not_saved: {reason_for(url, 'blocked')}"
            index.append(record)
            failed += 1
            continue
        ok, why = is_a_document(body, content_type)
        record.update({"content_type": content_type, "bytes": len(body), "fetched_with": transport})
        if not ok:
            record["note"] = f"not_saved: {reason_for(url, why)}"
            index.append(record)
            failed += 1
            continue
        name = key + extension(body, content_type)
        (RAW / name).write_bytes(body)
        record.update({"file": name, "sha256": hashlib.sha256(body).hexdigest()})
        index.append(record)
        saved += 1
        time.sleep(PAUSE_SECONDS)
    with INDEX.open("w", newline="") as f:
        writer = csv.DictWriter(f, INDEX_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(index, key=lambda r: str(r["key"])))
    on_disk = sum(1 for r in index if r["file"])
    total = sum(int(r["bytes"] or 0) for r in index if r["file"])
    print(
        f"{RAW.relative_to(REPO)}: {on_disk} documents on disk ({total / 1e6:.0f} MB); "
        f"{saved} fetched now, {failed} refused or unusable, {skipped} with no published copy"
    )
    for r in index:
        if not r["file"]:
            print(f"  {r['key']}: {r['note']}")


if __name__ == "__main__":
    main()
