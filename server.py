import glob, html, json, os, re, subprocess, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

# Claude Code 헤드리스(`claude -p`)로 동작: API 키 없이 로그인된 Claude Code 계정을 쓴다.
MODEL, EFFORT = "opus", "medium"
WORK = os.path.abspath(".tutor")  # claude 세션 저장 위치(cwd) + 강의별 system prompt 파일
os.makedirs(WORK, exist_ok=True)
SID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

LECTURES = {}  # id -> (title, transcript text without timestamps)
FILES = {}  # id -> transcript html
for f in sorted(glob.glob("[0-9]_*.html")):
    s = open(f, encoding="utf-8").read()
    title = html.unescape(re.search(r"<title>(.*?)</title>", s).group(1))
    paras = [html.unescape(re.sub(r"<[^>]+>", "", p)) for p in re.findall(r"<p><a [^>]*>\[[\d:]+\]</a>(.*?)</p>", s)]
    assert paras, f"{f}: 스크립트 문단을 찾지 못함"
    LECTURES[int(f[0])] = (title, "\n".join(p.strip() for p in paras))
    FILES[int(f[0])] = f
if not LECTURES:
    raise SystemExit("강의 스크립트가 없습니다. 먼저 `python3 fetch_transcripts.py`를 실행하세요. / No transcripts found — run `python3 fetch_transcripts.py` first.")
# 0 = 전체 과정: 9개 강의 전부 (~13만 토큰)
LECTURES[0] = ("전체 과정 (어디부터 볼지 정하기)", "\n\n".join(f"[강의: {t}]\n{x}" for _, (t, x) in sorted(LECTURES.items())))

RULES = """당신은 학생과 딱 4시간만 함께하는 선생님입니다. 그 뒤로는 다시 만날 수 없어요. 목표는 단 하나, 시간이 끝나기 전에 학생이 아래 강의 내용을 실제로 써먹을 수 있게 만드는 것입니다.
(과목: Stanford CS329A Self-Improving AI Agents. 강의 스크립트가 아래에 첨부되어 있습니다. 자동 자막이라 오타가 있으니 문맥으로 바로잡아 읽으세요.)

말투
- 학생 메시지 맨 앞의 [...] 태그는 시스템이 붙인 것입니다. 거기 적힌 답변 언어로만 답하세요.
- 한국어: 옆에서 같이 문제를 풀어 주는 선배처럼 자연스러운 해요체로 말하세요. "~이다/~하라" 같은 딱딱한 명령조, 번역투, 개조식 나열은 피하세요.
- English: warm, natural, conversational — like a sharp senior student sitting next to them. No stiff or textbook phrasing.
- 대개 10줄 안으로 짧게. 칭찬은 짧게, 피드백은 구체적으로. 제목(##)은 첫 안내처럼 꼭 필요할 때만 쓰세요.
- 수식은 $...$ (블록은 $$...$$)로, 코드는 백틱으로 감싸세요.

진행 규칙
1. 실전에 쓸 수 없는 이론은 설명하지 않습니다. 개념을 강의하지 말고, 목록만 던지지도 마세요.
2. 학생이 처음 '시작'(또는 'Start')이라고 하면 한 번만, 짧게 알려 주세요: ① 가장 먼저 배울 것 2~3개(순서와 이유 한 줄씩) ② 과감히 무시해도 되는 것 ③ 딱 한 번만 해 봐도 몇 달째 배우는 사람의 70%보다 앞서게 되는 연습 하나. 그리고 바로 첫 문제를 내세요. 첨부가 여러 강의라면 ①②를 강의 단위로 말하고, 남은 시간을 어떤 순서로 쓸지도 정해 주세요.
3. 개념을 설명하는 대신, 그 개념을 직접 써야 하고 학생이 실수하기 쉬운 구체적인 상황(작은 시나리오, 코드·설계·수식 한 조각, 판단 문제)에 바로 놓아 주세요. 문제는 한 번에 하나만.
4. 학생이 틀리면 정답을 알려 주지 마세요. 학생의 논리가 어디서 어긋났는지 스스로 발견하게 하는 질문(반례, 극단적인 경우, "그럼 X라면요?")을 하나만 던지세요. 힌트로 정답을 사실상 말해 버리면 안 됩니다.
5. 같은 문제에서 틀린 시도가 두 번 쌓이기 전에는 정답을 공개하지 않습니다. "모르겠어요", "답 알려 주세요"라고 해도 두 번 시도하기 전이라면 더 작은 질문으로 쪼개서 직접 해 보게 하세요. 틀릴 때마다 답변 첫 줄에 한국어는 「시도 k/2 ✗」, 영어는 「Attempt k/2 ✗」라고 쓰세요(k는 그 문제에서 틀린 횟수). k가 2가 되는 답변에서 정답과 왜 그렇게 틀리기 쉬운지를 짧게 알려 주고, 같은 함정을 담은 변형 문제를 내세요.
6. 맞혀도 끝이 아닙니다. 망설임 없이 정확하게 해낼 때까지 겉모습만 바꾸고 함정을 더한 변형 문제를 이어서 내세요. 맞히면 첫 줄을 「✓」로 시작하세요. 연속 두 문제를 막힘없이 맞히면 다음 핵심 기술로 넘어갑니다. 답이 맞아도 이유가 틀렸거나 찍은 것이면 맞힌 걸로 치지 않습니다.
7. 태그의 남은 시간에 맞춰 진도와 난이도를 조절하세요. 30분이 안 남았으면 가장 중요한 한 가지를 확실히 굳히는 데 집중하고, 0분이면 지금까지 익힌 것을 실전에서 쓰기 위한 체크리스트 세 줄로 마무리하세요.
8. 강의 내용에 근거한 문제만 냅니다. 강의에 없는 사실을 지어내지 마세요. 사용할 도구는 없으니 첨부된 스크립트만으로 답하세요.
9. 학생이 진행 방식을 직접 요청하면(예: 다시 설명해 달라, 제대로 익혔는지 확인해 달라, 자기가 설명해 보겠다) 그 요청의 지시를 위 규칙보다 우선해서 그대로 따르세요. 이때 설명을 요청받았다면 설명해도 됩니다. 요청한 활동이 끝나면 원래 진행으로 돌아오세요."""

# 브라우저에 내보낼 파일(화이트리스트)
STATIC = {"index.html": "text/html; charset=utf-8", "ui.css": "text/css; charset=utf-8", "transcript.js": "text/javascript; charset=utf-8"}
STATIC.update({f: "text/html; charset=utf-8" for f in FILES.values()})

PROMPTS = {}  # id -> system prompt file path
for k, (title, text) in LECTURES.items():
    PROMPTS[k] = os.path.join(WORK, f"system_{k}.txt")
    with open(PROMPTS[k], "w", encoding="utf-8") as fp:
        fp.write(f"{RULES}\n\n[첨부 강의: {title}]\n{text}")


def ask_claude(lecture, sid, text):
    """새 세션이면 --session-id, 이어가면 --resume. 반환: (응답, session_id)"""
    cmd = ["claude", "-p", "--safe-mode", "--tools", "", "--output-format", "json",
           "--model", MODEL, "--effort", EFFORT, "--system-prompt-file", PROMPTS[lecture]]
    cmd += ["--resume", sid] if sid else ["--session-id", str(uuid.uuid4())]
    # 프롬프트는 stdin으로: '-'로 시작하는 답이 플래그로 해석되지 않게
    p = subprocess.run(cmd, input=text, capture_output=True, text=True, cwd=WORK, timeout=600)
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError((p.stderr or p.stdout).strip()[-500:] or f"claude 종료 코드 {p.returncode}")
    if d.get("is_error"):
        raise RuntimeError(str(d.get("result") or d.get("subtype")))
    out = d["result"].strip()
    if not out:
        raise RuntimeError("empty response")
    return out, d["session_id"]


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def do_GET(self):
        if self.path == "/api/lectures":
            return self._json(200, {k: {"title": v[0], "file": FILES.get(k)} for k, v in LECTURES.items()})
        name = "index.html" if self.path in ("/", "/index.html") else self.path.lstrip("/")
        if name not in STATIC:
            return self._send(404, "not found", "text/plain")
        self._send(200, open(name, "rb").read(), STATIC[name])

    def do_POST(self):
        try:
            d = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            lecture, sid, text = int(d["lecture"]), d.get("sid"), str(d["text"]).strip()
            minutes, lang = max(0, int(d["minutes_left"])), d.get("lang", "ko")
            if lecture not in LECTURES or not text or lang not in ("ko", "en") or (sid and not SID.match(sid)):
                raise ValueError
        except (ValueError, KeyError, TypeError):
            return self._json(400, {"error": "bad_request"})
        tag = f"[남은 시간: {minutes}분 / 240분 · 답변 언어: 한국어]" if lang == "ko" else f"[Time left: {minutes} min / 240 · Reply in: English]"
        try:
            out, sid = ask_claude(lecture, sid, f"{tag}\n{text}")
        except FileNotFoundError:
            return self._json(500, {"error": "no_claude"})
        except subprocess.TimeoutExpired:
            return self._json(504, {"error": "timeout"})
        except RuntimeError as e:
            return self._json(502, {"error": "claude_error", "detail": str(e)})
        self._json(200, {"text": out, "sid": sid})


if __name__ == "__main__":
    print("http://localhost:8329")
    HTTPServer(("127.0.0.1", 8329), H).serve_forever()
