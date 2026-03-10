# itsmegram v2.0 - Instagram 데이터 수집 시스템 개선 PRD

## 📋 문서 개요

| 항목 | 내용 |
|------|------|
| **버전** | v2.0 |
| **작성일** | 2026-03-10 |
| **작성자** | itsmegram 개발팀 |
| **상태** | Draft |
| **목적** | Instaloader 대체 및 데이터 수집 시스템 개선 |

---

## 1. 🎯 문제 정의 (Problem Statement)

### 1.1 현재 상황
- **도구**: Instaloader 라이브러리 사용 중
- **문제**: Instagram에서 비공식 API 접근 차단
- **증상**: 401 Unauthorized, 429 Too Many Requests
- **영향**: 48시간 이상 지속적인 서비스 중단

### 1.2 해결 목표
- Instaloader 완전 제거
- 직접 HTTP 요청 기반 데이터 수집 구현
- 안정적인 Rate Limit 관리
- 300명 동시 요청 처리 가능한 아키텍처 구축

---

## 2. 💡 솔루션 개요 (Solution Overview)

### 2.1 핵심 전략: 3-Layer 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Queue System (요청 큐잉) - 선택적                  │
│  - 동시 요청 → 순차 처리 변환 (필요시에만 활성화)             │
│  - 초당 5-10개 요청 속도 제어                               │
│  - Redis 기반 분산 큐 (초기에는 인메모리 큐로 시작)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: HTTP Client (직접 요청)                          │
│  - Instagram web_profile_info API 직접 호출                 │
│  - JSON 응답 직접 파싱 (window._sharedData 대체)            │
│  - 필수 헤더 포함 (x-ig-app-id)                             │
│  - User-Agent 회전 + TLS fingerprint spoofing              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Cache System (캐싱)                              │
│  - 프로필 데이터: 30분 TTL                                  │
│  - 게시물 데이터: 30분 TTL                                  │
│  - Redis/Memory 기반                                       │
└─────────────────────────────────────────────────────────────┘
```

**⚠️ 중요 변경사항**: `window._sharedData` 파싱은 2024-2025년 기준 Instagram에서 제거되었습니다. `web_profile_info` API를 사용합니다.

### 2.2 처리 흐름

```
사용자 요청 (300명 동시)
    ↓
[Queue Manager] 요청 등록
    ↓
[Rate Limiter] 초당 5-10개 속도 제어
    ↓
[Cache Check] 캐시된 데이터 확인
    ├── Hit → 즉시 반환
    └── Miss → HTTP 요청
              ↓
        [HTTP Client] Instagram 웹 요청
              ↓
        [Parser] HTML → JSON 파싱
              ↓
        [Cache Store] 결과 캐싱
              ↓
        [Response] 데이터 반환
```

---

## 3. 🏗️ 기술 아키텍처 (Technical Architecture)

### 3.1 시스템 구성도

```
itsmegram-v2/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── instagram_scraper.py    # 새로운 스크래퍼 (instaloader 대체)
│   │   │   ├── queue_manager.py        # 요청 큐 관리
│   │   │   ├── rate_limiter.py         # 속도 제어
│   │   │   └── cache_service.py        # 캐싱 (기존 활용)
│   │   ├── clients/
│   │   │   └── http_client.py          # HTTP 요청 클라이언트
│   │   ├── parsers/
│   │   │   └── instagram_parser.py     # HTML/JSON 파서
│   │   └── models/
│   │       └── schemas.py              # 기존 모델 활용
│   └── requirements.txt                # instaloader 제거
```

### 3.2 사용 기술 스택

| 구성요소 | 기술 | 버전 | 목적 |
|----------|------|------|------|
| HTTP Client | httpx + curl_cffi | >=0.27.0 | 비동기 HTTP 요청, TLS spoofing |
| JSON Parser | stdlib json | - | API 응답 파싱 |
| Queue | asyncio.Queue / Redis + rq | >=1.15.0 | 작업 큐 관리 (단계적 도입) |
| Cache | Redis | >=5.0.0 | 데이터 캐싱 |
| Rate Limit | slowapi + Token Bucket | 기존 유지 | API Rate Limiting |
| TLS Spoofing | curl_cffi | >=0.6.0 | Instagram TLS fingerprinting 회피 |

### 3.3 제거 대상 (Instaloader 완전 제거)

#### A. 의존성 제거
**파일**: `backend/requirements.txt`
```diff
- # Instagram 데이터 수집
- instaloader==4.14
```

#### B. 코드 제거/변경

| 파일 | 라인 | 현재 내용 | 조치 |
|------|------|----------|------|
| `backend/app/services/instagram_service.py` | 3 | docstring "Instaloader를 사용하여..." | **변경** |
| `backend/app/services/instagram_service.py` | 11 | `import instaloader` | **제거** |
| `backend/app/services/instagram_service.py` | 12 | `from instaloader import Instaloader, Profile, Post` | **제거** |
| `backend/app/services/instagram_service.py` | 13-18 | `from instaloader.exceptions import ...` | **제거** |
| `backend/app/services/instagram_service.py` | 36 | docstring "Instaloader를 사용한..." | **변경** |
| `backend/app/services/instagram_service.py` | 42 | `self._loader: Optional[Instaloader]` | **제거** |
| `backend/app/services/instagram_service.py` | 45-63 | `_get_loader()` 메서드 (Instaloader 초기화) | **제거** |
| `backend/app/services/instagram_service.py` | 134-139 | `run_in_executor + Profile.from_username()` | **변경** (httpx 사용) |
| `backend/app/services/instagram_service.py` | 176-182 | `ProfileNotExistsException 처리` | **변경** (HTTP status 코드 기반) |
| `backend/app/services/instagram_service.py` | 180-182 | `TooManyRequestsException 처리` | **변경** (HTTP 429 처리) |
| `backend/app/utils/logger.py` | 97 | `logging.getLogger("instaloader")` | **제거** |

#### C. 새로운 파일 생성

| 파일 | 설명 |
|------|------|
| `backend/app/clients/http_client.py` | HTTP 요청 클라이언트 (httpx 기반) |
| `backend/app/parsers/instagram_parser.py` | HTML/JSON 파서 (BeautifulSoup 기반) |
| `backend/app/services/queue_manager.py` | 요청 큐 관리 (Redis 기반) |
| `backend/app/services/rate_limiter.py` | Rate limiting (토큰 버킷) |

#### D. 추가 의존성

```
# requirements.txt에 추가
httpx>=0.27.0           # 비동기 HTTP 클라이언트
curl_cffi>=0.6.0        # TLS fingerprint spoofing (Instagram 차단 회피)
```

**참고**: `beautifulsoup4`와 `lxml`은 더 이상 필요하지 않음 (HTML 파싱 → JSON API 직접 호출)

**의존성 제거**:
```diff
- beautifulsoup4>=4.12.0  # HTML 파싱 불필요
- lxml>=4.9.0            # BS4 파서 불필요
```

---

### 3.4 완전 교체 파일: `instagram_service.py`

**현재**: Instaloader 기반 스크래퍼
**변경 후**: HTTP + Parser + Queue + Cache 기반 스크래퍼

**핵심 변경점**:
1. `Instaloader` 인스턴스 변수 제거
2. `httpx.AsyncClient` 인스턴스 변수 추가
3. 모든 메서드에서 Instaloader 관련 코드 제거
4. HTTP 요청 → 파싱 → 캐싱 흐름으로 변경
5. Queue Manager 통합 (비동기 처리)

---

## 4. 🔧 상세 구현 (Implementation Details)

### 4.1 HTTP Client 모듈

**파일**: `backend/app/clients/http_client.py`

```python
# 핵심 기능
- Base URL: https://www.instagram.com/api/v1/users/web_profile_info/
- Query Param: username={username}
- Headers:
  * 필수: x-ig-app-id: 936619743392459
  * 회전 User-Agent, Accept-Language
  * Referer: https://www.instagram.com/
- Timeout: 10초 (연결), 30초 (읽기)
- Retry: 3회 (exponential backoff with jitter)
- Cookie: 선택적 세션 쿠키
```

**TLS Fingerprint Spoofing** (필수):
- `httpx` 기본 설정은 Python 클라이언트로 탐지됨
- `curl_cffi` 또는 TLS spoofing 적용 필요
- Instagram은 TLS 핸드셰이크 패턴으로 봇을 감지

**User-Agent 회전 목록**:
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    # 최소 10개 다양한 브라우저/OS 조합
]
```

**Exponential Backoff 전략**:
```python
# 429 응답 시 지연 시간
retry_delays = [5, 10, 30, 60]  # 초 단위
# Jitter 추가: random(0, delay * 0.1)  # 불규칙한 패턴으로 봇 탐지 회피
```

### 4.2 Instagram Parser 모듈

**파일**: `backend/app/parsers/instagram_parser.py`

**⚠️ 중요**: `window._sharedData` 파싱은 2024-2025년 기준 Instagram에서 제거되었습니다.

**데이터 추출 전략 (업데이트됨)**:
```
1. web_profile_info API 직접 호출
   GET https://www.instagram.com/api/v1/users/web_profile_info/?username={username}
   Headers: x-ig-app-id: 936619743392459

2. JSON 응답 직접 파싱 (HTML 파싱 불필요)

3. 응답 구조:
   {
     "data": {
       "user": {
         "username": "...",
         "full_name": "...",
         "biography": "...",
         ...
       }
     }
   }
```

**주요 파싱 필드** (응답 경로 업데이트):
| 필드 | JSON 경로 | 필수 |
|------|-----------|------|
| username | data.user.username | O |
| full_name | data.user.full_name | O |
| biography | data.user.biography | O |
| followers | data.user.edge_followed_by.count | O |
| following | data.user.edge_follow.count | O |
| posts_count | data.user.edge_owner_to_timeline_media.count | O |
| profile_pic | data.user.profile_pic_url_hd | O |
| is_private | data.user.is_private | O |
| is_verified | data.user.is_verified | O |

**Fallback 전략**:
- 401/403 응답 시: 세션 쿠키 또는 인증 토큰 갱신
- 404 응답 시: 사용자 존재하지 않음 처리
- 429 응답 시: Exponential backoff + jitter 적용

### 4.3 Queue Manager 모듈 (단순화된 버전)

**파일**: `backend/app/services/queue_manager.py`

**설계 원칙**: 과도한 엔지니어링 방지를 위해 단계적 도입

**Phase 1: 인메모리 큐 (초기 구현)**
```python
# 간단한 asyncio.Queue 기반
MAX_CONCURRENT = 5      # 동시 처리 개수
REQUESTS_PER_SECOND = 5 # 초당 요청 수
MAX_QUEUE_SIZE = 100    # 최대 대기열 크기 (과부하 방지)

# 100개 초과 시: "현재 서버가 바쁩니다. 잠시 후 다시 시도해주세요."
```

**Phase 2: Redis 기반 큐 (확장시)**
```python
# 실제 300명 동시 요청 필요성 검증 후 도입
# Redis + rq 사용
BATCH_SIZE = 300        # 최대 대기열 크기
```

**큐 상태**:
```python
class QueueStatus:
    PENDING = "pending"       # 대기 중
    PROCESSING = "processing" # 처리 중
    COMPLETED = "completed"   # 완료
    FAILED = "failed"         # 실패
    REJECTED = "rejected"     # 큐 초과로 거부
```

**API 인터페이스**:
```python
async def enqueue_analysis(username: str) -> Optional[str]:
    """
    분석 요청을 큐에 등록
    Returns: job_id (성공), None (큐 초과)
    """

async def get_queue_position(job_id: str) -> Optional[int]:
    """대기열 순서 조회"""

async def get_queue_status(job_id: str) -> QueueStatus:
    """작업 상태 조회"""

async def should_queue() -> bool:
    """현재 큐가 필요한 상황인지 판단 (큐 크기 > 10)"""
```

### 4.4 Rate Limiter 모듈

**파일**: `backend/app/services/rate_limiter.py`

**토큰 버킷 알고리즘 (개선)**:
```python
# 설정
TOKENS_PER_SECOND = 5      # 초당 생성 토큰
BUCKET_SIZE = 10           # 최대 토큰 보유량
JITTER_RANGE = (0.1, 0.3)  # 랜덤 지터 범위 (초)

# 동작
- 각 요청은 1개 토큰 소모
- 토큰 부족 시 대기
- 초과 요청은 자동 지연
- 지터 추가: 고정된 간격 패턴 회피 (봇 탐지 방지)
```

**Adaptive Rate Limiting** (Instagram 응답 기반):
```python
# Instagram 응답에 따라 동적 조정
if response.status == 429:
    TOKENS_PER_SECOND = max(1, TOKENS_PER_SECOND - 1)  # 감소
    BUCKET_SIZE = max(5, BUCKET_SIZE - 2)
    COOLDOWN_MINUTES = 5

if consecutive_successes > 10:
    TOKENS_PER_SECOND = min(10, TOKENS_PER_SECOND + 0.5)  # 점진적 증가
```

**Lua Script (Redis 기반 - Atomic)**:
```lua
-- Token Bucket with Atomic Operation
local key = KEYS[1]
local tokens_key = key .. ":tokens"
local timestamp_key = key .. ":timestamp"
local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
-- ... atomic token bucket logic
```

### 4.5 캐싱 전략

**캐시 키 구조**:
```
profile:{username}     → 프로필 데이터 (TTL: 30분)
posts:{username}:n     → 게시물 n개 (TTL: 30분)
queue:{job_id}         → 큐 상태 (TTL: 1시간)
```

**캐시 우선순위**:
1. Memory Cache (LRU) - 1차
2. Redis Cache - 2차

---

## 5. 📡 API 명세 (API Specification)

### 5.1 새로운/변경된 엔드포인트

#### POST /api/v1/analyze (기존 유지)
**변경사항**: 내부 로직만 변경, 인터페이스 동일

#### GET /api/v1/queue/{job_id}/status (신규)
```json
// Response
{
  "job_id": "job_abc123",
  "status": "processing",
  "queue_position": 27,
  "estimated_wait_seconds": 54,
  "username": "example_user",
  "created_at": "2026-03-10T10:00:00Z"
}
```

#### GET /api/v1/queue/status (신규 - 전체 큐 상태)
```json
// Response
{
  "total_pending": 150,
  "total_processing": 5,
  "total_completed": 1200,
  "average_wait_seconds": 45,
  "processing_rate": "5/sec"
}
```

### 5.2 에러 응답

```json
{
  "error": "RATE_LIMITED_BY_INSTAGRAM",
  "message": "Instagram에서 일시적으로 요청을 차단했습니다. 잠시 후 다시 시도해주세요.",
  "retry_after_seconds": 300,
  "job_id": "job_abc123"
}
```

---

## 6. 🎨 프론트엔드 변경사항 (Frontend Changes)

### 6.1 UI 개선

#### 분석 진행 상태 개선
```
[기존]
"분석 중..." → 무한 로딩

[변경]
"대기열에서 대기 중... (27/300)"
→ "데이터 수집 중... (최대 1분 소요)"
→ "AI 분석 중..."
→ "완료!"
```

#### 새로운 컴포넌트
- `QueueStatus.tsx`: 대기열 상태 표시
- `EstimatedWaitTime.tsx`: 예상 대기 시간

### 6.2 API 연동

```typescript
// 새로운 API 함수
async function getQueueStatus(jobId: string): Promise<QueueStatus>
async function getQueuePosition(jobId: string): Promise<number>
```

---

## 7. ⚡ 성능 목표 (Performance Goals)

### 7.1 처리량

| 시나리오 | 목표 | 설명 |
|----------|------|------|
| 단일 요청 | < 5초 | 캐시 Miss 시 |
| 단일 요청 | < 100ms | 캐시 Hit 시 |
| 300명 처리 | < 60초 | 초당 5개 기준 |
| 큐 대기 | < 120초 | 최대 대기 시간 |

### 7.2 가용성

| 지표 | 목표 |
|------|------|
| 성공률 | > 95% |
| 캐시 Hit률 | > 60% |
| Instagram 차단 | < 1% |

---

## 8. 🔒 보안 및 안전장치 (Security & Safety)

### 8.1 Rate Limiting (다중 레벨)

```
Level 1: IP 기반 (SlowAPI) - 100 req/min
Level 2: 사용자 기반 - 5 analysis/hour
Level 3: Instagram 요청 - 5 req/sec (전역)
```

### 8.2 회복 메커니즘

**Instagram 차단 감지 시 (개선)**:
```python
if response.status == 429:
    # 1. Exponential backoff with jitter
    delay = min(300, (2 ** retry_count) * 5)  # 5, 10, 20, 40... 최대 300초
    jitter = random.uniform(0, delay * 0.1)   # 불규칙한 패턴으로 봇 탐지 회피
    await asyncio.sleep(delay + jitter)

    # 2. Rate Limit 동적 조정
    TOKENS_PER_SECOND = max(1, TOKENS_PER_SECOND - 1)

    # 3. 프록시 전환 (프록시 풀 사용 시)
    if proxy_pool.available:
        current_proxy = proxy_pool.rotate()

    # 4. 관리자 알림
    await notify_admin(f"Instagram rate limit: {username}")

    # 5. 사용자에게 재시도 안내
    return {"error": "RATE_LIMITED", "retry_after": delay + jitter}

# 403 Forbidden (TLS/Header 탐지)
if response.status == 403:
    # 1. curl_cffi로 전환하여 TLS fingerprint spoofing
    # 2. User-Agent 재선택
    # 3. 헤더 검증 (x-ig-app-id 포함 여부)
```

**Circuit Breaker 패턴**:
```python
# 연속 실패 시 일시적 서비스 중단
if consecutive_failures > 10:
    circuit_breaker.open()  # 5분간 Instagram 요청 중단
    return {"error": "SERVICE_UNAVAILABLE", "retry_after": 300}
```

### 8.3 모니터링

**메트릭**:
- 큐 크기 (queue_size)
- 처리 시간 (processing_duration)
- Instagram 에러율 (instagram_error_rate)
- 캐시 Hit률 (cache_hit_ratio)

---

## 9. 📝 마이그레이션 계획 (Migration Plan)

### Phase 1: 준비 (1일)
- [ ] PRD 리뷰 및 승인
- [ ] 개발 브랜치 생성 (`feature/v2-scraper`)
- [ ] Redis 인프라 확인

### Phase 2: 개발 (2-3일)
- [ ] HTTP Client 구현
- [ ] Parser 구현
- [ ] Queue Manager 구현
- [ ] Rate Limiter 구현
- [ ] 기존 서비스 연동

### Phase 3: 테스트 (1-2일)
- [ ] 단위 테스트
- [ ] 통합 테스트
- [ ] 부하 테스트 (300명 동시 요청)

### Phase 4: 배포 (1일)
- [ ] 스테이징 배포
- [ ] 프로덕션 배포
- [ ] 모니터링 설정
- [ ] 롤백 계획 수립

### Phase 5: Instaloader 완전 제거 및 정리

**⚠️ 주요 변경사항**:
- `window._sharedData` 파싱은 사용하지 않음 (2024-2025년 기준 Instagram에서 제거됨)
- `beautifulsoup4`, `lxml`은 불필요 (HTML 파싱 대신 JSON API 사용)
- instagrapi는 사용하지 않음 (직접 HTTP 구현)
- [ ] `requirements.txt`에서 `instaloader==4.14` 제거
- [ ] `httpx>=0.27.0`, `curl_cffi>=0.6.0` 추가
- [ ] `backend/app/utils/logger.py`에서 instaloader 로거 설정 제거 (라인 97)
- [ ] `backend/app/services/instagram_service.py` 완전 재작성:
  - [ ] Instaloader import 문 제거
  - [ ] `Instaloader` 관련 인스턴스 변수 제거 (`self._loader`)
  - [ ] `_get_loader()` 메서드 제거
  - [ ] `Profile.from_username()` 호출을 web_profile_info API로 변경
  - [ ] `ProfileNotExistsException` → HTTP 404 체크로 변경
  - [ ] `TooManyRequestsException` → HTTP 429 체크로 변경
  - [ ] 모든 메서드 docstring 업데이트
  - [ ] `x-ig-app-id: 936619743392459` 헤더 추가
- [ ] 신규 파일 생성:
  - [ ] `backend/app/clients/__init__.py`
  - [ ] `backend/app/clients/http_client.py` (curl_cffi 적용)
  - [ ] `backend/app/parsers/__init__.py`
  - [ ] `backend/app/parsers/instagram_parser.py` (JSON API 응답 파싱)
  - [ ] `backend/app/services/queue_manager.py` (asyncio.Queue 기반, 단순화)
  - [ ] `backend/app/services/rate_limiter.py` (adaptive token bucket)
- [ ] 문서 업데이트
- [ ] 성능 리포트 작성

---

## 10. ⚠️ 위험 요소 및 대응 (Risks & Mitigations)

| 위험 | 가능성 | 영향 | 대응책 |
|------|--------|------|--------|
| Instagram API 변경 | 중간 | 높음 | web_profile_info API 모니터링 + 빠른 패치 |
| TLS Fingerprinting 차단 | 높음 | 높음 | curl_cffi 사용 + 프록시 풀 구축 |
| JavaScript Challenge | 중간 | 중간 | headless browser fallback (Playwright) |
| IP 차단 | 높음 | 높음 | Rate Limiting + Exponential backoff + 프록시 회전 |
| 300명 동시 요청 시 타임아웃 | 낮음 | 중간 | 큐 크기 제한(100) + Graceful rejection |
| 파싱 실패 | 낮음 | 중간 | JSON-LD Fallback + 에러 처리 |
| Redis 장애 | 낮음 | 높음 | Memory Cache Fallback + 인메모리 큐 |

---

## 11. 📊 성공 기준 (Success Criteria)

- [ ] Instaloader 완전 제거
- [ ] 300명 동시 요청 처리 가능
- [ ] 평균 응답 시간 < 60초
- [ ] Instagram 차단 없이 안정적 수집
- [ ] 기존 API 인터페이스 유지
- [ ] 95% 이상의 성공률

---

## 12. 🔗 참고 자료 (References)

- [Instagram Web Structure](https://developers.facebook.com/docs/instagram)
- [httpx Documentation](https://www.python-httpx.org/)
- [Redis Queue (RQ)](https://python-rq.org/)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)

---

**작성 완료**: 2026-03-10
**다음 단계**: 개발 브랜치 생성 및 Phase 1 시작
