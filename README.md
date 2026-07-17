# PickPing — 상품 추천·비교 자동 생성 사이트 (Programmatic SEO)

키워드별로 네이버 쇼핑 데이터를 수집해 **"OO 추천 TOP10" 비교 페이지를 대량 자동 생성**하는 정적 사이트 빌더.
구글 검색 유입 → 쿠팡파트너스 제휴/애드센스로 수익화하는 **구축 후 저유지형** 프로젝트.

## 핵심 설계 (왜 이렇게 만들었나)

> ⚠️ 요즘 구글은 "데이터만 긁어 찍어낸 저품질 페이지"를 강하게 페널티합니다.
> 그래서 각 페이지에 **비교 가치를 구조화**해 넣었습니다:
> 데이터 기반 인트로 · 가격대별 추천(가성비/밸런스/프리미엄) · 비교표 · 선정 기준 · FAQ · JSON-LD.
> 이게 "색인되고 살아남는" 핵심입니다.

## 빠른 시작

```bash
pip install -r requirements.txt
python build.py --demo     # API 키 없이 샘플로 사이트 생성 → dist/ 확인
```

`dist/index.html`을 브라우저로 열어보면 완성된 사이트가 보입니다.

## 실제 운영

### 1. 네이버 검색 API 키
https://developers.naver.com/apps/#/register → '검색' API 등록 → Client ID/Secret

### 2. 설정
```bash
copy config.example.json config.json     # 네이버 키·사이트명·쿠팡파트너스ID
copy keywords.example.json keywords.json # 생성할 키워드 목록
```

`keywords.json` 항목: `keyword`(검색어), `title`(페이지 제목), `category`(분류)

### 3. 빌드
```bash
python build.py     # dist/ 에 정적 사이트 생성
```

### 4. 배포 (무료)
- **Cloudflare Pages** 또는 **Vercel**에 `dist/` 연결 → 자동 배포·HTTPS
- 도메인 연결 (선택, 연 1~2만원)

### 5. 수익화 세팅
- **쿠팡파트너스** 가입(사이트 있으면 승인 쉬움) → `coupang_partners_id` 입력
  - 이것만으로는 링크에 트래킹 코드가 안 붙어 수익이 안 잡힘. 실제 정산을 받으려면
    파트너스 사이트 우측 상단 **Open API** 메뉴에서 `ACCESS KEY`/`SECRET KEY`를 추가로
    발급받아 `config.json`의 `coupang.access_key`/`coupang.secret_key`에 입력한다.
    (GitHub Actions 자동 빌드는 `COUPANG_ACCESS_KEY`/`COUPANG_SECRET_KEY` Secrets로 주입)
  - 키를 넣으면 빌드 시 쿠팡 검색 링크가 딥링크 API(`link.coupang.com/a/...`)로 자동
    변환되어 트래킹된다. 키가 없으면 트래킹 없는 검색 링크로 폴백(빌드는 실패하지 않음).
- **구글 애드센스** 신청 → 승인 후 광고 코드 삽입
- **구글 서치콘솔**에 사이트 등록 + `sitemap.xml` 제출 → 색인 유도

### 6. 자동화 (완전 방치화)
- GitHub Actions cron으로 주기적 `python build.py` → 가격·순위 자동 갱신
- 한 번 세팅하면 사람 손 없이 최신 상태 유지

## 정직한 로드맵 (기대치 관리)

| 시점 | 현실 |
|---|---|
| 0~1개월 | 사이트 만들고 키워드 50~200개 확보. **수익 0** (색인 대기) |
| 2~4개월 | 구글 색인·롱테일 랭킹 시작. 트래픽 조금씩 |
| 4~8개월 | 트래픽 쌓이면 제휴·광고 수익 발생 시작 |

**핵심 성공 요인 = 키워드 물량.** 페이지 10개론 안 됩니다. **좋은 롱테일 키워드 수백~수천 개**를 꾸준히 넣는 게 승부처예요. (예: "3만원대 무선이어폰", "캠핑 초보 의자" 같은 구체적 검색어)

## 구조
```
pickping/
├─ build.py              빌드 진입점 (--demo / 실제)
├─ config.example.json   사이트·API·쿠팡ID 설정
├─ keywords.example.json 생성할 키워드 목록 = 페이지들
├─ src/
│  ├─ naver_client.py    네이버 쇼핑 검색 API
│  ├─ coupang_client.py  쿠팡파트너스 딥링크(트래킹 링크) 변환
│  ├─ collector.py       비교 가치 가공(통계·픽·FAQ·슬러그)
│  └─ generator.py       Jinja2 렌더 + sitemap
├─ templates/            base / listing / index
└─ dist/                 생성된 정적 사이트 (배포 대상)
```
