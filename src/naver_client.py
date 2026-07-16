"""네이버 쇼핑 검색 API 클라이언트 (PricePing 재활용 + 스펙 필드 확장).

공식 검색 API(무료, 일 25,000회)로 키워드별 상품 목록을 수집한다.
개발자센터에서 '검색' API 등록: https://developers.naver.com/apps/#/register
"""
import re

SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"
_TAG_RE = re.compile(r"<[^>]+>")


def _strip(text):
    clean = _TAG_RE.sub("", text or "")
    return clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def search_products(query, client_id, client_secret, display=40):
    """검색어로 상품 목록을 반환(가격·브랜드·카테고리 포함)."""
    import requests  # 데모 모드에서는 불필요하므로 지연 임포트

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {"query": query, "display": display, "sort": "sim"}
    resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    products = []
    for it in items:
        price = int(it.get("lprice") or 0)
        if price <= 0:
            continue
        products.append(
            {
                "title": _strip(it.get("title")),
                "price": price,
                "mall": it.get("mallName") or "기타",
                "brand": it.get("brand") or it.get("maker") or "",
                "category": it.get("category3") or it.get("category2") or "",
                "link": it.get("link") or "",
                "image": it.get("image") or "",
                "product_id": it.get("productId") or "",
            }
        )
    return products
