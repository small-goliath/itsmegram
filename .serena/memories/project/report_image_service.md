# 리포트 이미지 생성 서비스

## 개요
Instagram 스토리 형식(1080x1920)의 리포트 이미지를 생성하는 서비스

## 파일 구조
- `backend/app/services/image_service.py` - 이미지 생성 서비스
- `backend/templates/report_story.html` - HTML 템플릿
- `backend/app/routers/report.py` - `/report/{report_id}/image` 엔드포인트

## 주요 기능
1. **HTML 템플릿 렌더링** - Jinja2를 사용하여 리포트 데이터를 HTML로 변환
2. **Playwright 스크린샷** - Chromium 브라우저로 HTML을 PNG 이미지로 변환
3. **Redis 캐싱** - 생성된 이미지를 1시간 TTL로 캐싱

## API 엔드포인트
```
GET /api/v1/report/{report_id}/image
```
- 성공: PNG 이미지 바이트 반환
- 캐싱: `Cache-Control: public, max-age=3600`

## 의존성
```
playwright==1.49.1
jinja2==3.1.4
```

## 설치
```bash
pip install playwright==1.49.1 jinja2==3.1.4
playwright install chromium
```

## 테스트
```bash
PYTHONPATH=/Users/iymaeng/Documents/private/itsmegram/backend python -m pytest tests/test_image_service.py -v
```

## 템플릿 섹션
- 프로필 섹션 (프로필 이미지, 사용자명)
- 핵심 지표 (참여율, 평균 좋아요/댓글, 게시물 수)
- 콘텐츠 성향 (카테고리, 시각적/텍스트 스타일, 해시태그)
- 라이프스타일 (관심사, 활동 패턴, 소비 성향)
- 성격 분석 (표현력 바, 성향, 커뮤니케이션)
- 종합 분석 (요약 텍스트)
- 푸터 (ITSMEGRAM 브랜딩)

## 디자인 특징
- 그라데이션 배경 (병아리색에서 복숭아색으로)
- Glassmorphism 효과 (backdrop-filter: blur)
- 한글 폰트 지원 (Noto Sans KR)
- 반응형이 아닌 고정 스토리 형식 (1080x1920)
