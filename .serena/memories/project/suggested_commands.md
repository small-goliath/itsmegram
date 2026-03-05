# itsmegram 개발 명령어

## Backend 개발

### 가상환경 활성화
```bash
cd /Users/iymaeng/Documents/private/itsmegram/backend
source venv/bin/activate
```

### 서버 실행
```bash
cd /Users/iymaeng/Documents/private/itsmegram/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 패키지 설치
```bash
cd /Users/iymaeng/Documents/private/itsmegram/backend
source venv/bin/activate
pip install -r requirements.txt
```

### 테스트 실행
```bash
cd /Users/iymaeng/Documents/private/itsmegram/backend
source venv/bin/activate
python -c "from fastapi.testclient import TestClient; from app.main import app; client = TestClient(app); print(client.get('/api/v1/health').json())"
```

## Frontend 개발

### 개발 서버 실행
```bash
cd /Users/iymaeng/Documents/private/itsmegram
npm run dev
```

### 빌드
```bash
cd /Users/iymaeng/Documents/private/itsmegram
npm run build
```

## 유틸리티

### 파일 검색
```bash
find . -name "*.py" | grep -v __pycache__ | grep -v venv
```

### 프로세스 확인
```bash
lsof -i :8000  # 백엔드 포트
lsof -i :3000  # 프론트엔드 포트
```
