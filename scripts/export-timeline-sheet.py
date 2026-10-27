"""Create a Google Sheets import file without changing the approved timeline."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def export_timeline():
    copy = json.loads((ROOT / "content/manuscript.json").read_text())
    target = ROOT / "content/timeline-sheet.csv"
    with target.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["시기", "분류", "제목", "본문", "공개"])
        for period in copy["timeline"]:
            for item in period["items"]:
                paragraphs = []
                groups = item.get("paragraph_links", [[] for _ in item["paragraphs"]])
                for text, links in zip(item["paragraphs"], groups):
                    cursor = 0
                    parts = []
                    for link in links:
                        start, end = link["start"], link["end"]
                        if text[start:end] != link["text"] or start < cursor:
                            raise ValueError("Link does not match timeline text")
                        parts.extend([text[cursor:start], f'[{link["text"]}]({link["url"]})'])
                        cursor = end
                    parts.append(text[cursor:])
                    paragraphs.append("".join(parts))
                writer.writerow([period["title"], item.get("meta", {}).get("kind", ""), item["title"], "\n\n".join(paragraphs), "예"])
    print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    export_timeline()
