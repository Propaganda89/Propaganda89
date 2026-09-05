#!/usr/bin/env python3
"""Render a GitHub contribution graph as two theme-paired SVGs in the HM brand palette.

Data comes from GitHub's own public endpoint (https://github.com/users/<user>/contributions),
so there is no token, no API key and no third-party badge service in the path. Private
contributions appear automatically once "Include private contributions on my profile" is
enabled in GitHub profile settings.

Standard library only, so the GitHub Action needs no dependency install.

    python3 tools/contributions.py --user Propaganda89 --out assets
"""
from __future__ import annotations
import argparse, datetime as dt, html, re, sys, urllib.error, urllib.request

UA = "Mozilla/5.0 (compatible; profile-readme-contribution-graph/1.0)"

# Level ramp: one hue, monotonic in luminance, straight from the locked brand ramp.
# Dark brightens toward the brand pop; light darkens, because #04F404 is 1.51:1 on white.
DARK = {
    "bg": "none", "empty": "#1B241F",
    "levels": ["#1B241F", "#004D2C", "#00713C", "#27BD53", "#04F404"],
    "label": "#919B94", "legend": "#626C65",
}
LIGHT = {
    "bg": "none", "empty": "#E9EEEA",
    "levels": ["#E9EEEA", "#BBF5B9", "#47DC58", "#069A4A", "#00713C"],
    "label": "#626C65", "legend": "#8A948C",
}

CELL, GAP = 12, 3
PITCH = CELL + GAP
LEFT, TOP = 32, 22
LEGEND_H = 26
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def fetch(user: str, timeout: int = 30) -> str:
    url = "https://github.com/users/%s/contributions" % urllib.parse.quote(user)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse(page: str):
    """-> (list of (date, level), total_contributions or None)"""
    cells = []
    for m in re.finditer(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d+)"', page):
        cells.append((dt.date.fromisoformat(m.group(1)), int(m.group(2))))
    if not cells:  # attribute order is not guaranteed; try the reverse
        for m in re.finditer(r'data-level="(\d+)"[^>]*?data-date="(\d{4}-\d{2}-\d{2})"', page):
            cells.append((dt.date.fromisoformat(m.group(2)), int(m.group(1))))
    cells.sort(key=lambda c: c[0])
    total = None
    m = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", html.unescape(page), re.I)
    if m:
        total = int(m.group(1).replace(",", ""))
    return cells, total


def render(cells, theme: dict, title: str) -> str:
    if not cells:
        raise SystemExit("no contribution cells parsed - GitHub markup may have changed")
    # GitHub weeks start on Sunday; column 0 is the week containing the first cell.
    def col_of(d: dt.date) -> int:
        return ((d - start).days + start_dow) // 7
    first = cells[0][0]
    start_dow = (first.weekday() + 1) % 7          # Sun=0
    start = first - dt.timedelta(days=start_dow)
    weeks = col_of(cells[-1][0]) + 1
    w = LEFT + weeks * PITCH - GAP
    h = TOP + 7 * PITCH - GAP + LEGEND_H

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
           'role="img" aria-labelledby="ttl dsc" fill="none">' % (w, h, w, h),
           '<title id="ttl">%s</title>' % html.escape(title),
           '<desc id="dsc">A year of GitHub contributions, one square per day, '
           'shaded from fewest to most.</desc>']
    fam = ('font-family="Arial, Helvetica, sans-serif"')   # metrically consistent everywhere

    # month labels
    seen = set()
    for d, _ in cells:
        c = col_of(d)
        if d.month not in seen and d.day <= 7:
            seen.add(d.month)
            x = LEFT + c * PITCH
            if x < w - 24:
                out.append('<text x="%d" y="%d" %s font-size="10" fill="%s">%s</text>'
                           % (x, TOP - 8, fam, theme["label"], MONTHS[d.month - 1]))
    # weekday labels (Mon/Wed/Fri, as GitHub does)
    for dow, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append('<text x="0" y="%d" %s font-size="10" fill="%s">%s</text>'
                   % (TOP + dow * PITCH + CELL - 2, fam, theme["label"], name))
    # cells
    for d, lvl in cells:
        x = LEFT + col_of(d) * PITCH
        y = TOP + ((d.weekday() + 1) % 7) * PITCH
        fill = theme["levels"][max(0, min(lvl, 4))]
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2.5" fill="%s"/>'
                   % (x, y, CELL, CELL, fill))
    # legend
    ly = TOP + 7 * PITCH + 8
    lx = w - (5 * PITCH + 74)
    out.append('<text x="%d" y="%d" %s font-size="10" fill="%s">Less</text>'
               % (lx, ly + CELL - 2, fam, theme["legend"]))
    for i, col in enumerate(theme["levels"]):
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2.5" fill="%s"/>'
                   % (lx + 30 + i * PITCH, ly, CELL, CELL, col))
    out.append('<text x="%d" y="%d" %s font-size="10" fill="%s">More</text>'
               % (lx + 30 + 5 * PITCH + 4, ly + CELL - 2, fam, theme["legend"]))
    out.append("</svg>")
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", default="assets")
    ap.add_argument("--from-file", help="read saved HTML instead of fetching (for testing)")
    a = ap.parse_args()

    page = open(a.from_file, encoding="utf-8", errors="replace").read() if a.from_file else fetch(a.user)
    cells, total = parse(page)
    title = "%s — GitHub contributions in the last year" % a.user
    for name, theme in (("dark", DARK), ("light", LIGHT)):
        path = "%s/contributions-%s.svg" % (a.out.rstrip("/"), name)
        open(path, "w", encoding="utf-8").write(render(cells, theme, title))
        print("wrote %s" % path)
    active = sum(1 for _, l in cells if l > 0)
    print("%d days parsed, %d with activity, total contributions: %s"
          % (len(cells), active, total if total is not None else "unknown"))
    if active == 0:
        print("WARNING: no activity in the window - the graph will render empty.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    import urllib.parse
    raise SystemExit(main())
