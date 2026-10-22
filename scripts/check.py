"""Check generated output and local navigation without third-party dependencies."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
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
        self.errors = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags[tag] += 1
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

    pages = {path.resolve(): Page(path) for path in PUBLIC.glob("*.html")}
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
    print(f"PASS: {len(pages)} generated pages match; {links} local links/assets and all ID references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
