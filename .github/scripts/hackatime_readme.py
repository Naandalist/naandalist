"""Update the README wakatime section with the last 7 days of Hackatime stats.

Output mimics athul/waka-readme so the README looks the same.
"""
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = os.environ.get("HACKATIME_USERNAME", "Huruhara")
API_KEY = os.environ.get("HACKATIME_API_KEY", "")
README = os.environ.get("TARGET_PATH", "README.md")
SECTION = os.environ.get("SECTION_NAME", "wakatime")
CODE_LANG = os.environ.get("CODE_LANG", "typescript")
LANG_COUNT = int(os.environ.get("LANG_COUNT", "10"))
BLOCKS = os.environ.get("BLOCKS", "░▒▓█")
GRAPH_LEN = 25
DAYS = int(os.environ.get("DAYS", "7"))


def fetch_stats():
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS)
    query = urllib.parse.urlencode({
        "features": "languages",
        "limit": LANG_COUNT,
        "start_date": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_date": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    url = f"https://hackatime.hackclub.com/api/v1/users/{USERNAME}/stats?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "naandalist-readme"})
    if API_KEY:
        token = base64.b64encode(API_KEY.encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)
    return body.get("data", body)


def human(seconds):
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    parts = []
    if h:
        parts.append(f"{h} hr" + ("s" if h != 1 else ""))
    if m or not h:
        parts.append(f"{m} min" + ("s" if m != 1 else ""))
    return " ".join(parts)


def graph(percent):
    markers = len(BLOCKS) - 1
    proportion = percent / 100 * GRAPH_LEN
    bar = BLOCKS[-1] * int(proportion + 0.5 / markers)
    remainder = int((proportion - len(bar)) * markers + 0.5)
    if remainder > 0:
        bar += BLOCKS[remainder]
    return bar + BLOCKS[0] * (GRAPH_LEN - len(bar))


def build(stats):
    now = datetime.now(timezone(timedelta(hours=7)))
    lines = [
        f"Last {DAYS} Days - Updated: {now.strftime('%d %B %Y')}",
        "",
        f"Total Time: {human(stats.get('total_seconds', 0))}",
        "",
    ]
    langs = (stats.get("languages") or [])[:LANG_COUNT]
    if not langs:
        lines.append("No activity tracked")
        return "\n".join(lines)
    pad = max(len(l["name"]) for l in langs)
    for l in langs:
        t = human(l.get("total_seconds", 0))
        p = float(l.get("percent", 0))
        lines.append(f"{l['name'].ljust(pad)}   {t: <18}{graph(p)}   {p:05.2f} %")
    return "\n".join(lines)


def main():
    stats = fetch_stats()
    content = build(stats)
    with open(README, encoding="utf-8") as f:
        readme = f.read()
    start = f"<!--START_SECTION:{SECTION}-->"
    end = f"<!--END_SECTION:{SECTION}-->"
    pattern = re.compile(re.escape(start) + r"[\s\S]+?" + re.escape(end))
    if not pattern.search(readme):
        sys.exit(f"Section markers for '{SECTION}' not found in {README}")
    block = f"{start}\n\n```{CODE_LANG}\n{content}\n```\n\n{end}"
    new = pattern.sub(lambda _: block, readme, count=1)
    if new == readme:
        print("No changes")
        return
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print("README updated")


if __name__ == "__main__":
    main()
