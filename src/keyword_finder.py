"""네이버 자동완성을 이용한 롱테일 키워드 대량 수집기.

시드 키워드 하나로 네이버 자동완성 제안어를 긁고, 그것을 다시 시드로
재귀 확장해 수백 개의 롱테일 검색어를 만든다. 각 검색어가 곧 한 페이지가 된다.

- 자동완성 API(ac.search.naver.com)는 키가 필요 없다(비공식 공개 엔드포인트).
- 상품 검색용 'keyword'(핵심 명사)와 SEO 타깃 'title'(자동완성 문구)을 분리한다.
"""
import re
import time

AC_URL = "https://ac.search.naver.com/nx/ac"

# 페이지 제목엔 살리되 상품 검색에선 제거할 수식어(코어 명사만 남기기 위함)
MODIFIERS = [
    "추천", "순위", "가성비", "저렴한", "인기", "브랜드", "후기", "비교",
    "베스트", "싼", "좋은", "종류", "TOP", "top", "고르는법", "고르는 법",
]
_MOD_RE = re.compile(r"\s*(?:" + "|".join(map(re.escape, MODIFIERS)) + r")\s*", re.I)

# 수집에서 제외할 잡음성 토큰(무관·비상품)
_NOISE = ("나무위키", "뜻", "영어로", "디시", "갤러리", "토렌트", "무료보기",
          "다시보기", "중고", "당근", "번개장터", "채용", "연봉", "위키")


def autocomplete(query, session=None):
    """네이버 자동완성 제안어 리스트를 반환."""
    import requests

    params = {
        "q": query, "st": "100", "frm": "nv", "ans": "2",
        "r_format": "json", "r_enc": "UTF-8", "r_unicode": "0",
    }
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.naver.com/"}
    getter = session.get if session else requests.get
    resp = getter(AC_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    out = []
    items = data.get("items") or []
    if items and items[0]:
        for row in items[0]:
            if row and row[0]:
                out.append(row[0].strip())
    return out


def core_of(phrase):
    """자동완성 문구에서 수식어를 떼어낸 상품 검색용 코어 명사."""
    core = _MOD_RE.sub(" ", phrase)
    core = re.sub(r"\s+", " ", core).strip()
    return core or phrase


def _title_of(phrase):
    return phrase if "추천" in phrase else phrase + " 추천"


def expand(seeds, depth=1, fetch=None, per_seed_limit=30, delay=0.25):
    """시드 목록을 자동완성으로 확장해 키워드 항목 리스트를 반환.

    반환 항목: {keyword(코어), title(SEO 제목), category, target(원 자동완성어)}
    """
    fetch = fetch or autocomplete
    seen_titles = set()
    seen_queries = set()
    results = []

    queue = [(s["seed"], s.get("category", ""), 0) for s in seeds]

    while queue:
        text, cat, d = queue.pop(0)
        if text in seen_queries:
            continue
        seen_queries.add(text)

        try:
            suggestions = fetch(text)
        except Exception as exc:  # 네트워크/차단 시 해당 시드만 건너뜀
            print(f"  [경고] '{text}' 자동완성 실패: {exc}")
            suggestions = []
        if delay and fetch is autocomplete:
            time.sleep(delay)

        for sug in suggestions[:per_seed_limit]:
            if len(sug) < 3 or any(n in sug for n in _NOISE):
                continue
            title = _title_of(sug)
            if title in seen_titles:
                continue
            seen_titles.add(title)
            results.append({
                "keyword": core_of(sug),
                "title": title,
                "category": cat,
                "target": sug,
            })
            # 다음 깊이로 재귀 확장
            if d < depth:
                queue.append((sug, cat, d + 1))

    return results
