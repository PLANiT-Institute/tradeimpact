"""Check that every reference in the register still resolves, and record what came back.

Input   reference/references.csv     the register, one row per reference, maintained by hand
Output  reference/link_check.csv     per reference: final URL after redirects, HTTP status,
                                     content type, bytes, the date checked, and — with
                                     ``--download`` — the SHA-256 of the file as served

These are third-party publications. The repository does **not** redistribute them: it records
where each one is, what came back when it was last fetched, and (optionally) the hash of the
edition read, so a reader can pin the same file without this repository carrying a copy.
``--download`` writes the files into ``reference/cache/``, which is ignored by git.

Two kinds of check, because a journal is not a web page:

* a row with a **DOI** is checked against the DOI system's own handle API, which answers whether
  the DOI is registered and where it points, and then against the DOI's registered metadata,
  which answers whether it points at the work the register describes. Scraping the publisher
  instead would prove nothing: Wiley, Annual Reviews, Science and OECD iLibrary all answer an
  automated request with 403 while the article sits there perfectly alive. The metadata check
  earns its keep: it caught a citation in the whitepaper whose DOI belonged to an unrelated
  paper in a different journal.
* a row with only a **URL** is fetched. A 403 or 405 from a host that answered is recorded as
  ``blocked`` - the page exists, the publisher refuses robots - and is not treated as a failure.
  A 404, a 410 or an unreachable host is a dead reference and fails the run.

Run from the repository root:
    .venv/bin/python script/reference/check_references.py [--download] [--key KEY ...]
"""

from __future__ import annotations

import csv
import hashlib
import json
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
OUT = REPO / "reference" / "link_check.csv"
CACHE = REPO / "reference" / "cache"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 tradeimpact/1.0 (research; sanghyun@planit.institute)"
)
CURL = "/usr/bin/curl"
PAUSE_SECONDS = 1.0
#: Statuses that mean the reference is still where the register says it is.
OK_STATUSES = {200, 206, 302, 303}
#: A host that answers this way is refusing the robot, not missing the document.
BLOCKED_STATUSES = {401, 403, 405, 429}
#: The DOI system's own resolver: responseCode 1 means the DOI is registered.
DOI_HANDLE_API = "https://doi.org/api/handles/"
#: Content negotiation on doi.org returns the work's registered metadata as CSL JSON.
CSL_JSON = "application/vnd.citationstyles.csl+json"
#: A DOI that points at a different work is a wrong citation, not a broken link.
MISMATCH_STATUS = 409
#: Share of the register title's significant words that must appear in the registered title.
TITLE_OVERLAP = 0.6
#: Words too common to tell two titles apart.
STOPWORDS = frozenset(
    "a an and as at by for from in of on or the to with into towards their its it that this".split()
)
FIELDS = [
    "key",
    "url",
    "final_url",
    "http_status",
    "content_type",
    "bytes",
    "sha256",
    "transport",
    "registered_title",
    "registered_year",
    "checked",
    "note",
]


def read_register() -> list[dict[str, str]]:
    """The register rows, in file order."""
    with REGISTER.open(newline="") as f:
        return list(csv.DictReader(f))


def resolve_doi(doi: str, context: ssl.SSLContext) -> tuple[int, str]:
    """(handle responseCode, the URL the DOI points at) from the DOI system's own API."""
    request = urllib.request.Request(
        DOI_HANDLE_API + doi.strip(), headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    target = ""
    for value in payload.get("values", []):
        if value.get("type") == "URL":
            target = str(value.get("data", {}).get("value", ""))
            break
    return int(payload.get("responseCode", 0)), target


def doi_metadata(doi: str, context: ssl.SSLContext) -> tuple[str, str]:
    """(title, year) as the DOI's own registered metadata states them."""
    request = urllib.request.Request(
        "https://doi.org/" + doi.strip(),
        headers={"User-Agent": USER_AGENT, "Accept": CSL_JSON},
    )
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    title = payload.get("title", "")
    if isinstance(title, list):
        title = title[0] if title else ""
    parts = payload.get("issued", {}).get("date-parts", [[""]])
    return str(title), str(parts[0][0] if parts and parts[0] else "")


def significant(title: str) -> set[str]:
    """The words of a title that carry its identity."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def titles_agree(registered: str, claimed: str) -> bool:
    """Whether the registered title is recognisably the one the register claims."""
    claimed_words = significant(claimed)
    if not claimed_words:
        return True
    return len(claimed_words & significant(registered)) / len(claimed_words) >= TITLE_OVERLAP


def head(url: str, context: ssl.SSLContext) -> tuple[int, str, str, str]:
    """(status, final url, content type, content length) from a GET that reads nothing."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, context=context, timeout=90) as response:
        return (
            response.status,
            response.url,
            response.headers.get("Content-Type", ""),
            response.headers.get("Content-Length", ""),
        )


def head_with_curl(url: str) -> tuple[int, str, str, str]:
    """The same, via the system curl, for hosts Python's TLS or urllib cannot reach."""
    proc = subprocess.run(
        [
            CURL, "--silent", "--show-error", "--location", "--max-time", "90",
            "--user-agent", USER_AGENT, "--output", "/dev/null",
            "--write-out", "%{http_code}\t%{url_effective}\t%{content_type}\t%{size_download}",
            url,
        ],
        capture_output=True,
        check=True,
        text=True,
    )  # fmt: skip
    status, final, content_type, size = (proc.stdout.strip().split("\t") + ["", "", "", ""])[:4]
    return int(status or 0), final, content_type, size


def download(url: str, into: Path) -> tuple[int, str]:
    """(bytes, SHA-256) of the file as served, saved under the ignored cache directory."""
    into.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            CURL, "--silent", "--show-error", "--fail", "--location", "--max-time", "300",
            "--user-agent", USER_AGENT, "--output", str(into), url,
        ],
        capture_output=True,
        check=True,
        text=True,
    )  # fmt: skip
    body = into.read_bytes()
    return len(body), hashlib.sha256(body).hexdigest()


def check(row: dict[str, str], context: ssl.SSLContext, fetch: bool) -> dict[str, object]:
    """One reference: what its URL returns today."""
    url = row["url"]
    result: dict[str, object] = {
        "key": row["key"],
        "url": url,
        "final_url": "",
        "http_status": "",
        "content_type": "",
        "bytes": "",
        "sha256": "",
        "transport": "urllib",
        "registered_title": "",
        "registered_year": "",
        "checked": date.today().isoformat(),
        "note": "",
    }
    if row.get("doi"):
        result["transport"] = "doi_handle"
        try:
            code, target = resolve_doi(row["doi"], context)
        except Exception as exc:  # noqa: BLE001 - the resolver being down is not a dead reference
            result["http_status"] = 0
            result["note"] = f"DOI resolver unreachable: {exc}"
            return result
        result["final_url"] = target
        if code != 1:
            result["http_status"] = 404
            result["note"] = f"DOI not registered (responseCode {code})"
            return result
        result["http_status"] = 200
        try:
            title, year = doi_metadata(row["doi"], context)
        except Exception as exc:  # noqa: BLE001 - metadata being unavailable is not a dead DOI
            result["note"] = f"registered metadata unavailable: {exc}"
            return result
        result["registered_title"], result["registered_year"] = title, year
        if not titles_agree(title, row["title"]):
            result["http_status"] = MISMATCH_STATUS
            result["note"] = (
                f"the DOI is registered to {title!r}, which is not the work this row describes"
            )
        elif year and year not in f"{row.get('year', '')} {row.get('edition', '')}":
            # An online-first paper has two years; the register carries both, one in `edition`.
            result["note"] = f"the DOI gives the year as {year}, the register says {row['year']}"
        return result
    try:
        status, final, content_type, size = head(url, context)
    except urllib.error.HTTPError as exc:
        status, final, content_type, size = exc.code, url, "", ""
        result["note"] = str(exc.reason)
    except Exception as exc:  # noqa: BLE001 - an unreachable host must not stop the sweep
        try:
            status, final, content_type, size = head_with_curl(url)
            result["transport"] = "curl_system_trust"
        except Exception as curl_exc:  # noqa: BLE001
            result["http_status"] = 0
            result["note"] = f"{exc} / curl: {curl_exc}"
            return result
    result.update(
        {"http_status": status, "final_url": final, "content_type": content_type, "bytes": size}
    )
    if fetch and status in OK_STATUSES:
        suffix = ".pdf" if "pdf" in content_type.lower() else ".html"
        size_bytes, digest = download(url, CACHE / f"{row['key']}{suffix}")
        result["bytes"], result["sha256"] = size_bytes, digest
    return result


def main() -> None:
    """Check every reference (or the ones named with --key) and write the result table."""
    argv = sys.argv[1:]
    fetch = "--download" in argv
    wanted = {argv[i + 1] for i, a in enumerate(argv) if a == "--key" and i + 1 < len(argv)}
    rows = [r for r in read_register() if not wanted or r["key"] in wanted]
    context = ssl.create_default_context(cafile=certifi.where())
    results = []
    for row in rows:
        results.append(check(row, context, fetch))
        time.sleep(PAUSE_SECONDS)
    if wanted and OUT.exists():
        # Carry the rows this run did not check, but drop any whose reference has since left
        # the register: a stale row would report a dead link for something nobody cites.
        registered = {r["key"] for r in read_register()}
        keep = [
            r
            for r in csv.DictReader(OUT.open(newline=""))
            if r["key"] not in wanted and r["key"] in registered
        ]
        results = keep + results
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, FIELDS)
        writer.writeheader()
        writer.writerows(sorted(results, key=lambda r: str(r["key"])))
    status_of = {r["key"]: int(r["http_status"] or 0) for r in results}
    blocked = [r for r in results if status_of[r["key"]] in BLOCKED_STATUSES]
    wrong = [r for r in results if status_of[r["key"]] == MISMATCH_STATUS]
    fine = OK_STATUSES | BLOCKED_STATUSES | {MISMATCH_STATUS}
    dead = [r for r in results if status_of[r["key"]] not in fine]
    print(
        f"{OUT.relative_to(REPO)}: {len(results)} references checked, "
        f"{len(results) - len(dead) - len(blocked) - len(wrong)} resolving, "
        f"{len(blocked)} reachable but refusing robots, {len(wrong)} pointing at another work, "
        f"{len(dead)} dead"
    )
    for r in wrong + dead:
        print(f"  FAIL {r['key']}: {r['http_status']} {r['url']} {r['note']}")
    for r in results:
        if r["note"] and status_of[r["key"]] not in {MISMATCH_STATUS} and r not in dead:
            print(f"  note {r['key']}: {r['note']}")
    if dead or wrong:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
