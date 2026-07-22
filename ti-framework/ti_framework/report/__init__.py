# SPDX-License-Identifier: GPL-3.0-or-later
"""Output writers (CSV/JSON + data-quality declaration) and plots."""

from ti_framework.report.outputs import (
    data_quality_text,
    to_json_dict,
    write_all,
)

__all__ = ["write_all", "to_json_dict", "data_quality_text"]
