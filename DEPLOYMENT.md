# itsmegram v2.0 배포 가이드

## 개요

이 문서는 itsmegram v2.0 (Instaloader 제거, HTTP 기반 스크래핑) 배포를 위한 가이드입니다.

## 주요 변경 사항

### v1.0 → v2.0
- **Instaloader 제거**: Instagram 직접 HTTP 요청 방식으로 대체
- **curl_cffi 추가**: 브라우저 지문 채취 우회를 위한 HTTP 클라이언트
- **Rate Limiter 추가**: Adaptive Token Bucket 알고리즘 적용
- **Queue Manager 추가**: 300명 동시 요청 처리 지원
- **Circuit Breaker 추가**: 연속 실패 시 자동 차단 및 복구
- **Metrics 수집**: 모니터링 및 알림 지원

## 배포 체크리스트

### 사전 확인사항

- [ ] Instaloader 완전 제거 확인 (`pip list | grep instaloader`)
- [ ] curl_cffi 설치 확인 (`pip list | grep curl_cffi`)
- [ ] Redis 연결 확인
- [ ] 환경 변수 설정 확인 (`.env` 파일)
- [ ] 통합 테스트 통과 (`pytest tests/integration/`)
- [ ] 부하 테스트 완료 (Locust 기준 300 concurrent)

### 환경 변수 설정

```bash
# .env 파일 예시
# Instagram
INSTAGRAM_RATE_LIMIT=5  # 초당 요청 수

# Redis
REDIS_URL=redis://localhost:6379/0

# AI
MOONSHOT_API_KEY=your_api_key_here

# 기타
LOG_LEVEL=INFO
DEBUG=false
```

## 롤백 계획

### 롤백 스크립트

```bash
#!/bin/bash
# rollback.sh - 배포 실패 시 롤백

echo "Rolling back to Instaloader version..."

# 1. Git 롤백
git checkout HEAD~15 -- backend/

# 2. 의존성 복구
pip install instaloader==4.14
pip uninstall curl_cffi -y

# 3. 서비스 재시작
sudo systemctl restart itsmegram

echo "Rollback completed"
```

### 롤백 조건

- 오류율 > 50% (1분 이상 지속)
- 응답 시간 > 60초 (평균)
- Instagram API 연결 불가 (5분 이상 지속)

## API 변경사항

### 새로운 엔드포인트

```
GET  /api/v1/queue/{job_id}/status    # 큐 작업 상태 조회
GET  /api/v1/queue/status             # 전체 큐 통계
GET  /api/v1/metrics                  # 시스템 메트릭
GET  /api/v1/metrics/health           # 헬스 체크
POST /api/v1/metrics/reset            # 메트릭 초기화
```

### 변경된 응답 형식

#### 분석 요청 (POST /api/v1/analyze)

```json
// 큐 활성화 시
{
  "report_id": "rep_abc123",
  "status": "processing",
  "message": "분석이 대기열에 추가되었습니다. (대기순번: 5번)",
  "estimated_time_seconds": 60,
  "check_url": "/api/v1/queue/job_abc123/status"
}

// 큐 비활성 시 (기존과 동일)
{
  "report_id": "rep_abc123",
  "status": "processing",
  "message": "분석이 시작되었습니다. 잠시 후 결과를 확인해주세요.",
  "estimated_time_seconds": 30,
  "check_url": "/api/v1/report/rep_abc123"
}
```

#### 에러 응답

```json
// Rate Limit (429)
{
  "error": "RATE_LIMITED_BY_INSTAGRAM",
  "message": "Instagram에서 일시적으로 요청을 차단했습니다",
  "suggestion": "5분 후에 다시 시도하거나, 다른 계정으로 분석해 보세요",
  "retry_after_seconds": 300,
  "retry_after_minutes": 5
}

// Circuit Breaker Open (503)
{
  "error": "SERVICE_UNAVAILABLE",
  "message": "현재 Instagram 분석 서비스가 일시적으로 사용 불가능합니다",
  "suggestion": "서버 과부하로 인해 잠시 동안 요청을 받을 수 없습니다. 5-10분 후 다시 시도해주세요",
  "retry_after_seconds": 300,
  "retry_after_minutes": 5
}
```

## 모니터링 설정

### 핵심 메트릭

```bash
# 큐 상태 확인
curl /api/v1/queue/status

# 전체 메트릭 확인
curl /api/v1/metrics

# 헬스 체크
curl /api/v1/metrics/health
```

### 알림 임계값

- 큐 대기 > 50개
- Instagram 실패율 > 30%
- Circuit Breaker Open
- 평균 응답 시간 > 30초

### Grafana 대시보드

필수 패널:
1. 큐 크기 (대기 중인 작업 수)
2. Instagram 요청 성공률
3. 처리 시간 (p50, p95, p99)
4. Circuit Breaker 상태
5. Rate Limiter 토큰/초

## 부하 테스트

### Locust 실행

```bash
cd backend/tests/load

# 300 concurrent users, 1 user/sec ramp up
locust -f locustfile.py \
  --host=http://localhost:8000 \
  --users 300 \
  --spawn-rate 1 \
  --run-time 10m
```

### 성능 기준

- 300명 동시 요청 시 큐 정상 동작
- 평균 응답 시간 < 60초
- 성공률 > 95%

## 문제 해결

### 자주 발생하는 문제

#### 1. curl_cffi 설치 실패
```bash
# macOS
brew install curl

# Ubuntu
sudo apt-get install libcurl4-openssl-dev
```

#### 2. Instagram 403 Forbidden
- IP 차단 가능성
- 5분 대기 후 재시도
- VPN/프록시 사용 검토

#### 3. 큐 과부하
- Max queue size 도달
- 잠시 후 재시도 권장
- 큐 크기 모니터링

#### 4. Circuit Breaker Open
- 연속 실패 발생
- 자동 복구 대기 (5분)
- 수동 복구: `instagram_circuit_breaker.reset()`

## 지원

- 기술 문의: [이슈 트래커]
- 긴급 연락: [관리자 이메일]
