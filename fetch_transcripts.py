"""Download the CS329A lecture captions from YouTube and build the transcript pages (1_*.html … 9_*.html).

The transcripts are not committed to the repo (the lectures are Stanford's content), so run this once:
    pip install youtube-transcript-api
    python3 fetch_transcripts.py
"""
import html, re
from youtube_transcript_api import YouTubeTranscriptApi

# (YouTube id, file slug, English title, Korean title) — playlist order
LECTURES = [
    ("6YnLB0XbTnI", "course_overview", "Course Overview", "강의 개요"),
    ("-Ggc37xLj_Y", "test_time_compute_scaling", "Test-Time Compute Scaling", "테스트 타임 컴퓨트 스케일링"),
    ("p7TdPUcPoik", "robust_verification", "Robust Verification", "견고한 검증"),
    ("Lxh9RF5S-K0", "learning_from_feedback_with_tools_code", "Learning from Feedback with Tools/Code", "도구·코드 피드백으로 배우기"),
    ("Ml_fp9XkB8Y", "planning_and_multi_step_reasoning", "Planning and Multi-Step Reasoning", "계획과 다단계 추론"),
    ("yVnmHSAy3ck", "train_time_scaling_scaling_rl", "Train Time Scaling/Scaling RL", "학습 시점 스케일링과 RL 확장"),
    ("Uni9dqyuuDM", "self_improvement_and_deep_research_agents", "Self-Improvement and Deep Research Agents", "자기 개선과 딥 리서치 에이전트"),
    ("8JAqLnTaZu4", "agentic_evaluations_and_long_horizon_tasks", "Agentic Evaluations and Long Horizon Tasks", "에이전트 평가와 장기 과제"),
    ("AyO6wyu4DEg", "future_research_areas", "Future Research Areas", "앞으로의 연구 방향"),
]


def paragraphs(frags):
    """Join caption fragments into paragraphs, breaking at a sentence end once a paragraph has ~400 chars. Words are kept as-is."""
    paras, cur, start = [], [], None
    for t, x in frags:
        if start is None:
            start = t
        cur.append(x)
        if re.search(r'[.?!]["\')\]]?$', x) and sum(len(c) for c in cur) >= 400:
            paras.append((start, " ".join(cur)))
            cur, start = [], None
    if cur:
        paras.append((start, " ".join(cur)))
    return paras


def page(n, vid, title, ko, en, paras):
    e = html.escape
    body = "\n".join(
        f'<p><a class="ts" href="https://www.youtube.com/watch?v={vid}&amp;t={t}s" target="_blank" rel="noopener">[{t // 60:02d}:{t % 60:02d}]</a> {e(p)}</p>'
        for t, p in paras)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><link rel="icon" href="data:,">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="ui.css"></head><body>
<div class="bg" aria-hidden="true"><i></i><i></i><i></i></div>
<header class="glass bar"><a class="back" href="/" data-i18n="back">← 튜터로</a>
<div class="seg" role="group" aria-label="Language"><button data-lang="ko">한국어</button><button data-lang="en">EN</button></div></header>
<main class="glass sheet">
<p class="kicker">CS329A · Part {n}</p>
<h1 data-ko="{e(ko)}" data-en="{e(en)}">{e(ko)}</h1>
<p class="meta"><span data-i18n="sub">원문 영어 자막 · 타임스탬프를 누르면 그 장면부터 재생돼요</span> · <a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener" data-i18n="yt">YouTube에서 보기</a></p>
<label class="find"><span class="sr" data-i18n="find">스크립트에서 찾기</span><input id="q" type="search" data-i18n-ph="find" placeholder="스크립트에서 찾기"></label>
<article id="tx">
{body}
</article></main>
<script src="transcript.js"></script></body></html>'''


if __name__ == "__main__":
    api = YouTubeTranscriptApi()
    for n, (vid, slug, en, ko) in enumerate(LECTURES, 1):
        frags = [(int(s.start), s.text.replace("\n", " ").strip()) for s in api.fetch(vid).snippets]
        title = f"Stanford CS329A Self-Improving AI Agents | Part {n} | {en}"
        out = f"{n}_{slug}.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(page(n, vid, title, ko, en, paragraphs(frags)))
        print(f"{out}: {len(frags)} captions")
