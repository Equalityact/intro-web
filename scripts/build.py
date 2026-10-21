"""차별금지법 사이트 페이지 생성기.

원고(문구)는 이 파일 안에서 고치고 `npm run generate`로 public/ 의 HTML을 다시 만듭니다.
출력은 빌드 없이 그대로 열람 가능한 정적 HTML입니다.
"""
import re
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "public"

PAGES = [
    ("about.html", "01", "차별금지법이란?", "차별금지법이 뭐야?"),
    ("scenes.html", "02", "일상의 변화", "차별금지법이 바꿀 우리 사회의 장면들"),
    ("why.html", "03", "필요한 이유", "차별금지법이 제정될 수밖에 없는 이유"),
    ("qna.html", "04", "Q&A", "차별금지법에 관한 질문들"),
    ("timeline.html", "05", "타임라인", "차별금지법 타임라인"),
    ("resources.html", "06", "자료", "더 보기"),
]

LINKS = {
    "home": "https://equalityact.kr/",
    "donate": "https://equalityact.kr/cms/",
    "leaflet": "https://forms.gle/xWYDviRJrtsjUtcMA",
    "newsletter": "https://equalityact.stibee.com/",
    "facebook": "https://www.facebook.com/equalact2017",
    "instagram": "https://www.instagram.com/equalityact_allpeople",
    "twitter": "https://twitter.com/equalact",
}
EXT = 'target="_blank" rel="noopener noreferrer"'

GROUNDS = ["성별", "장애", "질병", "나이", "출신국가", "출신민족", "인종", "피부색", "출신지역",
           "용모·유전정보 등 신체조건", "혼인여부", "임신·출산", "가족형태 및 가족상황", "종교",
           "사상 또는 정치적 의견", "형이 만료된 전과", "성적지향", "성별정체성", "학력", "고용형태",
           "사회적 신분 등"]


def grounds_html():
    tags = "".join(f'<li class="ground">{g}</li>' for g in GROUNDS)
    return (f'<ul class="grounds" aria-label="차별금지사유 {len(GROUNDS)}가지" style="list-style:none;margin:0">{tags}</ul>'
            '<div class="all-of-us">나도, 당신도, 우리 모두</div>')


def layout(filename, title, description, body):
    nav = "".join(
        f'<li><a href="{f}"{" aria-current=\"page\"" if f == filename else ""}>{short}</a></li>'
        for f, _, short, _ in PAGES)
    full_title = "차별금지법" if filename == "index.html" else f"{title} · 차별금지법"
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{full_title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{full_title}">
<meta property="og:description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hahmlet:wght@500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">본문으로 바로가기</a>
<header class="site-header">
  <div class="wrap">
    <a class="wordmark" href="index.html">차별금지법이 뭐예요?</a>
    <button class="menu-toggle" type="button" aria-controls="gnb" aria-expanded="false">메뉴 열기</button>
    <nav class="gnb" id="gnb" aria-label="주요 메뉴"><ul>{nav}</ul></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <p class="footer-name">차별금지법<small>평등을 위한 최소한의 약속</small></p>
      <dl class="footer-info">
        <dt>제작</dt><dd>차별금지법제정연대 · <a href="{LINKS['home']}" {EXT}>홈페이지</a></dd>
        <dt>SNS</dt><dd><a href="{LINKS['facebook']}" {EXT}>페이스북</a> · <a href="{LINKS['instagram']}" {EXT}>인스타그램</a> · <a href="{LINKS['twitter']}" {EXT}>트위터</a></dd>
        <dt>이메일</dt><dd><a href="mailto:equalact2017@gmail.com">equalact2017@gmail.com</a></dd>
        <dt>후원</dt><dd>우리은행 1006‒201‒507617 차별금지법제정연대</dd>
      </dl>
    </div>
    <p class="footer-bottom">© 차별금지법제정연대 · 디자인 초안</p>
  </div>
</footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="assets/js/main.js" defer></script>
</body>
</html>
"""


def page_hero(num, short, title, lead, toc=None):
    toc_html = ""
    if toc:
        items = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc)
        toc_html = f'<ul class="page-toc" aria-label="이 페이지의 내용">{items}</ul>'
    tone = {"01": "pink", "02": "yellow", "03": "purple", "04": "pink", "05": "yellow", "06": "purple"}[num]
    return f"""<section class="page-hero tone-{tone}">
  <div class="wrap">
    <p class="eyebrow"><b>{num}</b>{short}</p>
    <h1>{title}</h1>
    <p class="lead">{lead}</p>
    {toc_html}
  </div>
</section>"""


def pager(filename):
    idx = [p[0] for p in PAGES].index(filename)
    prev_html = next_html = ""
    if idx > 0:
        f, n, s, _ = PAGES[idx - 1]
        prev_html = f'<a class="prev" href="{f}"><small>← 이전 {n}</small><strong>{s}</strong></a>'
    else:
        prev_html = '<a class="prev" href="index.html"><small>← 처음으로</small><strong>차별금지법 한눈에 보기</strong></a>'
    if idx < len(PAGES) - 1:
        f, n, s, _ = PAGES[idx + 1]
        next_html = f'<a class="next" href="{f}"><small>다음 {n} →</small><strong>{s}</strong></a>'
    return f'<nav class="wrap pager" aria-label="이전·다음 페이지">{prev_html}{next_html}</nav>'


def blocks(items):
    out = []
    for i, (bid, title, body) in enumerate(items, 1):
        out.append(f"""<article class="block" id="{bid}">
  <div class="block-head"><span class="num">{i:02d}</span><h2>{title}</h2></div>
  <div class="block-body">{body}</div>
</article>""")
    return "\n".join(out)


# ---------------------------------------------------------------- 01 about
AREAS = [
    ("일할 때", "채용, 배치, 승진, 퇴직 등", "고용 영역"),
    ("배울 때", "학교, 교육시설, 직업훈련기관 등", "교육 영역"),
    ("물건을 사거나 서비스를 이용할 때", "병원, 은행, 식당, 카페 등", "재화·용역 영역"),
    ("행정 서비스를 이용할 때", "주민센터, 법원, 경찰서, 투표소 등", "행정서비스 영역"),
]
areas_html = '<ul class="area-list visual">' + "".join(
    f'<li><b>{a}</b><span>{d}</span><span class="tag">{t}</span></li>' for a, d, t in AREAS) + "</ul>"

about_body = page_hero(
    "01", "차별금지법이란?", "차별금지법이 뭐야?",
    "차별금지법은 모든 사람이 존엄한 대우를 받을 수 있도록 평등의 기준을 세우는 법이에요. 여섯 가지 문장으로 차근차근 살펴봐요.",
    [("standard", "평등의 기준"), ("courage", "용기를 돕는 법"), ("grounds", "차별금지사유"),
     ("areas", "차별금지영역"), ("state", "국가의 책임"), ("start", "시작해요")]
) + '<section class="section"><div class="wrap">' + blocks([
    ("standard", "평등의 기준을<br>세우는 법!",
     "<p>차별은 ‘나쁜 사람’만 하는 행동이 아닙니다. 어쩔 수 없이 겪어야 하는 일도 아니고요. 소수자를 약자의 자리로 내몰고 편견과 혐오를 방치하는 사회의 구조가 차별을 만듭니다.</p>"
     "<p>그래서 차별이 무엇인지 정하고, 차별을 포괄적으로 막고 예방하는 법이 필요해요. 차별금지법은 <strong>모든 사람이 존엄한 대우를 받을 수 있도록 평등의 기준을 세우는 법</strong>이에요.</p>"),
    ("courage", "차별에 맞서는<br>용기를 돕는 법!",
     "<p>차별은 예고없이 우리의 일상으로 찾아옵니다. 때로는 시선이나 호칭으로, 때로는 배제와 탈락으로 나타나죠.</p>"
     "<p>차별금지법은 <strong>차별에 맞서는 사람의 곁에 섭니다.</strong> 차별의 경험이 피해와 상처로 남지 않고, 용기 있는 대응과 일상의 회복으로 이어지도록 해요.</p>"),
    ("grounds", "누구도 혼자<br>남겨두지 않는 법!",
     "<p>차별금지법은 다음과 같은 이유로 일어나는 차별을 금지합니다. 이를 <strong>‘차별금지사유’</strong>라고 해요.</p>"
     f'<div class="visual">{grounds_html()}</div>'
     "<p>차별금지법은 누구도 혼자 남겨두지 않겠다는 평등의 약속입니다.</p>"),
    ("areas", "일상 곳곳을<br>바꾸는 법!",
     "<p>차별금지법은 일상의 네 가지 영역에서 벌어지는 차별을 금지합니다. 이를 <strong>‘차별금지영역’</strong>이라고 해요.</p>"
     + areas_html +
     '<p><a class="text-link" href="scenes.html">영역별로 달라질 장면 살펴보기 →</a></p>'),
    ("state", "차별 없는 사회,<br>국가가 만들어야 합니다.",
     "<p>차별의 책임은 차별하는 사람에게만 있지 않아요. 차별을 용인하는 사회가 함께 바뀌어야 합니다.</p>"
     "<p>차별금지법은 <strong>차별을 없애고 예방할 책임이 국가에 있음</strong>을 분명히 하는 법이에요. 차별금지법 제정으로 정부와 지자체는 모두가 평등하게 살아갈 수 있도록 제도를 만들고, 차별을 예방할 책임을 지게 됩니다.</p>"),
    ("start", "차별금지법으로<br>시작해요!",
     "<p>차별금지법이 모든 문제를 한 번에 해결하지는 못합니다. 그러나 차별금지법이 제정되면 일상에서부터 공공정책까지 평등을 구체적으로 요구할 수 있어요. 차별에 대한 사회적 인식 또한 달라지고요.</p>"
     '<div class="callout pink visual"><strong>우리의 일상이 조금씩 더 평등해지도록,<br>차별금지법 제정부터 시작해요.</strong></div>'),
]) + "</div></section>" + pager("about.html")

# ---------------------------------------------------------------- 02 scenes
SCENES = [
    ("work", "일할 때", "고용 영역", "pink", "일터", [
        "페미니스트라는 이유로 괴롭힘 당하지 않는 일터",
        "이주노동자라는 이유로 임금 차별을 겪지 않는 일터",
        "성소수자가 자신을 드러내도 걱정 없이 일할 수 있는 일터",
        "아프다는 이유로 채용 거부를 당하지 않는 일터",
        "성별을 이유로 업무에서 배제되지 않는 일터",
        "육아휴직을 하고 돌아와도 업무가 보장되는 일터"]),
    ("school", "배울 때", "교육 영역", "purple", "학교", [
        "성소수자 청소년도, 장애인 청소년도 있는 그대로 존중받고 배울 수 있는 학교",
        "혐오·차별·괴롭힘을 앞장서서 예방하는 학교",
        "트랜스젠더라는 이유로 수련회 참여가 제한되지 않는 학교",
        "차별·혐오 발언을 하는 학교장을 제지할 수 있는 학교",
        "다양한 가족 상황이 존중받는 학교"]),
    ("service", "물건을 사거나<br>서비스를 이용할 때", "재화·용역 영역", "yellow", "일상", [
        "장애를 이유로 금융 거래가 제한되지 않는 은행",
        "감염인이라는 이유로 진료를 거부당하지 않는 병원",
        "노동조합 조끼를 입고 편하게 쇼핑할 수 있는 백화점",
        "피부색을 이유로 거부당하지 않는 목욕탕",
        "성소수자도 자유롭게 대관할 수 있는 체육관",
        "어린이를 환대하는 카페"]),
    ("public", "행정서비스를<br>이용할 때", "행정서비스 영역", "white", "공공", [
        "성별·가족 관계 표기란이 다양하게 마련된 공공기관 문서",
        "수어·점자·음성 안내가 기본적으로 제공되는 민원 창구",
        "국적을 이유로 과도한 서류를 요구하지 않는 행정 절차",
        "차별 예방 교육이 정기적으로 이뤄지는 공공기관",
        "다양한 언어로 정확한 통역을 제공하는 법원과 경찰서",
        "휠체어로 접근할 수 있는 투표소"]),
]
areas_sections = ""
for i, (sid, name, area, tone, place, items) in enumerate(SCENES, 1):
    lis = "".join(f'<li class="scene-item"><span class="eq" aria-hidden="true">=</span><p>{s}</p></li>' for s in items)
    areas_sections += f"""<section class="area" id="{sid}" data-tone="{tone}" aria-labelledby="{sid}-title">
  <div class="wrap">
    <div class="area-head"><div><span class="num">{i:02d} / {place}</span><h2 id="{sid}-title">{name}</h2></div><span class="tag">{area}</span></div>
    <ul class="scene-list">{lis}</ul>
  </div>
</section>
"""
scenes_body = page_hero(
    "02", "일상의 변화", "차별금지법이 바꿀<br>우리 사회의 장면들",
    "차별금지법이 생기면 우리 삶은 어떻게 달라질까요?<br>일터, 학교, 일상, 공공에서 일어날 평등을 향한 변화를 만나보세요.",
    [(sid, name.replace("<br>", " ")) for sid, name, *_rest in SCENES]
) + areas_sections + """<section class="section soft"><div class="wrap">
  <p class="caption" style="margin:0">차별금지법이 지향하는 변화의 예시입니다. 차별 여부는 구체적 행위와 정당한 이유 등을 함께 살펴 판단합니다.</p>
</div></section>""" + pager("scenes.html")

# ---------------------------------------------------------------- 03 why
SURVEYS = """<div class="survey">
  <h3>차별금지법 제정 찬성</h3>
  <div class="rate-row">
    <div class="rate-label"><span>한국갤럽 · 2026년 상반기</span><strong>55%</strong></div>
    <div class="rate-track" role="img" aria-label="한국갤럽 조사 제정 찬성 55퍼센트"><div class="rate-fill" style="--value:55%"></div></div>
    <div class="scale"><span>0%</span><span>100%</span></div>
    <a class="rate-source" href="https://www.gallup.co.kr/gallupdb/reportContent.asp?seqNo=1632" target="_blank" rel="noopener noreferrer">조사 2026.3.31~4.2 · 1,001명 · 한국갤럽 원문 ↗</a>
  </div>
  <div class="rate-row">
    <div class="rate-label"><span>한국리서치 여론속의여론 · 2026년</span><strong>51%</strong></div>
    <div class="rate-track" role="img" aria-label="한국리서치 조사 제정 찬성 51퍼센트"><div class="rate-fill" style="--value:51%"></div></div>
    <div class="scale"><span>0%</span><span>100%</span></div>
    <span class="rate-source">조사 2026.5.22~26 · 1,000명 · 주간리포트 제393-2호 <em>(출처 링크 확인 필요)</em></span>
  </div>
  <div class="rate-row support">
    <div class="rate-label"><span>평등권 보장을 위한 법률 제정의 필요성에 동의<br><small class="muted">질문이 다른 보조 근거</small></span><strong>88.5%</strong></div>
    <div class="rate-track" role="img" aria-label="국가인권위원회 2020년 조사 평등권 보장 법률 제정 필요성 동의 88.5퍼센트"><div class="rate-fill" style="--value:88.5%"></div></div>
    <div class="scale"><span>0%</span><span>100%</span></div>
    <a class="rate-source" href="https://www.humanrights.go.kr/site/program/board/basicboard/view?boardtypeid=24&amp;menuid=001004002001&amp;boardid=7605604" target="_blank" rel="noopener noreferrer">국가인권위원회 · 2020 차별에 대한 국민인식조사 ↗</a>
  </div>
  <p class="caption">조사 시점·질문·조사 방식이 다릅니다. 하나의 추세선이나 합산 수치로 묶지 않습니다.</p>
</div>"""
DOTS = '<div class="dots" role="img" aria-label="권고 14차례, 원 하나가 권고 한 차례">' + "<span></span>" * 14 + "</div>"

why_body = page_hero(
    "03", "필요한 이유", "차별금지법이 제정될<br>수밖에 없는 이유",
    "시민의 요구, 종교계 안팎의 목소리, 국제사회의 권고. 차별금지법이 더 이상 미뤄질 수 없는 이유를 살펴봐요.",
    [("citizens", "많은 시민이 원해요"), ("religion", "일부 종교계의 반대"), ("global", "국제적 대세")]
) + f"""<section class="section" id="citizens" aria-labelledby="citizens-title"><div class="wrap">
  <div class="stat-hero">
    <div>
      <p class="label">01 / 시민의 목소리</p>
      <h2 class="section-title" id="citizens-title">많은 시민이<br>원하고 있어요.</h2>
      <div class="reading">
        <p>지난 윤석열퇴진광장에서 시민들이 꼽았던 사회대개혁 과제 1위는 <strong>차별금지·성평등·인권·소수자 권리 보장</strong>이었어요. 여기에는 포괄적 차별금지법도 포함됩니다.</p>
        <p style="margin-top:20px">지난 10년 동안 여러 기관의 여론 조사에서 차별금지법 제정에 찬성하는 비율은 55%부터 많게는 90%까지 나왔어요. 특히 갈수록 혐오와 관련한 사회적 사건들이 발생하면서 차별에 대한 감각과 평등을 향한 열망이 ‘차별금지법 제정’ 요구로 이어지고 있어요.</p>
      </div>
    </div>
    {SURVEYS}
  </div>
</div></section>
<section class="section tone-yellow-soft" id="religion" aria-labelledby="religion-title"><div class="wrap">
  <div class="block" style="padding:0;border:0">
    <div class="block-head"><span class="num">02 / 종교계</span><h2 id="religion-title">일부 종교계의 반대,<br>어떻게 볼까요?</h2></div>
    <div class="block-body">
      <p>흔히 차별금지법이 가로막힌 가장 큰 이유를 보수 개신교의 반대 때문이라고 생각합니다. 그러나 종교인 중 개신교인의 비율은 30% 내외이고, 개신교인 모두가 차별금지법에 반대하는 것도 아니에요. 일부 강하게 반대하는 목소리가 있는 건 사실이지만, 그 의견이 종교인 다수를 대표한다고 볼 수는 없습니다.</p>
      <div class="callout purple visual"><strong>차별금지법 제정에 찬성하는 교회와 기독교 단체도 있어요.</strong><br>‘차별과 혐오 없는 평등세상을 바라는 그리스도인 네트워크’ 같은 연대체가 있고, 교회에서 상처받은 이들을 환대하며 평등을 일구어 온 교회 공동체도 존재합니다.</div>
      <p>반대 주장과 근거의 상당수는 실제 법안 내용과 무관합니다. 성소수자를 시민의 범주에서 삭제하려는 시도는 인권의 기본 원칙에 위배되는 주장이에요. 민주주의 사회에서 이러한 주장이 종교적 신념이라는 이유로 정당화될 수도 없고요.</p>
      <p><a class="text-link" href="qna.html#q1">‘설교하면 처벌받나요?’ 질문 보기 →</a></p>
    </div>
  </div>
</div></section>
<section class="section" id="global" aria-labelledby="global-title"><div class="wrap">
  <div class="stat-hero">
    <div>
      <p class="label">03 / 국제사회</p>
      <h2 class="section-title" id="global-title">차별금지법은<br>국제적 대세입니다.</h2>
      <p class="big-number">14<small>차례</small></p>
      <p class="muted" style="margin-top:8px">2007년부터 유엔 조약기구가 한국 정부에 차별금지법 제정을 권고한 횟수</p>
      {DOTS}
      <p class="caption" style="margin-top:0">원 하나 = 권고 한 차례 · 공개 전 권고문 목록·집계 기준·기준일 확인 필요</p>
    </div>
    <div class="reading">
      <p>한국은 차별금지법을 제정해야 합니다. 이것은 국내의 이야기만이 아니에요. 2007년 유엔 인종차별철폐위원회를 시작으로 여성차별철폐위원회, 아동권리위원회 등의 유엔 조약기구가 무려 <strong>14차례</strong>나 한국 정부에 포괄적 차별금지법 제정을 권고했어요.</p>
      <p style="margin-top:20px">한국 정부의 답은 한결같았고요. “이에 대한 사회적 합의가 되지 않았다.”는 것이었습니다.</p>
      <div class="callout" style="margin-top:32px">
        <p class="callout-title">여러분은 어떻게 생각하세요?<br>사회적 합의는 여전히 ‘아직’일까요?<br>언제까지 ‘나중에’여야 할까요?</p>
        <p style="margin-top:16px">시민들은 꾸준히 과반의 찬성과 지지를 보내고 있습니다. 정치의 결단만 있다면 차별금지법 제정, 해낼 수 있어요.</p>
      </div>
    </div>
  </div>
</div></section>
""" + pager("why.html")

# ---------------------------------------------------------------- 04 qna
QA = [
    ("교회에서 ‘동성애는 죄’라고 말만 해도 처벌받나요?",
     "아니요. 차별금지법에는 설교를 처벌하는 조항이 없어요.",
     "아니요. 차별금지법에는 설교를 처벌하는 조항이 없어요. 일반 교회의 예배 활동은 법이 적용되는 영역도 아니고요. 다만 차별금지법은 성적지향·성별정체성을 이유로 한 차별이 ‘잘못’이라는 점을 분명히 선언하는 법입니다. 처벌하지 않는다고 해서 혐오가 정당해지는 것은 아니니까요."),
    ("표현의 자유가 침해되는 것 아닌가요?",
     "헌법과 국제인권규범은 차별과 혐오를 선동하는 발언까지 표현의 자유로 보호하지 않아요.",
     "한국의 헌법과 국제인권규범은 차별과 혐오를 선동하는 발언까지 표현의 자유로 보호하지 않아요. 그런 표현은 누군가의 자유를 침해하기 때문이에요. 또한 차별이 존재하는 사회에서는 표현의 자유가 모두에게 똑같이 주어지지 않습니다. 가령, 이슬람 종교에 대한 차별과 편견이 심각한 사회일수록 이슬람교 신자는 표현의 자유를 누리기 어려울 것입니다. 이처럼 차별금지법은 모두가 표현의 자유를 동등하게 누리기 위해 오히려 꼭 필요한 법이에요."),
    ("여대가 없어지는 것 아닌가요?",
     "아니요. 실질적 평등을 위해 소수자를 지원하는 정책은 차별이 아니에요.",
     "아니요. 여대가 만들어진 이유는 성차별적인 사회에서 여성들이 적극적으로 교육 받을 수 있게 하기 위해서입니다. 이처럼 실질적 평등을 위해 소수자 집단을 지원하는 정책은 차별금지법이 금지하는 차별이 아니에요."),
    ("화장실 등 여성 공간이 위험해지는 것 아닌가요?",
     "트랜스젠더의 화장실 이용과 성범죄는 별개의 문제예요.",
     "트랜스젠더의 화장실 이용과 성범죄는 별개의 문제예요. 가해자가 누구든 성범죄는 관련 법에 따라 처벌됩니다. 차별금지법은 모두가 자신의 성별정체성에 맞게, 편하고 안전하게 공간을 사용할 수 있는 사회를 만들려는 법이에요. 나와 ‘다른’ 사람이 같은 공간에 있어서 느끼는 ‘불편함’은 안전에 대한 위협이나 피해와 동일하지 않아요. 트랜스젠더도 한 명의 시민으로서 걱정 없이 공공화장실을 사용할 수 있어야 해요. 이로 인해 성범죄가 늘어날 수 있다는 우려는 통계상 근거가 없는 것으로 밝혀지기도 했고요."),
    ("성범죄자가 교육기관에서 일할 수 있게 되는 것 아닌가요?",
     "아니요. 법률에 따른 성범죄자의 취업 제한은 차별금지법이 제정되어도 그대로 유지돼요.",
     "아니요. 차별금지법은 사회의 안전을 위해 최소한의 제한까지 없애는 법이 아니에요. 법률에 따른 성범죄자 등의 취업 제한은 차별금지법이 제정되어도 그대로 유지됩니다. 차별금지법의 ‘전과 차별 금지’는 과거 범죄로 처벌받은 사람을 합리적 이유 없이 차별하지 말자는 뜻이에요. 기본권을 제한하는 법률이 존재하지 않고, 과거의 잘못과 무관한 업무의 경우 취업이나 사회생활에서 무조건 배제하는 것은 부당한 일이니까요."),
    ("학력에 따라 차별하는 건 공정한 것 아닌가요?",
     "차별금지법은 업무에 필요한 능력과 무관하게 오직 학력만을 이유로 하는 차별을 금지해요.",
     "학력이 정말 ‘개인의 선택과 노력’만으로 정해질까요? 높은 확률로 부모의 소득, 지역, 생활 환경에 따라 학력은 크게 달라질 수밖에 없어요. 출발점이 다르니까요. 이런 상황 속에서 차별금지법은 업무에 필요한 능력과 무관하게 오직 학력만을 이유로 하는 차별을 금지합니다."),
    ("소수를 위해 다수가 불편해지는 법 아닌가요?",
     "누구나 어떤 상황에서는 차별받는 소수자가 될 수 있어요.",
     "차별금지법은 모든 사람을 위한 법이에요. 차별금지사유(성별, 장애, 질병, 나이, 출신국가, 출신민족, 인종, 피부색, 출신지역, 용모와 유전정보 등 신체조건, 혼인여부, 임신과 출산, 가족형태 및 가족상황, 종교, 사상 또는 정치적 의견, 형이 만료된 전과, 성적지향, 성별정체성, 학력, 고용형태, 사회적 신분)는 누구에게나 해당될 수 있어, 누구나 어떤 상황에서는 차별받는 소수자가 될 수 있어요. 소수를 위해 다수가 불편해지는 법이 아니라, 차별금지법은 모두가 서로를 존중하며 살아갈 수 있게 만드는 법이에요."),
    ("법이 생긴다고 차별이 모두 사라지는 건 아니잖아요?",
     "맞아요. 하지만 명백한 차별에 대해서는 최소한의 조치가 필요해요. 차별금지법은 바로 그 시작이에요.",
     "맞아요. 법만으로 차별이 모두 사라질 수는 없겠죠. 차별은 누군가의 편이나 악의, 몇몇 잘못된 제도로만 발생하는 것은 아니기 때문이에요. 편견을 바로잡는 교육, 차별을 예방하는 정책 등 다양한 노력이 함께 필요해요. 그런 한편, 명백한 차별에 대해서는 이를 바로잡고 막는 최소한의 조치가 있어야겠죠. 차별금지법은 우리 사회에 어떤 차별이 있는지 알아차리고, 해결을 시도할 수 있게 만드는 시작점입니다."),
    ("차별이라고 주장만 하면 무조건 차별인가요?",
     "아니요. 차별금지법은 정해진 사유와 정해진 영역에서 차별을 금지해요.",
     "아니요. 차별금지법에서 말하는 차별은 정해진 사유(성별, 장애, 질병 등)를 이유로 정해진 영역(고용, 교육, 재화·용역, 행정서비스)에서 합리적인 이유 없이 사람을 배제하거나 불리하게 대우하는 행위를 의미해요. 구별하거나 다르게 대우한다고 해서 모두 차별은 아니에요. ‘정당한 이유’ 없이 배제하고 불리하게 대우하는 것이 차별이에요."),
]


def qa_item(i, q, summary, detail=None):
    detail_html = f'<div class="q-detail"><strong>자세한 답변</strong><p>{detail}</p></div>' if detail else ""
    tag = "details" if detail else "a"
    if detail:
        return f"""<details class="qa" id="q{i}"><summary><span class="q-number">Q{i}</span><span class="q-copy"><span class="q-title">{q}</span><span class="q-preview">{summary}</span></span><span class="q-toggle" aria-hidden="true"></span></summary>{detail_html}</details>"""
    return f"""<details class="qa"><summary><span class="q-number">Q{i}</span><span class="q-copy"><span class="q-title">{q}</span></span><span class="q-toggle" aria-hidden="true"></span></summary><div class="q-detail"><p>{summary}</p><p style="margin-top:10px"><a class="text-link" href="qna.html#q{i}">자세한 답변 보기 →</a></p></div></details>"""


qna_list = "\n".join(qa_item(i, q, s, d) for i, (q, s, d) in enumerate(QA, 1))
qna_body = page_hero(
    "04", "Q&A", "차별금지법에<br>관한 질문들",
    "차별금지법에 관해 자주 하는 질문들을 차근차근 살펴봐요. 답의 요지를 먼저 읽고, 더 궁금하면 펼쳐 보세요."
) + f"""<section class="section"><div class="wrap">
  <div class="faq-toolbar">
    <div class="field"><label for="faq-search">질문 검색</label><input type="search" id="faq-search" placeholder="예: 표현, 여대, 학력" aria-controls="faq-list" aria-describedby="faq-count"></div>
    <button type="button" class="btn small" id="faq-expand" aria-controls="faq-list" aria-expanded="false">모두 펼치기 <span aria-hidden="true">+</span></button>
  </div>
  <p class="faq-count" id="faq-count" role="status" aria-live="polite">질문 {len(QA)}개</p>
  <div id="faq-list">
{qna_list}
  </div>
  <div class="empty" id="faq-empty" hidden>일치하는 질문이 없습니다. 다른 단어로 검색해 주세요.</div>
</div></section>
""" + pager("qna.html")

# ---------------------------------------------------------------- 05 timeline
TIMELINE = [
    ("p0", "사회적 논의의 시작", "1998~2003", [
        ("1998~2003", "김대중 정부", "정부", "‘차별대우금지’ 대선 공약, 취임 후 법안 마련했으나 발의에 이르지 못함",
         "한국에서 차별금지법 논의는 김대중 정부(1998~2003)에서부터 시작되었습니다. 김대중 대통령은 제15대 대선에서 국민대화합을 위한 공약으로 ‘차별대우금지’를 제시하고, 취임 후 정부 법안을 마련했습니다. 그러나 발의에 이르지는 못했습니다.", False),
    ]),
    ("p17", "17대 국회", "2004~2008", [
        ("2003", "노무현 정부", "정부", "‘사회적 차별금지법’ 대선 공약, 국정과제로 차별금지법 추진 시작",
         "이어 노무현 대통령(2003~2008)이 제16대 대선에서 ‘사회적 차별금지법’을 공약으로 제시했고, 취임 후 국정과제 중 「국민통합과 양성평등의 구현」을 위한 세부과제로 차별금지법을 추진했습니다.", False),
        ("2006", "국가인권위원회", "권고", "국무총리에 「차별금지법안」 권고",
         "이를 위해 국가인권위원회가 2003년 차별금지법제정추진위원회를 구성해 법안 연구를 시작했고, 2006년 국무총리에게 「차별금지법안」을 권고했습니다.", False),
        ("2007", "법무부", "입법", "7개 차별금지사유 삭제한 「차별금지법안」 발의와 그에 대한 비판",
         "정부는 2007년 10월 2일 국가인권위원회 권고법안을 토대로 한 「차별금지법안」을 입법예고하였으나, 두 달 후인 2007년 12월 12일 입법예고안에 존재했던 7개의 차별금지사유(병력, 출신국가, 언어, 가족형태 또는 가족상황, 범죄 및 보호처분의 전력, 성적 지향, 학력)를 삭제한 형태의 「차별금지법안」(정부안)을 발의했습니다.</p><p style=\"margin-top:12px\">인권시민사회는 일부 종교계나 재계의 반대가 있다는 이유로 차별금지사유를 삭제한 정부법안은 ‘차별을 조장하는 차별금지법’이라는 비판을 하면서 ‘차별금지법의 올바른 제정을 위한 반차별공동행동(준)’을 결성하고 정부법안에 대항하는 「차별금지법안」(노회찬 의원 대표발의)을 발의시켰습니다. 2008년 5월, 17대 국회가 임기만료하면서 두 법안은 자동폐기되었습니다.", True),
    ]),
    ("p18", "18·19대 국회", "2008~2016", [
        ("2008~2016", "정부·국회", "입법", "꾸준히 이어진 차별금지법안 논의와 발의",
         "18대 국회 이후 차별금지법 제정을 위한 노력은 정부와 국회에서 형식적으로나마 꾸준히 이어졌습니다. 이명박 정부(2008~2013)는 법무부 산하에 ‘차별금지법TF’ 및 ‘차별금지법 특별분과위원회’를 구성·운영하며 법안을 논의하였고, 박근혜 정부(2013~2017) 또한 ‘사회통합적 인권체계 구축’을 위한 국정과제로 차별금지법 제정을 채택하고 ‘차별금지법 제정추진단’을 운영하며 법안 논의를 진행했습니다.</p><p style=\"margin-top:12px\">18대 국회에서 「차별금지기본법안」(박은수 의원 대표발의), 「차별금지법안」(권영길 의원 대표발의) 등 2개 법안이 발의되었고, 19대 국회에서 「차별금지법안」(김재연 의원 대표발의), 「차별금지법안」(김한길 의원 대표발의), 「차별금지법안」(최원식 의원 대표발의) 등 3개 법안이 발의되었습니다.", False),
        ("2013", "김한길·최원식 의원", "철회", "「차별금지법안」 철회 사태와 인권 제도의 후퇴",
         "꾸준히 이어지던 차별금지법 제정 시도 흐름에 제동을 건 것은 2013년 법안 철회 사태였습니다. 2013년 4월 24일 김한길 의원과 최원식 의원은 보수개신교계의 항의 등이 거세다는 이유로 법안 발의 2개월 만에 차별금지법안을 각각 철회했습니다.</p><p style=\"margin-top:12px\">2012년 출범한 차별금지법제정연대 등 인권시민사회는 법안이 실제로 철회되는 경우 “보수기독교 세력이 국회의 입법 활동을 저지하거나 개악할 수 있다는 것을 증명하는 초유의 사례가 될 것”이라고 우려하며 철회 중단을 요구하였으나 철회는 강행되었습니다. 인권시민사회의 경고대로 2013년 법안 철회 사태는 극우적 주장을 결집시켜 인권 법·정책을 가로막은 최초의 성공사례가 되었고 이후 지역인권조례 등 한국의 각종 인권 제도가 동일한 방식으로 막히거나 후퇴되기 시작하였습니다.", True),
    ]),
    ("p20", "20대 국회", "2016~2020", [
        ("2016~2020", "국회", "입법", "법안 발의조차 하지 못한 첫 국회",
         "2013년 법안 철회 사태 이후 2020년 5월 20대 국회 임기 만료 시까지 약 7년 간 국회에서 차별금지법안은 발의되지 못했습니다.", False),
    ]),
    ("p21", "21대 국회", "2020~2024", [
        ("2020", "국가인권위원회", "권고", "「평등 및 차별금지에 관한 법률」 제정 의견표명", "", False),
        ("2020~2021", "국회 · 시민", "시민 행동", "4개의 법안 발의와 10만 명 시민들의 국민동의청원",
         "긴 침묵이 깨진 것은 21대 국회가 시작된 2020년 6월이었습니다. 2020년 6월 29일 「차별금지법안」(장혜영 의원 대표발의)이 발의되었고, 그 다음 날인 6월 30일 국가인권위원회가 국회에 「평등 및 차별금지에 관한 법률」을 제정하라는 의견표명을 했습니다.</p><p style=\"margin-top:12px\">약 1년 뒤인 2021년 6월 14일 10만인의 시민들이 국민동의청원안인 「차별금지법 제정에 관한 청원」을 국회에 접수하였고, 이어 「평등에 관한 법률안」(이상민 의원 대표발의), 「평등에 관한 법률안」(박주민 의원 대표발의), 「평등 및 차별금지에 관한 법률안」(권인숙 의원 대표발의)이 연속으로 발의되었습니다.", True),
        ("2021~2022", "인권시민사회 · 국회", "시민 행동", "법 제정을 촉구하는 단식농성과 공청회",
         "인권시민사회는 10만 국민동의청원 성사 이후 30일 간의 전국도보행진, 46일 간의 단식농성을 이어가며 국회 논의와 법 제정을 촉구하였습니다. 2022년 5월 25일 국회 법제사법위원회 제1소위원회가 ‘차별금지법(평등에 관한 법률) 제정 관련 공청회’를 개최하였으나 21대 국회에서 논의는 더 나아가지 못했습니다. 4개의 발의법안 및 국민동의청원안은 21대 국회 임기만료로 자동폐기되기에 이르렀습니다.", False),
    ]),
    ("p22", "22대 국회", "2024~", [
        ("2026", "국회", "입법", "현재 2개의 법안이 국회 계류 중",
         "현재 22대 국회에는 2026년 1월 9일 「차별금지법안」(손솔 의원 대표발의), 2026년 2월 5일 「차별금지법안」(정춘생 의원 대표발의) 2개의 법안이 발의되어 있는 상태입니다.", True),
    ]),
]
periods = ""
for i, (pid, name, years, items) in enumerate(TIMELINE):
    lis = ""
    for date, actor, kind, title, desc, featured in items:
        desc_html = f"<p>{desc}</p>" if desc else ""
        cls = "timeline-item featured" if featured else "timeline-item"
        lis += f"""<li class="{cls}"><article class="timeline-card">
  <div class="timeline-meta"><time>{date}</time><span>{actor}</span><span class="timeline-kind">{kind}</span></div>
  <h3>{title}</h3>{desc_html}
</article></li>"""
    extra = '<p class="source muted" style="font-size:13px;margin-top:16px">기준일 2026.10.21 · 새 소식이 생기면 이 구간에 항목을 추가합니다.</p>' if pid == "p22" else ""
    periods += f"""<section class="period" id="{pid}" aria-labelledby="{pid}-title">
  <div class="period-head"><span class="num">{i:02d}</span><h2 id="{pid}-title">{name}</h2><span class="years">{years}</span></div>
  <div><ol class="timeline">{lis}</ol>{extra}</div>
</section>
"""
timeline_body = page_hero(
    "05", "타임라인", "차별금지법<br>타임라인",
    "평등을 위한 요구는 20년 넘게 이어져 왔어요. 사회적 논의의 시작부터 22대 국회까지, 입법의 경로를 따라가 봐요.",
    [(pid, name) for pid, name, *_ in TIMELINE]
) + f'<section class="section"><div class="wrap">{periods}</div></section>' + pager("timeline.html")

# ---------------------------------------------------------------- 06 resources
RESOURCES = [
    ("안내서", "2025", "기독교인을 위한 차별금지법 안내서 &lt;차별금지법이 궁금한 당신에게&gt;",
     "차별과 혐오 없는 평등세상을 바라는 그리스도인 네트워크(평등세상) X 차별금지법제정연대",
     "차별금지법과 기독교 사이의 거리를 좁히고 더 많은 접점을 발견하기를 바라는 마음으로 안내서를 만들었습니다. 안내서는 민주주의와 소수자 인권이 진전되는 과정에서 기독교가 써내려온 역사를 현재와 잇습니다. 존재 자체로 사랑하는 하나님의 세상과 차별금지법으로 만들고 싶은 모두가 존엄한 세상을 포개어 봅니다."),
    ("보고서", "2025", "&lt;극우리포트 : 성소수자 혐오에서 내란옹호까지&gt;",
     "성소수자차별반대 무지개행동 X 차별금지법제정연대",
     "최근 우리 사회에 가시화된 극우 세력의 특징과 이들이 결집한 역사적 배경을 분석하는 보고서입니다. 특히, 극우 세력화의 주된 동력으로서 성소수자 혐오와 차별금지법 제정 반대 운동이 차지한 역할을 검토하고, 민주주의 회복을 위해 혐오와 차별의 문제를 해결하기 위한 시급한 과제를 영역별로 제시하고 있습니다."),
    ("자료집", "2026", "&lt;차별금지법 권고 20년 : 한국사회 현재적 쟁점과 차별금지법&gt; 학술대회 자료집",
     "인권법학회 X 차별금지법제정연대",
     "2006년 국가인권위원회가 한국 정부에 포괄적 차별금지법 제정을 권고한 후로부터 20년이 흘렀습니다. 2026년 포괄적 차별금지법은 여전히 제정중입니다. 20년 동안 차별금지법은 그저 멈춰있지 않았습니다. 시민들의 여론은 높아졌고, 차별금지법 제정은 한국사회의 평등의 척도로 여겨지고 있습니다. 차별의 개념 재구성부터, 포괄적 차별금지법의 구체적 쟁점을 살피고 더 나은 제도화를 위한 방안을 모색합니다."),
    ("안내서", "2025", "안내서 &lt;광장에서 펼쳐보는 차별금지법 Q&amp;A&gt;",
     "차별금지법제정연대",
     "지난 2025년 12월 3일 내란 사태 이후, 광장에는 평등의 요구가 울려 퍼졌습니다. 차별은 먹고 사는 문제이며 때로는 사람이 죽고 사는 문제입니다. 그러므로 평등은 우리 삶이 당면한 생존의 문제입니다. “이제 차별과 혐오가 설 자리는 없다”고 선언하던 광장에서 왜 포괄적 차별금지법이 필요한지, 차별금지법이 제정되면 무엇이 바뀌는지 차별금지법에 대한 궁금증을 해소하기 위해 배포한 안내서입니다."),
    ("안내서", "2021", "차별금지/평등법 제정을 위한 안내서 &lt;차별금지법, 평등의 약속&gt;",
     "차별금지법제정연대",
     "2021년 6월 국민동의청원 10만행동 이후 정치권이 더 이상 사회적 합의를 거론하지 못하게 한 힘이 모인 자리에서 제작된 안내서입니다. 차별금지와 평등의 약속이 누구에게 어떤 변화를 가져올지 저마다의 질문을 가지고, 차별금지법 제정을 필요로 하는 이들이 손에 쥘 수 있는 싸움의 언어를 함께 만들어갑시다."),
    ("보고서", "2020", "평등정책 보고서 &lt;노동/일의 세계&gt;",
     "차별금지법제정연대 평등정책TF",
     "왜 모두에게 존엄한 노동이 보장되어야 하는지, 일의 세계를 평등하게 만드는 것이 어떤 의미인지, 이를 위해서는 어떤 평등정책이 필요한지 등을 주요하게 다루고 있습니다. 노동 영역의 차별 현실을 분석하고자, 특히 소수자가 일의 세계에서 어떠한 조건과 경험을 맞닥뜨리기 쉬운지 살펴보았습니다. 평등한 일의 세계는 어떠해야 하는지 전망하는 보고서입니다."),
    ("영상", "2025", "새로운 광장을 만드는 시민들의 목소리 ‘백 개의 광장’",
     "차별금지법제정연대",
     "차별과 혐오를 가까스로 버티며 지키고 있는 삶의 현장에서 들려오는 시민들의 외침. “더 이상 미루지 말라.” 다양한 정체성을 가지고 자기의 자리에서 분투하며 일상을 살아가는 시민들이, 자신이 직접 겪거나 목격한 경험을 통해 ‘차별’의 의미를 환기하고, 이러한 차별을 없애기 위해 필요한 것들을 스스로 질문하고 사유하며 카메라 앞에 선 목소리들의 기록입니다."),
    ("영상", "2025", "다시 광장에서 말하는 차별금지법 ‘만개할 평등’",
     "차별금지법제정연대",
     "지난 겨울 광장을 가득 메웠던 ‘반차별과 평등의 민주주의’ 구호를 현실로 만들기 위해 우리에게 필요한 것은, 20년 간 보류되었던 포괄적 차별금지법. 법률가, 연구자, 종교인, 저술가, 활동가 다섯 명이 1년 만에 다시 광장에 서서 극우와 혐오가 활개치는 지금, “내란 청산을 위한 정답, 인간 존엄 보장의 마지노선, 더 이상 미룰 수 없는 흐름, 가정과 교회와 나라를 망칠 리 없는, 더 작은 목소리를 듣는 광장”으로서의 차별금지법을 말합니다."),
]
res_items = "".join(f"""<li class="resource">
  <div class="meta"><span class="kind">{kind}</span><span class="year">{year}</span></div>
  <h3>{title}</h3>
  <p class="by">{by}</p>
  <p>{desc}</p>
  <a class="btn small" href="#" data-todo="link">자료 보기 <span aria-hidden="true">↗</span></a>
</li>""" for kind, year, title, by, desc in RESOURCES)

resources_body = page_hero(
    "06", "자료", "더 보기",
    "차별금지법에 대해 더 자세히 알아가고, 차별금지법을 둘러싼 이야기가 궁금한 분을 위해 다양한 형태의 자료를 소개합니다.",
    [("library", "자료 모음"), ("info", "정보")]
) + f"""<section class="section" id="library" aria-labelledby="library-title"><div class="wrap">
  <p class="label">자료 모음</p>
  <h2 class="section-title" id="library-title">안내서·보고서·영상</h2>
  <ul class="resource-list">{res_items}</ul>
  <p class="caption">자료 링크는 원고 확정 후 연결합니다.</p>
</div></section>
<section class="section soft" id="info" aria-labelledby="info-title"><div class="wrap">
  <p class="label">정보</p>
  <h2 class="section-title" id="info-title">차별금지법제정연대</h2>
  <table class="info-table">
    <tbody>
      <tr><th scope="row">제작</th><td>차별금지법제정연대</td></tr>
      <tr><th scope="row">홈페이지</th><td><a href="{LINKS['home']}" {EXT}>equalityact.kr ↗</a></td></tr>
      <tr><th scope="row">후원 계좌</th><td>우리은행 1006‒201‒507617 차별금지법제정연대<br><a href="{LINKS['donate']}" {EXT}>후원하기 ↗</a></td></tr>
      <tr><th scope="row">SNS</th><td><a href="{LINKS['facebook']}" {EXT}>페이스북 @equalact2017</a> · <a href="{LINKS['instagram']}" {EXT}>인스타그램 @equalityact_allpeople</a> · <a href="{LINKS['twitter']}" {EXT}>트위터 @equalact</a></td></tr>
      <tr><th scope="row">이메일</th><td><a href="mailto:equalact2017@gmail.com">equalact2017@gmail.com</a></td></tr>
      <tr><th scope="row">뉴스레터</th><td><a href="{LINKS['newsletter']}" {EXT}>월간평등UP 구독하기 ↗</a></td></tr>
    </tbody>
  </table>
</div></section>
""" + pager("resources.html")

# ---------------------------------------------------------------- index
scene_cards = "".join(f"""<a class="scene-card {cls}" href="scenes.html#{sid}">
  <div class="scene-top"><span class="scene-index">{i:02d} / {place}</span><span class="scene-glyph" aria-hidden="true">{glyph}</span></div>
  <h3>{name}</h3><p>{items[0]}</p>
  <span class="scene-link">장면 살펴보기 <span class="arrow" aria-hidden="true">→</span></span>
</a>""" for i, ((sid, name, _a, _t, place, items), cls, glyph) in enumerate(
    zip(SCENES, ["pink", "purple-bg", "yellow", "white"], ["[ ]", "?", "↔", "="]), 1))
qa_simple = "\n".join(qa_item(i, q, s) for i, (q, s, _d) in enumerate(QA, 1))

index_body = f"""<section class="hero" aria-labelledby="hero-title">
  <div class="wrap hero-grid">
    <div>
      <p class="overline">차별금지법 한눈에 보기</p>
      <h1 id="hero-title">차별금지법,<br>모두를 위한<br><mark>평등의 기준</mark></h1>
      <p>우리의 일상이 조금씩 더 평등해지도록,<br>차별금지법 제정부터 시작해요!</p>
      <div class="actions"><a class="btn purple large" href="about.html">알아보기 <span class="arrow" aria-hidden="true">→</span></a><a class="btn on-dark large" href="qna.html">질문 살펴보기</a></div>
    </div>
    <div class="shape-panel"><small>혼자 남겨두지 않겠다는 약속</small><span class="eq" aria-hidden="true">=</span><p class="caption">차별 없는 사회,<br>함께 시작해요.</p></div>
  </div>
</section>

<section class="section" aria-labelledby="summary-title"><div class="wrap">
  <p class="label">01 / 차별금지법 3줄 요약</p>
  <h2 class="section-title" id="summary-title">차별금지법은<br><span class="mark">어떤 일을 하는 법</span>일까요?</h2>
  <div class="pillars">
    <article class="pillar"><div class="role">기준</div><h3>평등의 기준을<br>세우는 법</h3><p>차별금지법은 차별이 무엇인지 정하고, 차별을 포괄적으로 막고 예방합니다.</p></article>
    <article class="pillar"><div class="role">곁</div><h3>차별에 맞서는<br>용기를 돕는 법</h3><p>차별금지법은 차별에 맞서는 사람의 곁에 서서, 용기 있는 대응과 일상의 회복을 만듭니다.</p></article>
    <article class="pillar"><div class="role">책임</div><h3>차별 없는 사회,<br>국가가 만들어야 합니다</h3><p>차별금지법은 차별을 없애고 예방할 책임이 국가에 있음을 분명히 합니다.</p></article>
  </div>
</div></section>

<section class="section tone-purple-soft" aria-labelledby="grounds-title"><div class="wrap">
  <p class="label">02 / 차별금지사유</p>
  <h2 class="section-title" id="grounds-title">누구도 혼자<br>남겨두지 않는 법</h2>
  <p class="section-intro" style="margin-bottom:32px">어떠한 이유로도 차별받지 않도록, 차별금지법은 누구도 혼자 남겨두지 않겠다는 평등의 약속입니다.</p>
  {grounds_html()}
  <div class="section-foot"><a class="btn" href="about.html#grounds">더 알아보기 <span class="arrow" aria-hidden="true">→</span></a></div>
</div></section>

<section class="section" aria-labelledby="scenes-title"><div class="wrap">
  <p class="label">03 / 일상의 변화</p>
  <h2 class="section-title" id="scenes-title">차별금지법이 바꿀<br>우리 사회의 장면들</h2>
  <div class="scene-grid">{scene_cards}</div>
  <div class="section-foot"><a class="btn" href="scenes.html">더 알아보기 <span class="arrow" aria-hidden="true">→</span></a></div>
</div></section>

<section class="section tone-yellow" aria-labelledby="stats-title"><div class="wrap">
  <p class="label">04 / 통계와 근거</p>
  <h2 class="section-title" id="stats-title">차별금지법에 대한 사회적 합의는<br>여전히 ‘아직’일까요?</h2>
  <div class="stat-hero" style="margin-top:40px">
    <div>
      <h3 style="font-size:26px;margin-bottom:12px">많은 시민이 차별금지법을 원하고 있어요.</h3>
      <p class="muted">여러 기관의 여론 조사에서 과반이 차별금지법 제정에 찬성했어요.</p>
      <div class="survey" style="margin-top:24px;padding:24px 28px">
        <p class="big-number">14<small>차례</small></p>
        <p class="callout-title" style="margin-top:8px">차별금지법은 국제적 대세이기도 합니다.</p>
        <p class="muted" style="font-size:15px;margin-top:6px">2007년부터 유엔 조약기구가 한국 정부에 차별금지법 제정을 권고한 횟수</p>
        {DOTS}
      </div>
    </div>
    {SURVEYS}
  </div>
  <div class="section-foot"><a class="btn" href="why.html">더 알아보기 <span class="arrow" aria-hidden="true">→</span></a></div>
</div></section>

<section class="section" aria-labelledby="qa-title"><div class="wrap">
  <p class="label">05 / 질문</p>
  <h2 class="section-title" id="qa-title">자주 하는 질문들을<br>차근차근 살펴봐요</h2>
  <div class="qa-list-simple" style="margin-top:32px">
{qa_simple}
  </div>
  <div class="section-foot"><a class="btn" href="qna.html">더 알아보기 <span class="arrow" aria-hidden="true">→</span></a></div>
</div></section>

<section class="section tone-pink-soft" id="join" aria-labelledby="join-title"><div class="wrap">
  <p class="label">06 / 함께하기</p>
  <h2 class="section-title" id="join-title">지금 나에게 맞는 방식으로<br><span class="mark">함께해요.</span></h2>
  <div class="join">
    <article class="join-path">
      <h3>알리기</h3>
      <p>차별금지법이 있는 나라를 하루라도 앞당기고 싶다면, 주변에 차별금지법을 알려주세요.</p>
      <div class="actions" style="margin-top:auto">
        <button class="btn purple small" type="button" data-share>사이트 링크 공유</button>
        <a class="btn small" href="{LINKS['leaflet']}" {EXT}>&lt;당신에게 차별금지법을 선물합니다&gt; 리플렛 신청하기 <span aria-hidden="true">↗</span></a>
      </div>
    </article>
    <article class="join-path">
      <h3>소식 받기</h3>
      <p>차별금지법 제정과 반차별 활동 소식이 궁금하다면? 매월 한국사회의 평등 지수를 끌어올리는 <strong>월간평등UP</strong>을 구독하세요.</p>
      <form class="subscribe" id="subscribe-form" action="{LINKS['newsletter']}" novalidate>
        <div class="field"><label for="sub-name">이름</label><input id="sub-name" name="name" autocomplete="name"></div>
        <div class="field"><label for="sub-email">이메일</label><input id="sub-email" name="email" type="email" autocomplete="email" required aria-describedby="sub-email-error"><p class="error" id="sub-email-error" hidden>이메일 주소를 확인해 주세요.</p></div>
        <label class="check"><input type="checkbox" required> 개인정보 수집 및 이용 동의 (필수)</label>
        <label class="check"><input type="checkbox" required> 광고성 정보 수신 동의 (필수)</label>
        <button class="btn purple small" type="submit">구독하기</button>
      </form>
    </article>
    <article class="join-path">
      <h3>힘 보태기</h3>
      <p>차별금지법 제정 운동에 함께하고 싶다면?</p>
      <p class="muted" style="font-size:14px">우리은행 1006‒201‒507617<br>차별금지법제정연대</p>
      <a class="btn purple small" href="{LINKS['donate']}" {EXT}>후원하기 <span aria-hidden="true">↗</span></a>
    </article>
  </div>
</div></section>"""

# ---------------------------------------------------------------- write
PAGE_LINK = re.compile(r'href="(index|' + "|".join(f[:-5] for f, *_ in PAGES) + r')\.html(#[^"]*)?"')


def clean_urls(html):
    """내부 링크를 확장자 없는 주소로: about.html#x → /about#x, index.html → /"""
    html = PAGE_LINK.sub(lambda m: f'href="{"/" if m[1] == "index" else "/" + m[1]}{m[2] or ""}"', html)
    return html.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')


pages = {
    "index.html": ("차별금지법", "차별금지법, 모두를 위한 평등의 기준. 우리의 일상이 조금씩 더 평등해지도록, 차별금지법 제정부터 시작해요.", index_body),
    "about.html": ("차별금지법이 뭐야?", "평등의 기준을 세우고, 차별에 맞서는 용기를 돕고, 누구도 혼자 남겨두지 않는 법. 차별금지법을 소개합니다.", about_body),
    "scenes.html": ("차별금지법이 바꿀 우리 사회의 장면들", "일터, 학교, 일상, 공공에서 차별금지법이 만들 평등을 향한 변화를 만나보세요.", scenes_body),
    "why.html": ("차별금지법이 제정될 수밖에 없는 이유", "많은 시민이 원하고, 국제사회가 14차례 권고한 법. 차별금지법이 필요한 이유를 살펴봅니다.", why_body),
    "qna.html": ("차별금지법에 관한 질문들", "차별금지법에 관해 자주 하는 질문 9가지와 답변을 정리했습니다.", qna_body),
    "timeline.html": ("차별금지법 타임라인", "사회적 논의의 시작부터 22대 국회까지, 차별금지법 입법의 경로를 정리했습니다.", timeline_body),
    "resources.html": ("더 보기", "차별금지법에 관한 안내서·보고서·영상 자료와 차별금지법제정연대 정보를 소개합니다.", resources_body),
}
for name, (title, desc, body) in pages.items():
    (OUT / name).write_text(clean_urls(layout(name, title, desc, body)), encoding="utf-8")
    print("wrote", name)
