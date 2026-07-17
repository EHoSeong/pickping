"""키워드별 상품을 수집하고 '비교 가치'를 갖도록 가공한다.

단순 나열이 아니라 통계·가격대별 추천·선정근거를 만들어
검색엔진이 '유용한 콘텐츠'로 인식하도록 구조화하는 것이 핵심.
"""
from statistics import median


def _affiliate_link(product, coupang_id):
    """쿠팡 검색 링크 생성(트래킹 코드는 없음). 쿠팡파트너스 ID가 없으면 네이버 원본."""
    if coupang_id and not coupang_id.startswith("여기에"):
        from urllib.parse import quote
        return f"https://www.coupang.com/np/search?q={quote(product['title'])}"
    return product["link"]


def build_page_data(entry, products, coupang_id="", top_n=10, coupang_creds=None):
    """수집된 상품으로 페이지 렌더링용 데이터 구조를 만든다.

    coupang_creds: {"access_key", "secret_key", "sub_id"(선택)} — 있으면 쿠팡 검색
    링크를 Open API로 실제 트래킹되는 딥링크로 변환한다. 없으면 트래킹 없는 검색 링크.
    """
    # 가격 오름차순 정렬 후 상위 N개
    ranked = sorted(products, key=lambda p: p["price"])[:top_n]
    for i, p in enumerate(ranked, 1):
        p["rank"] = i
        p["affiliate"] = _affiliate_link(p, coupang_id)

    if coupang_creds and coupang_creds.get("access_key") and coupang_creds.get("secret_key"):
        from . import coupang_client

        tracked = coupang_client.create_deeplinks(
            [p["affiliate"] for p in ranked],
            coupang_creds["access_key"],
            coupang_creds["secret_key"],
            sub_id=coupang_creds.get("sub_id"),
        )
        for p, link in zip(ranked, tracked):
            p["affiliate"] = link

    prices = [p["price"] for p in ranked]
    brands = sorted({p["brand"] for p in ranked if p["brand"]})
    malls = sorted({p["mall"] for p in ranked if p["mall"]})

    # 가격대별 대표 추천(저가/중가/고가) — 단순 최저가가 아닌 '가치' 관점
    picks = {}
    if ranked:
        picks = {
            "budget": ranked[0],                       # 가장 저렴
            "balanced": ranked[len(ranked) // 2],      # 중간 가격대
            "premium": ranked[-1],                     # 상위 가격대
        }

    stats = {
        "count": len(ranked),
        "min": min(prices) if prices else 0,
        "max": max(prices) if prices else 0,
        "median": int(median(prices)) if prices else 0,
        "brands": brands,
        "malls": malls,
    }

    return {
        "keyword": entry["keyword"],
        "title": entry.get("title", entry["keyword"] + " 추천"),
        "category": entry.get("category", ""),
        "slug": _slugify(entry.get("title", entry["keyword"])),
        "products": ranked,
        "picks": picks,
        "stats": stats,
        "faqs": _build_faqs(entry, stats),
    }


def _build_faqs(entry, stats):
    """키워드·데이터 기반 FAQ 자동 생성(콘텐츠 깊이 확보)."""
    kw = entry["keyword"]
    faqs = [
        {
            "q": f"{kw} 가격은 보통 얼마인가요?",
            "a": f"이 비교에서 {kw}의 가격은 최저 {stats['min']:,}원부터 "
                 f"최고 {stats['max']:,}원까지이며, 중간값은 약 {stats['median']:,}원입니다.",
        },
        {
            "q": f"저렴한 {kw}를 고르면 품질이 별로일까요?",
            "a": "가격이 낮다고 무조건 나쁜 건 아닙니다. 다만 브랜드·판매처의 신뢰도와 "
                 "구매 후기를 함께 확인하는 것을 권장합니다.",
        },
    ]
    if stats["brands"]:
        faqs.append(
            {
                "q": f"어떤 브랜드의 {kw}가 있나요?",
                "a": "이 비교에 포함된 주요 브랜드는 "
                     + ", ".join(stats["brands"][:6]) + " 등입니다.",
            }
        )
    return faqs


def _slugify(text):
    """URL/파일명용 슬러그. 한글은 유지하고 공백·특수문자만 하이픈으로."""
    import re
    slug = text.strip().lower()
    slug = re.sub(r"[\s/\\]+", "-", slug)
    slug = re.sub(r"[^0-9a-z가-힣\-]", "", slug)
    return slug or "page"
