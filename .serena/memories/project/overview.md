# itsmegram 프로젝트 개요

## 프로젝트명
itsmegram - Instagram AI Analyzer

## 목적
인스타그램 계정을 AI로 분석하여 인사이트와 리포트를 제공하는 서비스

## 기술 스택
- **Backend**: Python 3.13 + FastAPI + Pydantic
- **Frontend**: Next.js + TypeScript
- **AI**: Moonshot AI API
- **Rate Limiting**: slowapi
- **Caching**: Redis (선택사항)

## 프로젝트 구조
```
itsmegram/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── config.py            # 설정 관리 (Pydantic Settings)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py        # 헬스체크 엔드포인트
│   │   │   ├── instagram.py     # 인스타그램 데이터 수집
│   │   │   ├── analysis.py      # AI 분석
│   │   │   └── report.py        # 리포트 생성
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic 모델
│   │   └── services/
│   │       ├── __init__.py
│   │       └── cache_service.py # 캐시 서비스
│   ├── venv/                    # Python 가상환경
│   ├── requirements.txt
│   └── .env                     # 환경 변수
├── app/                         # Next.js 프론트엔드
├── components/
├── lib/
├── public/
└── docs/
```

## API 버저닝
- API v1 prefix: `/api/v1`
- 모든 엔드포인트는 `/api/v1` 하위에 위치
