"""Rebuild the live parts of the Amit Bhakt GitHub profile README.

Runs locally or in GitHub Actions (see .github/workflows/build.yml).
Standard library only: no external dependencies required.

Updates:
1. assets/voice-pipeline.svg (Sleek dark mode real-time Voice AI pipeline architecture diagram)
2. README.md (filtered pull requests list)
3. contributions.md (categorized PR and contribution log)
"""

from __future__ import annotations

import html
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

ROOT = pathlib.Path(__file__).parent.resolve()
README = ROOT / "README.md"
CONTRIBUTIONS = ROOT / "contributions.md"
ASSETS = ROOT / "assets"

USER = "amitbhakt"

# Fallback or explicit token from environment or gh CLI
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    try:
        TOKEN = subprocess.check_output(["gh", "auth", "token"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        TOKEN = None


def fetch(url: str, *, data: bytes | None = None, accept: str = "application/json") -> bytes:
    """Fetch URL with sensible headers and token authorization if available."""
    headers = {
        "User-Agent": "amitbhakt-profile-builder/1.0",
        "Accept": accept,
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        return res.read()


def get_json(url: str):
    """Fetch and parse JSON from a URL."""
    try:
        raw = fetch(url)
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        print(f"Warning: Failed to fetch JSON from {url}: {e}", file=sys.stderr)
        return None


def short_date(iso: str) -> str:
    """Format YYYY-MM-DD to 'Mon YYYY'."""
    if not iso or len(iso) < 7:
        return ""
    try:
        return datetime.strptime(iso[:7], "%Y-%m").strftime("%b %Y")
    except Exception:
        return iso


def md_escape(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]").replace("|", "\\|")


def replace_chunk(content: str, marker: str, chunk: str, inline: bool = False) -> str:
    """Replace content between <!-- marker starts --> and <!-- marker ends -->."""
    start_tag = f"<!-- {marker} starts -->"
    end_tag = f"<!-- {marker} ends -->"
    pat = re.escape(start_tag) + r".*?" + re.escape(end_tag)
    replacement = f"{start_tag}{chunk}{end_tag}" if inline else f"{start_tag}\n{chunk.rstrip()}\n{end_tag}"
    new_content, count = re.subn(pat, replacement, content, flags=re.DOTALL)
    return new_content


def all_prs_filtered() -> list[dict]:
    """Fetch all authored PRs. Keep all open/merged for other repos, but strictly ONLY merged for Dograh."""
    q = f"is:pr author:{USER} -user:{USER}"
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": q, "per_page": 50})
    data = get_json(url)
    if not data or "items" not in data:
        return []

    prs = []
    for it in data["items"]:
        repo = it["repository_url"].removeprefix("https://api.github.com/repos/")
        pull = it.get("pull_request") or {}
        merged_at = pull.get("merged_at")
        state = "merged" if merged_at else it["state"]
        date_str = (merged_at or it.get("closed_at") or it.get("created_at"))[:10]

        # Dograh rule: ONLY merged PRs
        if "dograh" in repo.lower():
            if state != "merged":
                continue

        prs.append({
            "repo": repo,
            "number": it["number"],
            "title": it["title"].strip(),
            "url": it["html_url"],
            "state": state,
            "date": date_str,
        })

    # Sort open first, then by date descending
    prs.sort(key=lambda p: (p["state"] == "open", p["date"]), reverse=True)
    return prs


def prs_md(prs: list[dict]) -> str:
    """Format PR list as a clean, easy-to-read markdown table."""
    if not prs:
        return "_No pull requests to display._"
    lines = [
        "| Project | Contribution | Status | Date |",
        "|:---|:---|:---:|:---:|",
    ]
    for p in prs:
        title = md_escape(p["title"])
        repo = p["repo"]
        repo_link = f"[{repo}](https://github.com/{repo})"
        pr_link = f"[{title}]({p['url']})"
        badge = "🟣 Merged" if p["state"] == "merged" else ("🟢 Open" if p["state"] == "open" else "Closed")
        date_str = short_date(p["date"])
        lines.append(f"| {repo_link} | {pr_link} | {badge} | {date_str} |")
    return "\n".join(lines)


def voice_pipeline_svg() -> str:
    """Generate subtle, sleek horizontal SVG diagram of real-time voice pipeline (dark mode)."""
    width, height = 860, 150
    y = 75

    stages = [
        ("INGRESS", "WhatsApp WebRTC (SRTP)", 110),
        ("DETECTION", "VAD &amp; Turn-Taking", 320),
        ("PIPELINE", "Pipecat / LiveKit", 530),
        ("SYNTHESIS", "Low-Latency TTS", 740),
    ]

    nodes = []
    for label, sub, x in stages:
        nodes.append(f"""
        <g>
          <circle cx="{x}" cy="{y}" r="5" fill="#38bdf8"/>
          <circle cx="{x}" cy="{y}" r="11" fill="none" stroke="#38bdf8" stroke-width="1.2" opacity="0.5">
            <animate attributeName="r" values="7;16;7" dur="3.5s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.7;0;0.7" dur="3.5s" repeatCount="indefinite"/>
          </circle>
          <text class="stage-tag" x="{x}" y="{y - 20}" text-anchor="middle">{label}</text>
          <text class="stage-sub" x="{x}" y="{y + 26}" text-anchor="middle">{sub}</text>
        </g>
        """)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Real-Time Voice AI Pipeline Architecture">
<defs>
  <clipPath id="card-clip"><rect width="{width}" height="{height}" rx="10"/></clipPath>
  <linearGradient id="line-grad" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>
    <stop offset="50%" stop-color="#818cf8" stop-opacity="0.95"/>
    <stop offset="100%" stop-color="#34d399" stop-opacity="0.8"/>
  </linearGradient>
  <radialGradient id="pulse-glow" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0%" stop-color="#38bdf8" stop-opacity="1"/>
    <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
  </radialGradient>
</defs>
<style>
  .stage-tag {{ font: 700 11px ui-monospace, SFMono-Regular, Menlo, monospace; fill: #38bdf8; letter-spacing: 1.5px; }}
  .stage-sub {{ font: 500 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; fill: #f0f6fc; }}
  .wire {{ stroke: url(#line-grad); stroke-width: 2; fill: none; }}
  .meta {{ font: 600 10px ui-monospace, SFMono-Regular, Menlo, monospace; fill: #8b949e; letter-spacing: 1px; }}
</style>
<g clip-path="url(#card-clip)">
  <rect width="{width}" height="{height}" fill="#0d1117" stroke="#30363d" stroke-width="1.5" rx="10"/>
  
  <text class="meta" x="30" y="28">REAL-TIME VOICE PIPELINE ARCHITECTURE</text>
  <text class="meta" x="{width - 30}" y="28" text-anchor="end">SUB-SECOND LATENCY &lt;450ms</text>
  <line x1="30" x2="{width - 30}" y1="36" y2="36" stroke="#21262d" stroke-width="1" stroke-dasharray="3 3"/>

  <!-- Pipeline Wire -->
  <line class="wire" x1="110" x2="740" y1="{y}" y2="{y}"/>

  <!-- Traveling Pulse -->
  <g>
    <animateTransform attributeName="transform" type="translate" from="0 0" to="630 0" dur="3.5s" repeatCount="indefinite"/>
    <circle cx="110" cy="{y}" r="14" fill="url(#pulse-glow)"/>
    <circle cx="110" cy="{y}" r="3.5" fill="#ffffff"/>
  </g>

  <!-- Nodes -->
  {''.join(nodes)}
</g>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="none" stroke="#30363d"/>
</svg>
"""


def contributions_page(prs: list[dict]) -> str:
    """Generate contributions.md page listing all pull requests."""
    by_repo: dict[str, list[dict]] = {}
    for p in prs:
        by_repo.setdefault(p["repo"], []).append(p)

    sections = []
    for repo, r_prs in sorted(by_repo.items(), key=lambda item: len(item[1]), reverse=True):
        entries = []
        for p in r_prs:
            badge = "🟣 Merged" if p["state"] == "merged" else ("🟢 Open" if p["state"] == "open" else "Closed")
            entries.append(f"- **[{md_escape(p['title'])}]({p['url']})** (#{p['number']}) — _{badge}, {p['date']}_")
        sections.append(f"### [{repo}](https://github.com/{repo})\n\n" + "\n".join(entries))

    return (
        "# Open Source Pull Requests & Contributions\n\n"
        f"A log of pull requests authored by [@{USER}](https://github.com/{USER}).\n\n"
        + "\n\n".join(sections)
        + "\n\n---\n<sub>Automatically generated by `build_readme.py`.</sub>\n"
    )


def main() -> None:
    print(f"--> Rebuilding profile for @{USER}...")
    ASSETS.mkdir(parents=True, exist_ok=True)

    # 1. Generate Voice Pipeline SVG
    print("--> Generating assets/voice-pipeline.svg...")
    (ASSETS / "voice-pipeline.svg").write_text(voice_pipeline_svg(), encoding="utf-8")

    # 2. Fetch Filtered PRs (All PRs with status, Dograh ONLY merged)
    print("--> Fetching filtered PRs...")
    prs = all_prs_filtered()
    print(f"    Found {len(prs)} qualified PRs.")

    # 3. Write contributions.md
    print("--> Writing contributions.md...")
    CONTRIBUTIONS.write_text(contributions_page(prs), encoding="utf-8")

    # 4. Update README.md
    if README.exists():
        print("--> Updating README.md dynamic sections...")
        content = README.read_text(encoding="utf-8")
        content = replace_chunk(content, "prs", prs_md(prs))
        README.write_text(content, encoding="utf-8")
        print("--> README.md successfully updated!")
    else:
        print("Warning: README.md does not exist yet. Please write template first.", file=sys.stderr)

    print("--> Done!")


if __name__ == "__main__":
    main()
