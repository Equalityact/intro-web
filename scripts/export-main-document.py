"""Export the existing home-page copy as a Google Docs heading-based appendix."""
import json
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
COPY=json.loads((ROOT/'content/manuscript.json').read_text())
HOME=COPY['home']
FIELDS=[('사이트 이름','name'),('메인 슬로건','slogan'),('메인 소개','description'),('요약 섹션 제목','summary_title'),('법안 이름 안내','summary_note'),('히어로 카드 문구','grounds_title'),('통계 제목','stats_title'),('찬성 비율','support_value'),('찬성 설명 제목','support_title'),('찬성 설명','support_caption'),('정책 과제 제목','policy_title'),('정책 과제 설명','policy_caption'),('국제사회 권고 횟수','recommendation_value'),('국제사회 권고 제목','recommendation_title'),('국제사회 권고 설명','recommendation_caption'),('질문 섹션 제목','questions_title'),('함께하기 제목','join_title'),('공유 안내','share'),('리플렛 버튼','leaflet'),('뉴스레터 안내','newsletter_question'),('뉴스레터 설명','newsletter'),('뉴스레터 버튼','newsletter_button'),('후원 안내','donate'),('출처 표시','source_label')]
def main_html():
 parts=['<h1>0. 메인페이지</h1>']
 for title,key in FIELDS:
  parts.append(f'<h2>{escape(title)}</h2>')
  text='\n'.join(HOME['slogan_lines']) if key=='slogan' else HOME[key]
  parts.append('<p>'+escape(text).replace('\n','<br>')+'</p>')
 parts.append('<h2>메인 카드</h2>')
 for title,body in HOME['pillars']:parts.extend([f'<h3>{escape(title)}</h3>',f'<p>{escape(body)}</p>'])
 parts.append('<h2>여론조사</h2>')
 for (_,name,date,url),values in zip(HOME['surveys'][:2],HOME['survey_values']):
  parts.extend([f'<h3>{escape(name)}</h3>',f'<p>{escape(date)}</p>',f'<p><a href="{escape(url,quote=True)}">출처</a></p>'])
  for label,value in zip(HOME['survey_responses'],values):parts.append(f'<p>{escape(label)} {value}%</p>')
 parts.extend(['<h2>리플렛 신청 링크</h2>',f'<p><a href="{escape(COPY["links"]["leaflet"],quote=True)}">리플렛 신청하기</a></p>'])
 return '\n'.join(parts)
if __name__=='__main__':
 target=ROOT/'docs/main-page-appendix.html'
 target.write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>구글문서 메인페이지 추가 원고</title><body>'+main_html()+'</body></html>')
 print(target)
