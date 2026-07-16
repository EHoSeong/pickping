"""PickPing — 롱테일 키워드 자동 수집기 진입점.

사용법:
    python find_keywords.py --demo           # 네트워크 없이 로직 검증
    python find_keywords.py                   # seeds.json → keywords.json 생성
    python find_keywords.py --merge           # 기존 keywords.json 에 병합
    python find_keywords.py --depth 2 --max 500
"""
import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src import keyword_finder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEYWORDS_PATH = os.path.join(BASE_DIR, "keywords.json")


def _load(name):
    with open(os.path.join(BASE_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _mock_fetch(query):
    """데모용 가짜 자동완성(수식어 6종 부착)."""
    return [f"{query} {m}" for m in ("추천", "가성비", "브랜드", "저렴한", "후기", "순위")]


def main():
    parser = argparse.ArgumentParser(description="PickPing 키워드 자동 수집기")
    parser.add_argument("--demo", action="store_true", help="네트워크 없이 로직 검증")
    parser.add_argument("--merge", action="store_true", help="기존 keywords.json 에 병합")
    parser.add_argument("--depth", type=int, default=1, help="자동완성 재귀 깊이(기본 1)")
    parser.add_argument("--max", type=int, default=0, help="최대 키워드 수(0=무제한)")
    args = parser.parse_args()

    if args.demo:
        seeds = [
            {"seed": "무선 이어폰", "category": "디지털"},
            {"seed": "캠핑 의자", "category": "캠핑"},
        ]
        fetch = _mock_fetch
        print("=== 데모 모드 (샘플 자동완성) ===")
    else:
        seeds = _load("seeds.json")
        fetch = keyword_finder.autocomplete
        print(f"=== 시드 {len(seeds)}개 확장 (depth={args.depth}) ===")

    found = keyword_finder.expand(seeds, depth=args.depth, fetch=fetch)

    # 출력 형태(build.py 호환): keyword, title, category
    items = [
        {"keyword": f["keyword"], "title": f["title"], "category": f["category"]}
        for f in found
    ]

    if args.merge and os.path.exists(KEYWORDS_PATH):
        existing = _load("keywords.json")
        seen = {e["title"] for e in existing}
        merged = existing + [it for it in items if it["title"] not in seen]
        items = merged
        print(f"기존 {len(existing)}개에 병합")

    if args.max and len(items) > args.max:
        items = items[: args.max]
        print(f"최대 {args.max}개로 제한")

    with open(KEYWORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\n생성: 키워드 {len(items)}개 → keywords.json")
    # 미리보기
    for it in items[:12]:
        print(f"  · {it['title']}  (검색어: {it['keyword']})")
    if len(items) > 12:
        print(f"  ... 외 {len(items) - 12}개")


if __name__ == "__main__":
    main()
