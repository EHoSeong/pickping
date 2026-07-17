"""PickPing — 상품 추천·비교 정적 사이트 빌더.

사용법:
    python build.py --demo   # API 키 없이 샘플 데이터로 사이트 생성 검증
    python build.py          # config.json / keywords.json 으로 실제 생성
"""
import argparse
import json
import os
import sys

# Windows 콘솔(cp949) 한글 출력 깨짐/크래시 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src import collector, generator, naver_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    with open(os.path.join(BASE_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def _demo_products(keyword):
    """샘플 상품(각 키워드 공통 형태). 실제 API 대체용."""
    base = abs(hash(keyword)) % 10000
    brands = ["삼성", "샤오미", "앤커", "브리츠", "노브랜드"]
    malls = ["베스트몰", "가전나라", "스마트샵", "쿠팡", "위메프"]
    out = []
    for i in range(12):
        out.append({
            "title": f"{keyword} 모델 {chr(65+i)} ({brands[i % 5]})",
            "price": 15000 + base % 5000 + i * 4300,
            "mall": malls[i % 5],
            "brand": brands[i % 5],
            "category": "샘플카테고리",
            "link": f"https://example.com/{keyword}/{i}",
            "image": "",
            "product_id": str(i),
        })
    return out


def main():
    parser = argparse.ArgumentParser(description="PickPing 상품 추천 사이트 빌더")
    parser.add_argument("--demo", action="store_true",
                        help="API 키 없이 샘플 데이터로 사이트 생성")
    parser.add_argument("--limit", type=int, default=0,
                        help="처음 N개 키워드만 빌드(테스트용, 0=전체)")
    args = parser.parse_args()

    if args.demo:
        site = {
            "name": "오늘의 추천픽",
            "base_url": "https://example.com",
            "description": "가격·브랜드를 한눈에 비교해 카테고리별 추천을 정리합니다.",
            "coupang_partners_id": "",
        }
        keywords = [
            {"keyword": "무선 블루투스 이어폰", "title": "무선 블루투스 이어폰 추천", "category": "디지털"},
            {"keyword": "경량 캠핑 의자", "title": "경량 캠핑 의자 추천", "category": "캠핑"},
        ]
        top_n, fetch = 10, 40
        fetch_products = _demo_products
        coupang_creds = None
        print("=== 데모 모드 (샘플 데이터, 실제 API 미사용) ===")
    else:
        config = _load("config.json")
        keywords = _load("keywords.json")
        site = config["site"]
        top_n = config.get("top_n", 10)
        fetch = config.get("fetch_count", 40)

        coupang_creds = config.get("coupang")

        def fetch_products(keyword):
            return naver_client.search_products(
                keyword,
                config["naver"]["client_id"],
                config["naver"]["client_secret"],
                display=fetch,
            )

    if args.limit and args.limit > 0:
        keywords = keywords[: args.limit]
        print(f"[제한] 처음 {args.limit}개 키워드만 빌드")

    pages = []
    for entry in keywords:
        products = fetch_products(entry["keyword"])
        if not products:
            print(f"[건너뜀] {entry['keyword']} — 상품 없음")
            continue
        page = collector.build_page_data(
            entry, products, site.get("coupang_partners_id", ""), top_n, coupang_creds
        )
        pages.append(page)
        print(f"[수집] {entry['keyword']}: {page['stats']['count']}개 "
              f"({page['stats']['min']:,}~{page['stats']['max']:,}원)")

    generator.generate_site(pages, site)


if __name__ == "__main__":
    main()
