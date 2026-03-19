# StudyMate
> AI 문제 생성 + 오답 분석 학습 도우미 SaaS

## 개요

StudyMate는 Gemini AI를 활용해 사용자가 입력한 학습 자료에서 퀴즈를 자동 생성하고, 오답 패턴을 분석해 취약점을 진단하는 서비스입니다.
학습 세션 데이터를 누적하여 맞춤형 학습 경로를 제안합니다.

**수익 구조**: 무료 플랜(월 20문제) / 프리미엄 플랜 월 구독(무제한 생성 + 심층 분석)

## 기술 스택

- **Backend**: FastAPI 0.104, Python 3.11
- **DB**: SQLAlchemy 2.0 (async) + SQLite (aiosqlite) + Alembic
- **AI**: Google Gemini API (퀴즈 생성, 오답 분석)
- **인증**: JWT (python-jose) + bcrypt
- **배포**: Docker + docker-compose

## 시작하기

### 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 다음 값을 설정합니다:

| 변수명 | 설명 |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `DATABASE_URL` | SQLite DB 경로 (기본값 사용 가능) |
| `SECRET_KEY` | JWT 서명용 시크릿 키 |
| `DEBUG` | 개발 환경 여부 (True/False) |

### 실행 방법

#### Docker (권장)

```bash
docker-compose up -d
```

#### 직접 실행

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

서버 실행 후 http://localhost:8000/docs 에서 API 문서를 확인하세요.

## API 문서

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/` | 헬스체크 |
| GET | `/health` | 서버 상태 확인 |
| POST | `/users/register` | 회원가입 |
| POST | `/users/login` | 로그인 (JWT 발급) |
| GET | `/users/me` | 내 정보 조회 |
| GET | `/users/me/stats` | 학습 통계 조회 |
| POST | `/quiz/generate` | AI 퀴즈 생성 |
| POST | `/quiz/{id}/attempt` | 퀴즈 풀기 (답안 제출) |
| GET | `/quiz/history` | 풀이 기록 조회 |
| GET | `/quiz/analysis` | 오답 분석 결과 조회 |

## 수익 구조

- **무료 플랜**: 월 20문제 생성, 기본 오답 통계
- **프리미엄 플랜** (월 6,900원): 무제한 문제 생성, AI 심층 오답 분석, 맞춤 학습 경로 추천
- **기관 라이선스**: 학원/학교 단위 대량 구독 할인

## 라이선스

MIT
