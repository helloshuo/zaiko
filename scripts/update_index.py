#!/usr/bin/env python3
"""Refresh the dated Markdown links on the repository homepage."""

from datetime import datetime
from pathlib import Path
import re
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- DAILY_INDEX_START -->"
END = "<!-- DAILY_INDEX_END -->"
YEAR_NAME = re.compile(r"[0-9]{4}\Z")
DAY_NAME = re.compile(r"([0-9]{8})\.md\Z")


def daily_files(year_dir: Path) -> list[tuple[str, str]]:
    result = []
    for path in year_dir.iterdir():
        if not path.is_file():
            continue
        match = DAY_NAME.fullmatch(path.name)
        if not match:
            continue
        date_text = match.group(1)
        try:
            date = datetime.strptime(date_text, "%Y%m%d")
        except ValueError:
            continue
        if date.year != int(year_dir.name):
            continue
        result.append((date.strftime("%Y-%m-%d"), f"{year_dir.name}/{path.name}"))
    return sorted(result, reverse=True)


def links(records: list[tuple[str, str]]) -> str:
    if not records:
        return "暂无日报。"
    return "\n".join(f"- [{day}]({path})" for day, path in records)


def index_text(now_year: int) -> str:
    years = {
        int(path.name): daily_files(path)
        for path in ROOT.iterdir()
        if path.is_dir() and YEAR_NAME.fullmatch(path.name)
    }
    lines = [f"## {now_year} 年 · 当年日报", "", links(years.get(now_year, []))]

    future_years = sorted((y for y in years if y > now_year), reverse=True)
    if future_years:
        lines.extend(["", "## 以后年份", ""])
        for year in future_years:
            lines.extend([f"### {year} 年", "", links(years[year]), ""])

    older_years = sorted((y for y in years if y < now_year), reverse=True)
    if older_years:
        lines.extend(["", "## 往年归档", ""])
        for year in older_years:
            lines.extend([
                "<details>",
                f"<summary>{year} 年（{len(years[year])} 天，点击展开）</summary>",
                "",
                links(years[year]),
                "",
                "</details>",
                "",
            ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    readme = ROOT / "README.md"
    current = readme.read_text(encoding="utf-8")
    if current.count(START) != 1 or current.count(END) != 1:
        raise ValueError("README.md 必须各有一个日报索引起止标记")
    before, rest = current.split(START, 1)
    _, after = rest.split(END, 1)
    now_year = datetime.now(ZoneInfo("Asia/Tokyo")).year
    updated = before + START + "\n" + index_text(now_year) + END + after
    if updated != current:
        readme.write_text(updated, encoding="utf-8")
        print("Updated README.md")
    else:
        print("README.md is current")


if __name__ == "__main__":
    main()
