import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "api"))

from compute import MAX_REQUEST_BYTES, compute, validate_payload  # noqa: E402


def _payload() -> dict:
    return json.loads((REPO / "ti-framework" / "fixtures" / "reference_case.json").read_text())


def test_public_compute_accepts_the_reference_contract():
    result = compute(_payload())
    assert set(result["cohorts"]) == {"S1", "S2", "S3"}
    assert MAX_REQUEST_BYTES == 1_000_000


def test_engine_imports_in_a_clean_process():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                f"sys.path.insert(0, {str(REPO / 'ti-framework')!r}); "
                "import ti_framework; import ti_framework.io.schema"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda p: p["support"].update(lifetime_T=51), "support.lifetime_T"),
        (lambda p: p["placements"].__imul__(501), "placements"),
        (lambda p: p["placements"][0].update(units=-1), "units"),
        (lambda p: p["countries"]["KR"]["r_fleet"].update(s2=1.1), "r_fleet.s2"),
        (lambda p: p["placements"][0].update(country="ZZ"), "included country"),
    ],
)
def test_public_compute_rejects_unbounded_or_invalid_inputs(mutate, message):
    payload = _payload()
    mutate(payload)
    with pytest.raises(ValueError, match=message):
        validate_payload(payload)
