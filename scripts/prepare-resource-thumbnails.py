"""Create uncropped web thumbnails from the supplied cover images."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
source = Path(sys.argv[1])
files = [
    ("기독교인을위한차별금지법안내서_이미지-1024x685.jpg", "christian-guide"),
    ("극우리포트표지.png", "far-right-report"),
    ("차별금지법 권고 20년 학술대회 표지.png", "twenty-years"),
    ("광장에서 펼쳐보는 차별금지법 Q&A 표지.png", "square-qna"),
    ("차별금지평등법 제정을 위한 안내서 표지.jpg", "equality-promise"),
    ("평등정책 보고서 노동일의 세계 표지.jpg", "world-of-work"),
    ("백 개의 광장.png", "hundred-squares"),
    ("만개할 평등 .png", "equality-in-bloom"),
]
resources = json.loads((ROOT / "content/manuscript.json").read_text(encoding="utf-8"))["resources"]
assert len(resources) == len(files)
output = ROOT / "public/assets/images/resources"
output.mkdir(parents=True, exist_ok=True)
manifest = {}
for resource, (filename, slug) in zip(resources, files):
    with Image.open(source / filename) as original:
        img = ImageOps.exif_transpose(original).convert("RGB")
        img.thumbnail((800, 1000), Image.Resampling.LANCZOS)
        path = output / f"{slug}.webp"
        img.save(path, "WEBP", quality=85, method=6)
        manifest[resource["url"]] = {"src": f"/assets/images/resources/{slug}.webp", "width": img.width, "height": img.height}
        print(slug, img.size, path.stat().st_size)
(ROOT / "content/resource-thumbnails.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
