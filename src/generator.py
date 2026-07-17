"""Jinja2로 정적 HTML 페이지를 생성해 dist/ 에 쓴다."""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
DIST_DIR = os.path.join(BASE_DIR, "dist")


def _env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["won"] = lambda v: f"{int(v):,}원"
    return env


def generate_site(pages, site):
    """페이지 데이터 목록으로 전체 정적 사이트를 생성한다."""
    site = dict(site)
    site["base_url"] = (site.get("base_url") or "").strip().rstrip("/")

    os.makedirs(DIST_DIR, exist_ok=True)
    env = _env()

    listing_tpl = env.get_template("listing.html")
    for page in pages:
        html = listing_tpl.render(page=page, site=site)
        out = os.path.join(DIST_DIR, page["slug"] + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)

    # 인덱스
    index_tpl = env.get_template("index.html")
    with open(os.path.join(DIST_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_tpl.render(pages=pages, site=site))

    # sitemap.xml (색인 유도)
    _write_sitemap(pages, site)

    print(f"생성 완료: 페이지 {len(pages)}개 + index + sitemap → {DIST_DIR}")


def _write_sitemap(pages, site):
    base = site.get("base_url", "").rstrip("/")
    urls = [f"{base}/index.html"] + [f"{base}/{p['slug']}.html" for p in pages]
    body = "\n".join(
        f"  <url><loc>{u}</loc></url>" for u in urls
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )
    with open(os.path.join(DIST_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
