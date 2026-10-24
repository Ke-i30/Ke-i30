"""Post-process generated 3D contribution SVGs.

- removes the radar chart and the date range
- replaces the language donut with a fixed, hand-defined language mix
  (same position, size and style as the original donut)
"""
import math
import re
import sys

# label, color, share. The donut keeps this order, clockwise from the top.
# These values are chosen by hand, they are not measured from GitHub.
LANGUAGES = [
    ("TypeScript", "#3178c6", 30),
    ("JavaScript", "#f1e05a", 22),
    ("Python", "#3572a5", 16),
    ("Java", "#b07219", 11),
    ("Flutter", "#54c5f8", 9),
    ("C++", "#f34b7d", 6),
    ("HTML", "#e34c26", 4),
    ("CSS", "#563d7c", 2),
]

# Group positions in the 1280x850 layout
RADAR_POS = (980.0, 284.5)  # translate(980, 284.5)
PIE_POS = (40.0, 520.0)  # translate(40, 520), 520x260 box
TOLERANCE = 2.0

DATE_TEXT = re.compile(
    r'<text[^>]*class="fill-weak"[^>]*>\s*\d{4}-\d{2}-\d{2} / \d{4}-\d{2}-\d{2}\s*</text>'
)
GROUP_OPEN = re.compile(
    r'<g\b[^>]*\btransform="translate\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)"[^>]*>'
)
TAG = re.compile(r"<(/?)g\b[^>]*?(/?)>")


def remove_group(svg: str, pos: tuple[float, float]) -> tuple[str, int, bool]:
    """Remove the <g> placed at translate(pos). Returns (svg, start index, found)."""
    for match in GROUP_OPEN.finditer(svg):
        x, y = float(match.group(1)), float(match.group(2))
        if abs(x - pos[0]) > TOLERANCE or abs(y - pos[1]) > TOLERANCE:
            continue
        depth = 0
        for tag in TAG.finditer(svg, match.start()):
            if tag.group(2) == "/":
                continue  # self-closing <g/>
            depth += -1 if tag.group(1) == "/" else 1
            if depth == 0:
                return svg[: match.start()] + svg[tag.end():], match.start(), True
    return svg, 0, False


def donut_group() -> str:
    """Language donut with the same geometry as the original (520x260 box, 8 rows)."""
    height = 260.0
    radius = height / 2
    outer, inner = radius - radius / 10, radius / 2
    rows = 8
    offset = (rows - len(LANGUAGES)) / 2 + 0.5
    font = height / rows / 1.5
    total = float(sum(share for _, _, share in LANGUAGES))
    steps = 5

    def fade(i: int) -> str:
        count = len(LANGUAGES) + steps
        return ";".join(
            "0" if k < i else f"{min((k - i) / steps, 1):g}" for k in range(count)
        )

    def anim(i: int) -> str:
        return (
            f'<animate attributeName="fill-opacity" values="{fade(i)}" '
            'dur="3s" repeatCount="1"></animate>'
        )

    def point(r: float, a: float) -> str:
        return f"{r * math.sin(a):.2f},{-r * math.cos(a):.2f}"

    paths, markers, labels = [], [], []
    start = 0.0
    for i, (name, color, share) in enumerate(LANGUAGES):
        end = start + share / total * 2 * math.pi
        large = 1 if end - start > math.pi else 0
        d = (
            f"M{point(outer, start)}A{outer:g},{outer:g},0,{large},1,{point(outer, end)}"
            f"L{point(inner, end)}A{inner:g},{inner:g},0,{large},0,{point(inner, start)}Z"
        )
        paths.append(
            f'<path d="{d}" style="fill: {color};" class="stroke-bg" stroke-width="2px">'
            f"<title>{name}</title>{anim(i)}</path>"
        )
        y = (i + offset) * (height / rows)
        markers.append(
            f'<rect x="0" y="{y - font / 2:.2f}" width="{font:.2f}" height="{font:.2f}" '
            f'fill="{color}" class="stroke-bg" stroke-width="1px">{anim(i)}</rect>'
        )
        labels.append(
            f'<text dominant-baseline="middle" x="{font * 1.2:.2f}" y="{y:.2f}" '
            f'class="fill-fg" font-size="{font:.2f}px">{name}{anim(i)}</text>'
        )
        start = end

    return (
        f'<g transform="translate({PIE_POS[0]:g}, {PIE_POS[1]:g})">'
        f'<g transform="translate({radius * 2.1:g}, 0)">{"".join(markers)}{"".join(labels)}</g>'
        f'<g transform="translate({radius:g}, {radius:g})">{"".join(paths)}</g>'
        "</g>"
    )


def main(paths: list[str]) -> None:
    for path in paths:
        with open(path, encoding="utf-8") as f:
            svg = f.read()
        svg, _, radar_removed = remove_group(svg, RADAR_POS)
        svg, date_count = DATE_TEXT.subn("", svg)
        svg, index, pie_found = remove_group(svg, PIE_POS)
        if pie_found:
            svg = svg[:index] + donut_group() + svg[index:]
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(
            f"{path}: radar removed={radar_removed}, date removed={date_count}, "
            f"languages replaced={pie_found}"
        )


if __name__ == "__main__":
    main(sys.argv[1:])
