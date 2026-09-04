"""Inline-SVG chart primitives for the analysis report.

Every chart is a string of SVG with no script, no external file and no embedded raster, so the
report stays one self-contained file that opens from disk and prints. Colours come from CSS
custom properties defined by the report stylesheet, which is what lets the same markup work in
light and dark rendering without redrawing.

Each function takes values already computed by the caller and does only geometry: it never
reads a database and never rounds a published figure into a different one than the report's
prose states.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Plot geometry in user units; the viewBox scales it to whatever width the page gives.
WIDTH = 760
ROW_H = 22
PAD_TOP = 26
PAD_BOTTOM = 34
GRID_STEPS = 5


def esc(text: str) -> str:
    """XML-escape a label."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _nice(limit: float) -> float:
    """Round an axis limit up to a readable step."""
    if limit <= 0:
        return 1.0
    magnitude = 10.0 ** (len(f"{int(limit)}") - 1)
    for step in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0):
        if limit <= step * magnitude:
            return step * magnitude
    return 10.0 * magnitude


def _fmt(value: float, dp: int) -> str:
    """Axis tick label."""
    if dp == 0:
        return f"{value:,.0f}"
    return f"{value:,.{dp}f}"


@dataclass(frozen=True)
class Series:
    """One named set of values sharing an x axis."""

    name: str
    values: list[float]
    colour: str


def _axis(values: list[float]) -> tuple[float, float]:
    """Nice axis limits that use the width a one-sided distribution actually needs.

    A symmetric axis wastes half the plot when every bar points the same way, and crowds the
    labels of the long bars into the row labels. So the negative and positive sides are rounded
    up independently and the zero line sits where the data puts it.
    """
    lo = min(0.0, min(values))
    hi = max(0.0, max(values))
    span_neg = _nice(abs(lo)) if lo < 0 else 0.0
    span_pos = _nice(hi) if hi > 0 else 0.0
    if span_neg == 0.0 and span_pos == 0.0:
        return 0.0, 1.0
    return span_neg, span_pos


def _ticks(span_neg: float, span_pos: float) -> list[float]:
    """Tick values across an asymmetric axis, always including zero."""
    out = [0.0]
    for span, sign in ((span_neg, -1.0), (span_pos, 1.0)):
        if span <= 0:
            continue
        steps = GRID_STEPS if span_neg and span_pos else GRID_STEPS * 2
        for k in range(1, steps + 1):
            out.append(sign * span * k / steps)
    return sorted(out)


def _place(x: float, value: float, left: float, right: float) -> tuple[float, str, str]:
    """Where to write a bar's value label, and how, so it never runs into the row labels."""
    if value >= 0:
        if x + 34 <= right:
            return x + 5, "start", "value"
        return x - 4, "end", "value inbar"
    if x - 34 >= left:
        return x - 5, "end", "value"
    return x + 4, "start", "value inbar"


def frame(width: int, height: int, body: str, label: str) -> str:
    """Wrap plot geometry in a responsive, labelled SVG element."""
    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(label)}">{body}</svg>'
    )


def diverging_bars(
    rows: list[tuple[str, float]],
    *,
    unit: str,
    label: str,
    dp: int = 1,
    colours: tuple[str, str] = ("var(--pos)", "var(--neg)"),
    label_width: int = 190,
) -> str:
    """Horizontal bars around a zero line, one row per label.

    Args:
        rows: (label, value) in plot order, top to bottom.
        unit: Axis unit, written under the axis.
        label: Accessible description of the whole chart.
        dp: Decimal places on the tick labels and the value annotations.
        colours: (positive, negative) CSS colour expressions.
        label_width: User units reserved for the row labels.

    Returns:
        One SVG element.
    """
    if not rows:
        return ""
    height = PAD_TOP + ROW_H * len(rows) + PAD_BOTTOM
    plot_w = WIDTH - label_width - 70
    span_neg, span_pos = _axis([v for _, v in rows])
    total = span_neg + span_pos
    zero = label_width + plot_w * span_neg / total
    scale = plot_w / total
    plot_right = label_width + plot_w

    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{height}" class="plot-bg"/>']
    for tick in _ticks(span_neg, span_pos):
        x = zero + tick * scale
        parts.append(
            f'<line x1="{x:.1f}" y1="{PAD_TOP - 8}" x2="{x:.1f}" '
            f'y2="{PAD_TOP + ROW_H * len(rows)}" class="grid"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{PAD_TOP + ROW_H * len(rows) + 14}" '
            f'class="tick" text-anchor="middle">{_fmt(tick, dp)}</text>'
        )
    for i, (name, value) in enumerate(rows):
        y = PAD_TOP + i * ROW_H
        w = abs(value) * scale
        x = zero if value >= 0 else zero - w
        colour = colours[0] if value >= 0 else colours[1]
        parts.append(
            f'<rect x="{x:.1f}" y="{y + 3}" width="{max(w, 0.6):.1f}" height="{ROW_H - 8}" '
            f'fill="{colour}"/>'
        )
        parts.append(
            f'<text x="{label_width - 8}" y="{y + ROW_H / 2 + 3}" class="row-label" '
            f'text-anchor="end">{esc(name)}</text>'
        )
        end = x + w if value >= 0 else x
        tx, anchor, klass = _place(end, value, label_width, plot_right)
        parts.append(
            f'<text x="{tx:.1f}" y="{y + ROW_H / 2 + 3}" class="{klass}" '
            f'text-anchor="{anchor}">{_fmt(value, dp)}</text>'
        )
    parts.append(
        f'<line x1="{zero:.1f}" y1="{PAD_TOP - 8}" x2="{zero:.1f}" '
        f'y2="{PAD_TOP + ROW_H * len(rows)}" class="zero"/>'
    )
    parts.append(
        f'<text x="{WIDTH - 4}" y="14" class="axis-unit" text-anchor="end">{esc(unit)}</text>'
    )
    return frame(WIDTH, height, "".join(parts), label)


def grouped_bars(
    rows: list[tuple[str, list[tuple[str, float]]]],
    *,
    unit: str,
    label: str,
    palette: dict[str, str],
    dp: int = 1,
    label_width: int = 190,
) -> str:
    """Horizontal bars around zero, several series per row.

    Args:
        rows: (row label, [(series name, value)]) in plot order.
        unit: Axis unit.
        label: Accessible description.
        palette: series name -> CSS colour expression.
        dp: Decimal places.
        label_width: User units reserved for the row labels.

    Returns:
        One SVG element.
    """
    if not rows:
        return ""
    per_row = max(len(series) for _, series in rows)
    band = 11
    row_h = band * per_row + 10
    height = PAD_TOP + row_h * len(rows) + PAD_BOTTOM
    plot_w = WIDTH - label_width - 70
    span_neg, span_pos = _axis([v for _, series in rows for _, v in series])
    total = span_neg + span_pos
    zero = label_width + plot_w * span_neg / total
    scale = plot_w / total
    plot_right = label_width + plot_w

    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{height}" class="plot-bg"/>']
    for tick in _ticks(span_neg, span_pos):
        x = zero + tick * scale
        parts.append(
            f'<line x1="{x:.1f}" y1="{PAD_TOP - 8}" x2="{x:.1f}" '
            f'y2="{PAD_TOP + row_h * len(rows)}" class="grid"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{PAD_TOP + row_h * len(rows) + 14}" class="tick" '
            f'text-anchor="middle">{_fmt(tick, dp)}</text>'
        )
    for i, (name, series) in enumerate(rows):
        top = PAD_TOP + i * row_h
        parts.append(
            f'<text x="{label_width - 8}" y="{top + row_h / 2 + 3}" class="row-label" '
            f'text-anchor="end">{esc(name)}</text>'
        )
        for j, (sname, value) in enumerate(series):
            y = top + 5 + j * band
            w = abs(value) * scale
            x = zero if value >= 0 else zero - w
            parts.append(
                f'<rect x="{x:.1f}" y="{y}" width="{max(w, 0.6):.1f}" height="{band - 3}" '
                f'fill="{palette[sname]}"/>'
            )
            end = x + w if value >= 0 else x
            tx, anchor, klass = _place(end, value, label_width, plot_right)
            parts.append(
                f'<text x="{tx:.1f}" y="{y + band - 5}" class="{klass} small" '
                f'text-anchor="{anchor}">{_fmt(value, dp)}</text>'
            )
    parts.append(
        f'<line x1="{zero:.1f}" y1="{PAD_TOP - 8}" x2="{zero:.1f}" '
        f'y2="{PAD_TOP + row_h * len(rows)}" class="zero"/>'
    )
    parts.append(
        f'<text x="{WIDTH - 4}" y="14" class="axis-unit" text-anchor="end">{esc(unit)}</text>'
    )
    return frame(WIDTH, height, "".join(parts), label)


def lines(
    series: list[Series],
    x_labels: list[str],
    *,
    unit: str,
    label: str,
    height: int = 300,
    dp: int = 1,
    fill_between: tuple[str, str] | None = None,
    zero_line: bool = True,
) -> str:
    """A line chart over a shared categorical x axis, optionally shading between two series.

    Args:
        series: One entry per line; every entry must have the same number of values.
        x_labels: Tick labels, one per x position.
        unit: Axis unit for the y axis.
        label: Accessible description.
        height: Plot height in user units.
        dp: Decimal places on the y ticks.
        fill_between: Names of two series to shade between, or None.
        zero_line: Draw a rule at y = 0 when the range crosses it.

    Returns:
        One SVG element.
    """
    if not series or not x_labels:
        return ""
    left, right, top, bottom = 62, 14, 18, 40
    plot_w, plot_h = WIDTH - left - right, height - top - bottom
    flat = [v for s in series for v in s.values]
    lo, hi = min(flat), max(flat)
    if lo > 0:
        lo = 0.0
    if hi < 0:
        hi = 0.0
    span = _nice(max(abs(lo), abs(hi)) or 1.0)
    lo_axis = -span if lo < 0 else 0.0
    hi_axis = span if hi > 0 else 0.0
    if hi_axis == lo_axis:
        hi_axis = span

    def px(i: int) -> float:
        n = max(len(x_labels) - 1, 1)
        return left + plot_w * i / n

    def py(v: float) -> float:
        return top + plot_h * (hi_axis - v) / (hi_axis - lo_axis)

    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{height}" class="plot-bg"/>']
    ticks = GRID_STEPS
    for k in range(ticks + 1):
        v = lo_axis + (hi_axis - lo_axis) * k / ticks
        y = py(v)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" class="grid"/>'
        )
        parts.append(
            f'<text x="{left - 6}" y="{y + 3:.1f}" class="tick" text-anchor="end">'
            f"{_fmt(v, dp)}</text>"
        )
    step = max(1, len(x_labels) // 12)
    for i, xl in enumerate(x_labels):
        if i % step:
            continue
        parts.append(
            f'<text x="{px(i):.1f}" y="{top + plot_h + 16}" class="tick" '
            f'text-anchor="middle">{esc(xl)}</text>'
        )
    if zero_line and lo_axis < 0 < hi_axis:
        parts.append(
            f'<line x1="{left}" y1="{py(0):.1f}" x2="{left + plot_w}" '
            f'y2="{py(0):.1f}" class="zero"/>'
        )
    if fill_between:
        a = next(s for s in series if s.name == fill_between[0])
        b = next(s for s in series if s.name == fill_between[1])
        up = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(a.values))
        down = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in reversed(list(enumerate(b.values))))
        parts.append(f'<polygon points="{up} {down}" class="band"/>')
    for s in series:
        points = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(s.values))
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{s.colour}" stroke-width="2"/>'
        )
    parts.append(
        f'<text x="{WIDTH - 4}" y="12" class="axis-unit" text-anchor="end">{esc(unit)}</text>'
    )
    return frame(WIDTH, height, "".join(parts), label)


def dots(
    rows: list[tuple[str, float]],
    *,
    unit: str,
    label: str,
    dp: int = 0,
    label_width: int = 60,
    highlight: dict[str, str] | None = None,
) -> str:
    """A one-dimensional dot plot with a zero rule: one dot per label, sorted by the caller.

    Args:
        rows: (label, value) in plot order.
        unit: Axis unit.
        label: Accessible description.
        dp: Decimal places on the ticks.
        label_width: User units for the labels.
        highlight: label -> CSS colour expression for dots that should stand out.

    Returns:
        One SVG element.
    """
    if not rows:
        return ""
    row_h = 15
    height = PAD_TOP + row_h * len(rows) + PAD_BOTTOM
    plot_w = WIDTH - label_width - 80
    values = [v for _, v in rows]
    span_neg, span_pos = _axis(values)
    total = span_neg + span_pos
    zero = label_width + plot_w * span_neg / total
    scale = plot_w / total
    plot_right = label_width + plot_w
    highlight = highlight or {}

    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{height}" class="plot-bg"/>']
    for tick in _ticks(span_neg, span_pos):
        x = zero + tick * scale
        parts.append(
            f'<line x1="{x:.1f}" y1="{PAD_TOP - 8}" x2="{x:.1f}" '
            f'y2="{PAD_TOP + row_h * len(rows)}" class="grid"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{PAD_TOP + row_h * len(rows) + 14}" class="tick" '
            f'text-anchor="middle">{_fmt(tick, dp)}</text>'
        )
    parts.append(
        f'<line x1="{zero:.1f}" y1="{PAD_TOP - 8}" x2="{zero:.1f}" '
        f'y2="{PAD_TOP + row_h * len(rows)}" class="zero"/>'
    )
    for i, (name, value) in enumerate(rows):
        y = PAD_TOP + i * row_h + row_h / 2
        x = zero + value * scale
        colour = highlight.get(name, "var(--pos)" if value >= 0 else "var(--neg)")
        parts.append(f'<line x1="{zero:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}" class="stem"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{colour}"/>')
        parts.append(
            f'<text x="{label_width - 8}" y="{y + 3:.1f}" class="row-label small" '
            f'text-anchor="end">{esc(name)}</text>'
        )
        tx, anchor, klass = _place(x + (4 if value >= 0 else -4), value, label_width, plot_right)
        parts.append(
            f'<text x="{tx:.1f}" y="{y + 3:.1f}" class="{klass} small" '
            f'text-anchor="{anchor}">{_fmt(value, dp)}</text>'
        )
    parts.append(
        f'<text x="{WIDTH - 4}" y="14" class="axis-unit" text-anchor="end">{esc(unit)}</text>'
    )
    return frame(WIDTH, height, "".join(parts), label)


def ranges(
    rows: list[tuple[str, float, float, float]],
    *,
    unit: str,
    label: str,
    dp: int = 1,
    label_width: int = 210,
) -> str:
    """A tornado plot: a bar from low to high with the central value marked.

    Args:
        rows: (label, low, central, high) in plot order.
        unit: Axis unit.
        label: Accessible description.
        dp: Decimal places.
        label_width: User units for the labels.

    Returns:
        One SVG element.
    """
    if not rows:
        return ""
    row_h = 24
    height = PAD_TOP + row_h * len(rows) + PAD_BOTTOM
    plot_w = WIDTH - label_width - 80
    flat = [v for _, lo, mid, hi in rows for v in (lo, mid, hi)]
    span_neg, span_pos = _axis(flat)
    total = span_neg + span_pos
    zero = label_width + plot_w * span_neg / total
    scale = plot_w / total

    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{height}" class="plot-bg"/>']
    for tick in _ticks(span_neg, span_pos):
        x = zero + tick * scale
        parts.append(
            f'<line x1="{x:.1f}" y1="{PAD_TOP - 8}" x2="{x:.1f}" '
            f'y2="{PAD_TOP + row_h * len(rows)}" class="grid"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{PAD_TOP + row_h * len(rows) + 14}" class="tick" '
            f'text-anchor="middle">{_fmt(tick, dp)}</text>'
        )
    for i, (name, lo, mid, hi) in enumerate(rows):
        y = PAD_TOP + i * row_h
        x1, x2 = zero + min(lo, hi) * scale, zero + max(lo, hi) * scale
        parts.append(
            f'<rect x="{x1:.1f}" y="{y + 5}" width="{max(x2 - x1, 1):.1f}" height="{row_h - 12}" '
            f'class="range"/>'
        )
        xm = zero + mid * scale
        parts.append(
            f'<line x1="{xm:.1f}" y1="{y + 3}" x2="{xm:.1f}" y2="{y + row_h - 4}" class="central"/>'
        )
        parts.append(
            f'<text x="{label_width - 8}" y="{y + row_h / 2 + 3}" class="row-label small" '
            f'text-anchor="end">{esc(name)}</text>'
        )
        parts.append(
            f'<text x="{x2 + 6:.1f}" y="{y + row_h / 2 + 3}" class="value small">'
            f"{_fmt(min(lo, hi), dp)} to {_fmt(max(lo, hi), dp)}</text>"
        )
    parts.append(
        f'<line x1="{zero:.1f}" y1="{PAD_TOP - 8}" x2="{zero:.1f}" '
        f'y2="{PAD_TOP + row_h * len(rows)}" class="zero"/>'
    )
    parts.append(
        f'<text x="{WIDTH - 4}" y="14" class="axis-unit" text-anchor="end">{esc(unit)}</text>'
    )
    return frame(WIDTH, height, "".join(parts), label)


def stacked_shares(
    rows: list[tuple[str, list[tuple[str, float]]]],
    *,
    label: str,
    palette: dict[str, str],
    label_width: int = 150,
) -> str:
    """Stacked 100 % bars, one row per label; values are shares that need not fill the bar.

    Args:
        rows: (row label, [(segment name, share of 1.0)]).
        label: Accessible description.
        palette: segment name -> CSS colour expression.
        label_width: User units for the labels.

    Returns:
        One SVG element.
    """
    if not rows:
        return ""
    row_h = 26
    height = PAD_TOP + row_h * len(rows) + PAD_BOTTOM
    plot_w = WIDTH - label_width - 60
    parts = [f'<rect x="0" y="0" width="{WIDTH}" height="{height}" class="plot-bg"/>']
    for k in range(6):
        x = label_width + plot_w * k / 5
        parts.append(
            f'<line x1="{x:.1f}" y1="{PAD_TOP - 8}" x2="{x:.1f}" '
            f'y2="{PAD_TOP + row_h * len(rows)}" class="grid"/>'
        )
        parts.append(
            f'<text x="{x:.1f}" y="{PAD_TOP + row_h * len(rows) + 14}" class="tick" '
            f'text-anchor="middle">{k * 20} %</text>'
        )
    for i, (name, segments) in enumerate(rows):
        y = PAD_TOP + i * row_h
        cursor = float(label_width)
        for sname, share in segments:
            w = plot_w * share
            parts.append(
                f'<rect x="{cursor:.1f}" y="{y + 4}" width="{max(w, 0.4):.1f}" '
                f'height="{row_h - 11}" fill="{palette[sname]}"/>'
            )
            if w > 34:
                parts.append(
                    f'<text x="{cursor + w / 2:.1f}" y="{y + row_h / 2 + 2}" '
                    f'class="value small inbar" text-anchor="middle">{share * 100:.0f} %</text>'
                )
            cursor += w
        parts.append(
            f'<text x="{label_width - 8}" y="{y + row_h / 2 + 3}" class="row-label" '
            f'text-anchor="end">{esc(name)}</text>'
        )
    return frame(WIDTH, height, "".join(parts), label)


def legend(items: list[tuple[str, str]]) -> str:
    """A colour key rendered as HTML, so it wraps with the text around it."""
    chips = "".join(
        f'<span class="key"><i style="background:{colour}"></i>{esc(name)}</span>'
        for name, colour in items
    )
    return f'<p class="legend">{chips}</p>'
