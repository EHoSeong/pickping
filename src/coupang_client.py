"""쿠팡파트너스 Open API 클라이언트 (딥링크 변환).

가입 시 받는 파트너 ID(AF ID)와는 별개로, partners.coupang.com 우측 상단
'Open API' 메뉴에서 ACCESS KEY / SECRET KEY를 발급받아야 사용 가능하다.
공식 문서: https://developers.coupang.com/hc/ko/articles/360033396034
"""
import hashlib
import hmac
import time

DOMAIN = "https://api-gateway.coupang.com"
DEEPLINK_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"

# 문서상 1회 요청당 변환 가능한 URL 개수에 제한이 있어 안전하게 나눠 보낸다.
_BATCH_SIZE = 20


def _authorization(method, path_and_query, access_key, secret_key):
    signed_date = time.strftime("%y%m%d", time.gmtime()) + "T" + time.strftime("%H%M%S", time.gmtime()) + "Z"
    path, _, query = path_and_query.partition("?")
    message = signed_date + method + path + query
    signature = hmac.new(
        secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, "
        f"signed-date={signed_date}, signature={signature}"
    )


def create_deeplinks(urls, access_key, secret_key, sub_id=None):
    """URL 목록을 쿠팡파트너스 트래킹 딥링크(link.coupang.com/a/...)로 변환.

    키 미발급·네트워크 오류 등으로 변환에 실패한 URL은 원본을 그대로 반환해
    (트래킹은 안 되지만) 빌드가 중단되지 않게 한다.
    """
    import requests

    tracked = {}
    for i in range(0, len(urls), _BATCH_SIZE):
        batch = urls[i : i + _BATCH_SIZE]
        body = {"coupangUrls": batch}
        if sub_id:
            body["subId"] = sub_id
        headers = {
            "Authorization": _authorization("POST", DEEPLINK_PATH, access_key, secret_key),
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(DOMAIN + DEEPLINK_PATH, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            for item in resp.json().get("data", []):
                original = item.get("originalUrl")
                shortened = item.get("shortenUrl")
                if original and shortened:
                    tracked[original] = shortened
        except Exception as exc:  # 이 배치만 원본 링크로 폴백
            print(f"  [경고] 쿠팡 딥링크 변환 실패({len(batch)}건): {exc}")

    return [tracked.get(u, u) for u in urls]
