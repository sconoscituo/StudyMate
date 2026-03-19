# StudyMate - AI 학습 도우미 서비스

## 필요한 API 키 및 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 (학습 콘텐츠 생성/분석용) | https://aistudio.google.com/app/apikey |
| `SECRET_KEY` | JWT 토큰 서명용 시크릿 키 (임의 문자열) | - |
| `PORTONE_API_KEY` | 포트원(PortOne) 결제 API 키 | https://portone.io |
| `PORTONE_API_SECRET` | 포트원(PortOne) 결제 API 시크릿 | https://portone.io |
| `DATABASE_URL` | 데이터베이스 연결 URL (기본: SQLite) | - |

## GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `SECRET_KEY` | JWT 시크릿 키 (랜덤 32자 이상 문자열) |
| `PORTONE_API_KEY` | 포트원 API 키 |
| `PORTONE_API_SECRET` | 포트원 API 시크릿 |

## 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/StudyMate.git
cd StudyMate

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 아래 항목 입력:
# GEMINI_API_KEY=your_gemini_api_key
# SECRET_KEY=your_random_secret_key
# PORTONE_API_KEY=your_portone_api_key (결제 기능 사용 시)
# PORTONE_API_SECRET=your_portone_api_secret (결제 기능 사용 시)

# 5. 데이터베이스 마이그레이션 (alembic 사용)
alembic upgrade head

# 6. 서버 실행
uvicorn app.main:app --reload
```

서버 기동 후 http://localhost:8000/docs 에서 API 문서를 확인할 수 있습니다.

## Docker로 실행

```bash
docker-compose up --build
```

## 주요 기능 사용법

### AI 학습 자료 생성
- Gemini AI가 주제를 입력받아 요약본, 퀴즈, 플래시카드를 자동으로 생성합니다.
- 학습 수준(초급/중급/고급)에 맞는 난이도로 콘텐츠를 조절합니다.

### 퀴즈 및 테스트
- 학습한 내용을 바탕으로 AI가 자동으로 문제를 생성하고 채점합니다.
- 오답 분석을 통해 취약 부분을 파악하고 집중 학습을 유도합니다.

### 학습 진도 추적
- 과목별, 날짜별 학습 시간과 진도를 기록합니다.
- 목표 달성률을 시각화해서 확인할 수 있습니다.

### 결제 및 구독
- 포트원(PortOne) 결제 연동으로 프리미엄 플랜을 제공합니다.
- 결제 없이도 기본 학습 기능은 무료로 사용 가능합니다.

### 데이터베이스 마이그레이션
- `alembic`을 사용해 DB 스키마를 관리합니다.
- 새로운 마이그레이션 파일 생성: `alembic revision --autogenerate -m "설명"`
- 마이그레이션 적용: `alembic upgrade head`

### 인증
- JWT 기반 인증 (토큰 유효기간: 24시간)
- `/api/auth/register` - 회원가입
- `/api/auth/login` - 로그인 및 토큰 발급

## 프로젝트 구조

```
StudyMate/
├── app/
│   ├── config.py       # 환경변수 설정
│   ├── database.py     # DB 연결 관리
│   ├── main.py         # FastAPI 앱 진입점
│   ├── models/         # SQLAlchemy 모델
│   ├── routers/        # API 라우터
│   ├── schemas/        # Pydantic 스키마
│   └── services/       # 비즈니스 로직 (AI, 결제 등)
├── tests/
├── docker-compose.yml
└── requirements.txt
```
