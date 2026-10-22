"""Check generated output and local navigation without third-party dependencies."""
from collections import Counter
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = Counter()
        self.tags = Counter()
        self.links = []
        self.references = []
        self.manuscript_links = []
        self.errors = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags[tag] += 1
        if tag == "a" and "data-manuscript-link" in attrs:
            self.manuscript_links.append(attrs.get("href"))
        if "id" in attrs:
            self.ids[attrs["id"]] += 1
        for name in ("href", "src"):
            if name in attrs:
                self.links.append(attrs[name])
        for name in ("aria-controls", "aria-labelledby", "aria-describedby", "for"):
            self.references.extend(attrs.get(name, "").split())
        if tag == "a" and attrs.get("target") == "_blank":
            if not {"noopener", "noreferrer"} <= set(attrs.get("rel", "").split()):
                self.errors.append("external new-tab link is missing rel protections")
        if tag == "a" and attrs.get("href") in ("", "#"):
            self.errors.append("placeholder link has no destination")


def normalise(value):
    return re.sub(r"\s+", "", unescape(value))


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


class ManuscriptAudit(HTMLParser):
    """Check all manuscript blocks and all remaining Korean body text."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    UI = {normalise(value) for value in [
        "본문으로 바로가기", "메뉴 열기", "메뉴 닫기", "← 이전", "다음 →",
        "질문 검색", "모두 펼치기", "모두 접기", "검색 결과 없음", "자세한 답변",
        "자료 보기", "알아보기", "질문 살펴보기", "더 알아보기", "더 알아보기 →", "사이트 링크 공유",
    ]}

    def __init__(self, html, corpus):
        super().__init__(convert_charrefs=True)
        self.corpus = corpus
        self.stack = []
        self.errors = []
        self.count = 0
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        parent = self.stack[-1] if self.stack else {}
        context = {
            "tag": tag,
            "body": parent.get("body", False) or tag == "body",
            "ignore": parent.get("ignore", False) or attrs.get("aria-hidden") == "true" or tag in ("script", "style"),
            "copy": [] if "data-manuscript" in attrs else None,
        }
        if tag not in self.VOID:
            self.stack.append(context)
        if tag == "meta" and attrs.get("name", attrs.get("property")) in ("description", "og:description"):
            self.check(attrs.get("content", ""))

    def handle_data(self, value):
        if not self.stack or not self.stack[-1]["body"] or self.stack[-1]["ignore"]:
            return
        copies = [context for context in self.stack if context["copy"] is not None]
        if copies:
            for context in copies:
                context["copy"].append(value)
        elif re.search(r"[가-힣]", value):
            value = normalise(value)
            if value not in self.UI and not re.fullmatch(r"질문[0-9]+개", value):
                self.check(value)

    def check(self, value):
        value = normalise(value)
        if value and value not in self.corpus:
            self.errors.append(f"copy absent from approved manuscript: {value[:120]}")

    def handle_endtag(self, tag):
        match = next((index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index]["tag"] == tag), None)
        if match is None:
            return
        for context in self.stack[match:]:
            if context["copy"] is not None:
                self.count += 1
                self.check("".join(context["copy"]))
        del self.stack[match:]


def local_path(url, source):
    path = unquote(urlsplit(url).path)
    if not path:
        return source
    target = PUBLIC / path.lstrip("/") if path.startswith("/") else source.parent / path
    if target.is_dir():
        target /= "index.html"
    elif not target.suffix:
        target = target.with_suffix(".html")
    return target.resolve()


def main():
    errors = []
    with tempfile.TemporaryDirectory(prefix="intro-web-check-") as output:
        subprocess.run([sys.executable, str(ROOT / "scripts/build.py"), output], check=True, capture_output=True, text=True)
        generated = {path.name: path for path in Path(output).glob("*.html")}
        checked_in = {path.name: path for path in PUBLIC.glob("*.html")}
        if generated.keys() != checked_in.keys():
            errors.append("generated/public page membership differs; remove stale output or regenerate")
        for name in generated.keys() & checked_in.keys():
            if generated[name].read_bytes() != checked_in[name].read_bytes():
                errors.append(f"{name}: stale output; run npm run generate")

    manuscript = json.loads((ROOT / "content/manuscript.json").read_text())
    original_details = normalise((ROOT / "content/details.txt").read_text())
    # Detailed headings and prose must remain verbatim from the uploaded source.
    for section in ("about", "scenes", "why", "timeline", "resources"):
        for block in manuscript[section]:
            values = [block["title"]]
            if "paragraphs" in block:
                values.extend(block["paragraphs"])
            for item in block.get("items", []):
                values.extend([item] if isinstance(item, str) else [item["title"], *item["paragraphs"]])
            for value in values:
                if normalise(value) not in original_details:
                    errors.append(f"{section}: approved detail differs from original source: {value[:60]}")
    for question in manuscript["questions"]:
        for key in ("question", "answer"):
            if normalise(question[key]) not in original_details:
                errors.append(f"question {key} differs from original source")
    corpus = original_details + "\n" + "\n".join(normalise(value) for value in strings(manuscript))
    copy_blocks = 0
    for path in PUBLIC.glob("*.html"):
        audit = ManuscriptAudit(path.read_text(), corpus)
        copy_blocks += audit.count
        errors.extend(f"{path.name}: {message}" for message in audit.errors)
    pages = {path.resolve(): Page(path) for path in PUBLIC.glob("*.html")}
    supplied_links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', (ROOT / "content/timeline-links.md").read_text())
    if pages[(PUBLIC / "timeline.html").resolve()].manuscript_links != supplied_links:
        errors.append("timeline.html: supplied links or their order differ from source, including bracket links")
    links = 0
    for path, page in pages.items():
        errors.extend(f"{path.name}: {message}" for message in page.errors)
        for tag in ("h1", "main"):
            if page.tags[tag] != 1:
                errors.append(f"{path.name}: expected exactly one {tag}")
        for ident, count in page.ids.items():
            if count != 1:
                errors.append(f"{path.name}: duplicate id {ident}")
        for ident in page.references:
            if ident not in page.ids:
                errors.append(f"{path.name}: missing labelled/controlled element {ident}")
        for url in page.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            links += 1
            target = local_path(url, path)
            if not target.is_relative_to(PUBLIC):
                errors.append(f"{path.name}: local URL escapes public/: {url}")
            elif not target.is_file():
                errors.append(f"{path.name}: missing local destination {url}")
            elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f"{path.name}: missing fragment {url}")

    for css in PUBLIC.rglob("*.css"):
        for url in re.findall(r'url\([\'"]?([^\)\'"\s]+)[\'"]?\)', css.read_text()):
            if not urlsplit(url).scheme and not local_path(url, css).is_file():
                errors.append(f"{css.name}: missing CSS asset {url}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(pages)} generated pages match; {links} local links/assets and all ID references resolve; {copy_blocks} manuscript blocks and {len(supplied_links)} supplied timeline links audited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
