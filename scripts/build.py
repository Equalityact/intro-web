"""Render the approved manuscript; keep editorial copy in content/manuscript.json."""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "public"
OUT.mkdir(parents=True, exist_ok=True)
COPY = json.loads((ROOT / "content/manuscript.json").read_text(encoding="utf-8"))
PAGES = COPY["pages"]
HOME = COPY["home"]
LINKS = COPY["links"]
EXT = 'target="_blank" rel="noopener noreferrer"'
h = escape


def prose(tag, value, attrs=""):
    """Mark manuscript text so checks can detect unapproved editorial additions."""
    suffix = f' {attrs}' if attrs else ''
    return f'<{tag} data-manuscript{suffix}>{h(value)}</{tag}>'


def paragraphs(values, attrs=""):
    return "".join(prose("p", value, attrs) for value in values)


def emphasised_paragraph(value, phrase):
    before, match, after = value.partition(phrase)
    if not match:
        raise ValueError("Emphasis must match existing copy")
    return f'<p data-manuscript>{h(before)}<strong>{h(match)}</strong>{h(after)}</p>'


def external(url, label, classes=""):
    return f'<a href="{h(url)}" class="{classes}" {EXT}>{prose("span", label)} <span aria-hidden="true">↗</span></a>'


def grounds_html():
    return '<ul class="grounds">' + "".join(prose("li", value, 'class="ground"') for value in HOME["grounds"]) + "</ul>"


def linked_paragraphs(item):
    result = ""
    groups = item.get("paragraph_links", [[] for _ in item["paragraphs"]])
    for value, links in zip(item["paragraphs"], groups):
        cursor = 0
        fragments = []
        for link in links:
            start, end = link["start"], link["end"]
            if not cursor <= start < end <= len(value) or value[start:end] != link["text"]:
                raise ValueError("Timeline link range does not match its manuscript text")
            fragments.append(h(value[cursor:start]))
            fragments.append(f'<a data-manuscript-link href="{h(link["url"])}" {EXT}>{h(value[start:end])}</a>')
            cursor = end
        fragments.append(h(value[cursor:]))
        result += '<p data-manuscript>' + "".join(fragments) + '</p>'
    return result


def page_hero(filename, toc=()):
    _, number, short, title = next(page for page in PAGES if page[0] == filename)
    links = "".join(f'<li><a href="#{ident}">{prose("span", label)}</a></li>' for ident, label in toc)
    lead_html = prose("p", COPY["page_introductions"][filename], 'class="lead"')
    toc_attrs = ' data-timeline-toc' if filename == "timeline.html" else ""
    toc_html = f'<ul class="page-toc" aria-label="이 페이지의 내용"{toc_attrs}>{links}</ul>' if links else ""
    return f'''<section class="page-hero"><div class="wrap">
  <p class="eyebrow"><b aria-hidden="true">{number}</b>{prose("span", short)}</p>
  {prose("h1", title)}{lead_html}{toc_html}
</div></section>'''


def pager(filename):
    index = [page[0] for page in PAGES].index(filename)
    previous = PAGES[index - 1] if index else ("index.html", "", HOME["name"], HOME["name"])
    result = f'<a class="prev" href="{previous[0]}"><small>← 이전</small>{prose("strong", previous[2])}</a>'
    if index + 1 < len(PAGES):
        following = PAGES[index + 1]
        result += f'<a class="next" href="{following[0]}"><small>다음 →</small>{prose("strong", following[2])}</a>'
    return f'<nav class="wrap pager" aria-label="이전·다음 페이지">{result}</nav>'


def layout(filename, title, description, body):
    navigation = "".join(
        f'<li><a href="{name}"' + (' aria-current="page"' if name == filename else "") + f'>{prose("span", short)}</a></li>'
        for name, _, short, _ in PAGES
    )
    site_title = HOME["name"] if filename == "index.html" else f'{title} · {HOME["name"]}'
    timeline_script = '<script src="assets/js/timeline.js" defer></script>\n' if filename == "timeline.html" else ""
    section_menu = ""
    if filename == "index.html":
        section_links = "".join(f'<li><a href="#{ident}"><span aria-hidden="true">{index:02d}</span>{prose("span", label)}</a></li>' for index, (ident, label) in enumerate(HOME["section_navigation"], 1))
        section_menu = f'''<nav class="section-jump" aria-label="메인 페이지 섹션">
  <ol id="home-section-links">{section_links}</ol>
  <button class="btn purple small section-jump-toggle" type="button" aria-controls="home-section-links" aria-expanded="true" hidden>섹션 이동 <span aria-hidden="true">⌃</span></button>
</nav>'''
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h(site_title)}</title>
<meta name="description" content="{h(description)}">
<meta property="og:title" content="{h(site_title)}">
<meta property="og:description" content="{h(description)}">
<meta name="theme-color" content="#7056BE">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">본문으로 바로가기</a>
<header class="site-header"><div class="wrap">
  <a class="wordmark" href="index.html">{prose("span", HOME["wordmark"])}</a>
  <button class="menu-toggle" type="button" aria-controls="gnb" aria-expanded="false">메뉴 열기</button>
  <nav class="gnb" id="gnb" aria-label="주요 메뉴"><ul>{navigation}</ul></nav>
</div></header>
<main id="main">{body}</main>
{section_menu}
<footer class="site-footer"><div class="wrap"><div class="footer-grid">
  {prose("p", HOME["name"], 'class="footer-name"')}
  <dl class="footer-info">
    <dt>제작</dt><dd>{prose("span", "차별금지법제정연대")} · {external(LINKS["home"], "홈페이지")}</dd>
    <dt>SNS</dt><dd>{external(LINKS["facebook"], "페이스북")} · {external(LINKS["instagram"], "인스타그램")} · {external(LINKS["twitter"], "트위터")}</dd>
    <dt>이메일</dt><dd><a href="mailto:equalact2017@gmail.com">{prose("span", "equalact2017@gmail.com")}</a></dd>
    <dt>후원</dt><dd>{prose("span", "우리은행 1006‒201‒507617 차별금지법제정연대")}</dd>
  </dl>
</div></div></footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="assets/js/main.js" defer></script>
{timeline_script}</body>
</html>
'''


def areas_html():
    cards = ""
    for line in COPY["about"][3]["paragraphs"][1:]:
        match = re.fullmatch(r"(.+?) : (.+) \((.+)\)", line)
        name, description, area = match.groups()
        cards += f'<li>{prose("b", name)}{prose("span", description, "class=\"area-description\"")}{prose("span", area, "class=\"tag\"")}</li>'
    return f'<ul class="area-list visual">{cards}</ul>'


about_blocks = ""
for index, block in enumerate(COPY["about"], 1):
    if block["id"] == "grounds":
        values = block["paragraphs"]
        body = prose("p", values[0]) + grounds_html() + prose("p", values[-1])
    elif block["id"] == "areas":
        body = prose("p", block["paragraphs"][0]) + areas_html()
    else:
        body = paragraphs(block["paragraphs"])
    about_blocks += f'''<article class="block" id="{block["id"]}">
  <div class="block-head"><span class="num" aria-hidden="true">{index:02d}</span>{prose("h2", block["title"])}</div>
  <div class="block-body">{body}</div>
</article>'''
about_body = page_hero("about.html", toc=[(b["id"], b["title"]) for b in COPY["about"]])
about_body += f'<section class="section"><div class="wrap">{about_blocks}</div></section>' + pager("about.html")

scene_sections = ""
scene_tabs = ""
comparison = COPY["scene_comparison"]
for scene in COPY["scenes"]:
    sid = scene["id"]
    scene_tabs += f'<button type="button" id="tab-{sid}" role="tab" aria-controls="{sid}" aria-selected="false" tabindex="-1">{prose("span", scene["title"])}</button>'
    cards = ""
    if len(scene["items"]) != len(scene["before"]):
        raise ValueError("Each manuscript scene needs one comparison")
    for index, (after, before) in enumerate(zip(scene["items"], scene["before"]), 1):
        cards += f'''<article class="scene-comparison" aria-labelledby="compare-{sid}-{index}">
  <div class="comparison-grid"><div class="comparison-box">{prose("h4", comparison["before_label"])}{prose("p", before)}</div><span class="comparison-arrow" aria-hidden="true">→</span><div class="comparison-box after">{prose("h4", comparison["after_label"])}{prose("p", after, f'id="compare-{sid}-{index}"')}</div></div>
</article>'''
    scene_sections += f'<section class="scene-panel" id="{sid}" aria-labelledby="{sid}-title">{prose("h3", scene["title"], f'class="scene-area-title" id="{sid}-title"')}{cards}</section>'
scenes_body = page_hero("scenes.html", [(s["id"], s["title"]) for s in COPY["scenes"]])
scenes_body += f'''<section class="section" aria-labelledby="comparison-title"><div class="wrap">
{prose("p", comparison["label"], 'class="eyebrow"')}{prose("h2", comparison["title"], 'class="section-title comparison-title" id="comparison-title"')}
{prose("p", comparison["hint"], 'class="section-intro muted" id="scene-hint" hidden')}
<div class="scene-selector" role="tablist" aria-label="일상 장면 선택" aria-describedby="scene-hint" hidden>{scene_tabs}</div>
<div class="scene-panels">{scene_sections}</div>
</div></section>''' + pager("scenes.html")

survey_rows = []
for value, institution, date, url in HOME["surveys"]:
    number = value.removesuffix("%")
    survey_rows.append(f'''<div class="rate-row">
  <div class="rate-label">{external(url, institution)}{prose("strong", value)}</div>
  <div class="rate-track" aria-hidden="true"><div class="rate-fill" style="--value:{number}%"></div></div>
  <div class="scale" aria-hidden="true"><span>0%</span><span>100%</span></div>
  {prose("p", date, 'class="rate-source"')}
</div>''')


def survey_card(label):
    return f'<div class="survey">{prose("h3", label)}{"".join(survey_rows[:2])}<div class="survey-context">{survey_rows[2]}</div></div>'


surveys = survey_card(HOME["source_label"])
why_surveys = survey_card(COPY["why_source_label"])
dots = '<div class="dots" aria-hidden="true">' + "<span></span>" * 14 + "</div>"


def recommendation_card(include_title=True):
    number = f'<p class="big-number" data-manuscript>{h(HOME["recommendation_value"].removesuffix("차례"))}<small>차례</small></p>'
    title = prose("h3", HOME["recommendation_title"]) if include_title else ""
    caption = prose("p", HOME["recommendation_caption"], 'class="muted"')
    return f'<div class="recommendations">{number}{title}{caption}{dots}</div>'


why_sections = ""
for index, block in enumerate(COPY["why"]):
    title = prose("h2", block["title"], f'class="section-title" id="{block["id"]}-title"')
    body = f'<div class="reading">{paragraphs(block["paragraphs"])}</div>'
    if index == 0:
        citizen_paragraphs = emphasised_paragraph(block["paragraphs"][0], block["emphasis"]) + paragraphs(block["paragraphs"][1:])
        body = f'<div class="stat-hero"><div><p class="eyebrow"><b aria-hidden="true">01</b>{prose("span", block["label"])}</p>{title}<div class="reading">{citizen_paragraphs}</div></div>{why_surveys}</div>'
    elif index == 1:
        callout = f'<div class="callout purple visual">{prose("strong", block["callout"]["title"])}{prose("p", block["callout"]["body"])}</div>'
        body = f'''<div class="block"><div class="block-head"><p class="eyebrow"><b aria-hidden="true">02</b>{prose("span", block["label"])}</p>{title}</div>
<div class="block-body">{prose("p", block["paragraphs"][0])}{callout}{prose("p", block["paragraphs"][1])}<p><a class="text-link" href="qna.html#q1">{prose("span", block["question_link"])}</a></p></div></div>'''
    elif index == 2:
        closing = COPY["why_closing"]
        global_paragraphs = emphasised_paragraph(block["paragraphs"][0], block["emphasis"]) + paragraphs(block["paragraphs"][1:])
        body = f'''<div class="stat-hero editorial-columns"><div class="editorial-title"><p class="eyebrow"><b aria-hidden="true">03</b>{prose("span", block["label"])}</p><div class="editorial-content">{title}{recommendation_card(False)}</div></div>
<div class="reading">{global_paragraphs}<div class="callout section-content">{prose("p", closing["title"], 'class="callout-title"')}{prose("p", closing["body"])}</div></div></div>'''
    else:
        body = title + body
    why_sections += f'<section class="section{" soft" if index == 1 else ""}" id="{block["id"]}" aria-labelledby="{block["id"]}-title"><div class="wrap">{body}</div></section>'
why_body = page_hero("why.html", toc=[(b["id"], b["title"]) for b in COPY["why"]]) + why_sections + pager("why.html")


def qa_item(index, question, preview=True):
    summary = prose("span", question["summary"], 'class="q-preview"') if preview else ""
    return f'''<details class="qa" id="q{index}">
  <summary><span class="q-number" aria-hidden="true">Q{index}</span><span class="q-copy">{prose("span", question["question"], 'class="q-title"')}{summary}</span><span class="q-toggle" aria-hidden="true"></span></summary>
  <div class="q-detail"><p class="detail-label">자세한 답변</p>{prose("p", question["answer"])}</div>
</details>'''


question_list = "".join(qa_item(index, question) for index, question in enumerate(COPY["questions"], 1))
home_questions = "".join(qa_item(index, question, preview=False) for index, question in enumerate(COPY["questions"][:4], 1))
qna_body = page_hero("qna.html") + f'''<section class="section"><div class="wrap">
  <div class="faq-toolbar" hidden><div class="field"><label for="faq-search">질문 검색</label><input type="search" id="faq-search" aria-controls="faq-list" aria-describedby="faq-count"></div><button class="btn small" type="button" id="faq-expand" aria-controls="faq-list" aria-expanded="false">모두 펼치기 <span aria-hidden="true">+</span></button></div>
  <p class="faq-count" id="faq-count" role="status" aria-live="polite">질문 {len(COPY["questions"])}개</p>
  <div id="faq-list">{question_list}</div><p class="empty" id="faq-empty" hidden>검색 결과 없음</p>
</div></section>''' + pager("qna.html")

periods = ""
for index, period in enumerate(COPY["timeline"], 1):
    items = ""
    for item in period["items"]:
        meta = item.get("meta", {})
        metadata = "".join(prose("span", meta[key], f'class="timeline-{key}"') for key in ("date", "actor", "kind") if meta.get(key))
        prefix = f'{meta.get("actor", "")}({meta.get("date", "")}) - '
        title = item["title"].removeprefix(prefix) if meta.get("actor") and meta.get("date") else item["title"]
        items += f'<li class="timeline-item"><article class="timeline-card"><div class="timeline-meta">{metadata}</div>{prose("h3", title)}{linked_paragraphs(item)}</article></li>'
    years = prose("span", period["years"], 'class="years"') if period.get("years") else ""
    periods += f'<section class="period" id="{period["id"]}" aria-labelledby="{period["id"]}-title"><div class="period-head"><span class="period-number" aria-hidden="true">{index:02d}</span>{prose("h2", period["title"], f'id="{period["id"]}-title"')}{years}</div><ol class="timeline">{items}</ol></section>'
timeline_body = page_hero("timeline.html", toc=[(p["id"], p["title"]) for p in COPY["timeline"]])
timeline_body += f'<section class="section"><div class="wrap"><div class="timeline-periods" data-timeline>{periods}</div></div></section>' + pager("timeline.html")

def resource_button(item):
    return f'<a class="btn purple small" href="{h(item["url"])}" {EXT}>자료 보기 <span aria-hidden="true">↗</span></a>'


resource_items = "".join(f'<li class="resource">{prose("h2", item["title"])}{prose("p", item["by"], "class=\"by\"")}{paragraphs(item["paragraphs"])}{resource_button(item)}</li>' for item in COPY["resources"])
resources_body = page_hero("resources.html", [("library", "더 보기"), ("info", "정보")])
resources_body += f'''<section class="section" id="library"><div class="wrap"><ul class="resource-list">{resource_items}</ul></div></section>
<section class="section soft" id="info" aria-labelledby="info-title"><div class="wrap">{prose("h2", "정보", 'class="section-title" id="info-title"')}
<table class="info-table"><tbody>
  <tr><th scope="row">제작</th><td>{prose("span", "차별금지법제정연대")}</td></tr>
  <tr><th scope="row">홈페이지</th><td><div class="info-links">{external(LINKS["home"], "equalityact.kr", "info-link")}</div></td></tr>
  <tr><th scope="row">후원 계좌</th><td>{prose("p", "우리은행 1006‒201‒507617 차별금지법제정연대", 'class="info-account"')}<div class="info-links">{external(LINKS["donate"], "후원하기", "info-link")}</div></td></tr>
  <tr><th scope="row">SNS</th><td><div class="info-links">{external(LINKS["facebook"], "페이스북 @equalact2017", "info-link")}{external(LINKS["instagram"], "인스타그램 @equalityact_allpeople", "info-link")}{external(LINKS["twitter"], "트위터 @equalact", "info-link")}</div></td></tr>
  <tr><th scope="row">이메일</th><td><div class="info-links"><a class="info-link" href="mailto:equalact2017@gmail.com">{prose("span", "equalact2017@gmail.com")}</a></div></td></tr>
  <tr><th scope="row">뉴스레터 구독하기</th><td><div class="info-links">{external(LINKS["newsletter"], HOME["newsletter_button"], "info-link")}</div></td></tr>
</tbody></table></div></section>''' + pager("resources.html")

pillars = "".join(f'<article class="pillar"><div class="role" aria-hidden="true">{index:02d}</div>{prose("h3", title)}{prose("p", body)}</article>' for index, (title, body) in enumerate(HOME["pillars"], 1))
scene_cards = "".join(f'<a class="scene-card" href="scenes.html#{scene["id"]}"><div class="scene-top"><span class="scene-index" aria-hidden="true">{index:02d}</span><span class="scene-glyph" aria-hidden="true">{glyph}</span></div>{prose("h3", scene["title"])}<span class="scene-link">더 알아보기 <span class="arrow" aria-hidden="true">→</span></span></a>' for index, (scene, glyph) in enumerate(zip(COPY["scenes"], ["[ ]", "?", "↔", "="]), 1))
index_body = f'''<section class="hero" aria-labelledby="hero-title"><div class="wrap hero-grid"><div>
  <h1 id="hero-title" data-manuscript><span class="hero-title-line">차별금지법,</span><span class="hero-title-line">모두를 위한</span><span class="hero-title-line"><mark>평등의 기준</mark></span></h1>
  {prose("p", HOME["description"], 'class="hero-lead"')}
  <div class="actions"><a class="btn purple" href="about.html">알아보기 <span class="arrow" aria-hidden="true">→</span></a><a class="btn on-dark" href="qna.html">질문 살펴보기 <span class="arrow" aria-hidden="true">→</span></a></div>
</div><div class="shape-panel"><span class="eq" aria-hidden="true">=</span>{prose("p", HOME["grounds_title"], 'class="shape-caption"')}</div></div></section>
<section class="section" aria-labelledby="summary-title"><div class="wrap">{prose("h2", HOME["summary_title"], 'class="section-title" id="summary-title"')}<div class="pillars">{pillars}</div></div></section>
<section class="section soft" aria-labelledby="grounds-title"><div class="wrap">{prose("h2", HOME["grounds_title"], 'class="section-title" id="grounds-title"')}{prose("p", HOME["grounds_intro"], 'class="section-intro"')}{grounds_html()}<div class="section-foot"><a class="text-link" href="about.html#grounds">더 알아보기 →</a></div></div></section>
<section class="section" aria-labelledby="scenes-title"><div class="wrap">{prose("h2", PAGES[1][3], 'class="section-title" id="scenes-title"')}<div class="scene-grid">{scene_cards}</div><div class="section-foot"><a class="text-link" href="scenes.html">더 알아보기 →</a></div></div></section>
<section class="section soft" aria-labelledby="stats-title"><div class="wrap">{prose("h2", HOME["stats_title"], 'class="section-title" id="stats-title"')}
<div class="stat-hero stats-summary section-content"><div>{prose("p", HOME["support_value"], 'class="big-number range"')}{prose("h3", HOME["support_title"], 'class="callout-title"')}{prose("p", HOME["support_caption"], 'class="caption"')}{recommendation_card()}</div>{surveys}</div>
<div class="section-foot"><a class="text-link" href="why.html">더 알아보기 →</a></div></div></section>
<section class="section" aria-labelledby="qa-title"><div class="wrap">{prose("h2", HOME["questions_title"], 'class="section-title" id="qa-title"')}<div class="qa-list-simple section-content">{home_questions}</div><div class="section-foot"><a class="btn purple" href="qna.html">더 알아보기 <span class="arrow" aria-hidden="true">→</span></a></div></div></section>
<section class="section pink-soft" id="join" aria-labelledby="join-title"><div class="wrap">{prose("h2", HOME["join_title"], 'class="section-title" id="join-title"')}<div class="join">
<article class="join-path">{prose("p", HOME["share"])}<div class="actions"><button class="btn small" type="button" data-share hidden>사이트 링크 공유</button>{external(LINKS["leaflet"], HOME["leaflet"], "btn purple small")}</div></article>
<article class="join-path">{prose("p", HOME["newsletter_question"])}{prose("p", HOME["newsletter"])}<div class="actions">{external(LINKS["newsletter"], HOME["newsletter_button"], "btn purple small")}</div></article>
<article class="join-path">{prose("p", HOME["donate"])}<div class="actions">{external(LINKS["donate"], "후원하기", "btn purple small")}</div></article>
</div></div></section>'''

PAGE_LINK = re.compile(r'href="(index|' + "|".join(name[:-5] for name, *_ in PAGES) + r')\.html(#[^"]*)?"')


def clean_urls(html):
    html = PAGE_LINK.sub(lambda match: f'href="{"/" if match[1] == "index" else "/" + match[1]}{match[2] or ""}"', html)
    return html.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')


bodies = [about_body, scenes_body, why_body, qna_body, timeline_body, resources_body]
pages = [("index.html", HOME["name"], HOME["description"], index_body)]
pages += [(name, title, title, body) for (name, _, _, title), body in zip(PAGES, bodies)]
for filename, title, description, body in pages:
    (OUT / filename).write_text(clean_urls(layout(filename, title, description, body)), encoding="utf-8")
    print("wrote", filename)
