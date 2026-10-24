"""Remove the radar chart and the date range from generated 3D contribution SVGs."""
import re
import sys

# Position of the radar group in the 1280x850 layout: translate(980, 284.5)
RADAR_X, RADAR_Y, TOLERANCE = 980.0, 284.5, 2.0

DATE_TEXT = re.compile(
    r'<text[^>]*class="fill-weak"[^>]*>\s*\d{4}-\d{2}-\d{2} / \d{4}-\d{2}-\d{2}\s*</text>'
)
GROUP_OPEN = re.compile(
    r'<g\b[^>]*\btransform="translate\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)"[^>]*>'
)
TAG = re.compile(r"<(/?)g\b[^>]*?(/?)>")


def remove_radar(svg: str) -> tuple[str, bool]:
    for match in GROUP_OPEN.finditer(svg):
        x, y = float(match.group(1)), float(match.group(2))
        if abs(x - RADAR_X) > TOLERANCE or abs(y - RADAR_Y) > TOLERANCE:
            continue
        depth = 0
        for tag in TAG.finditer(svg, match.start()):
            if tag.group(2) == "/":
                continue  # self-closing <g/>
            depth += -1 if tag.group(1) == "/" else 1
            if depth == 0:
                return svg[: match.start()] + svg[tag.end():], True
    return svg, False


def main(paths: list[str]) -> None:
    for path in paths:
        with open(path, encoding="utf-8") as f:
            svg = f.read()
        svg, radar_removed = remove_radar(svg)
        svg, date_count = DATE_TEXT.subn("", svg)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"{path}: radar removed={radar_removed}, date removed={date_count}")


if __name__ == "__main__":
    main(sys.argv[1:])
