# TagMind: 백엔드(BE) 개발 계획서

## 1. 개요
이 문서는 'TagMind' 애플리케이션의 백엔드 시스템 개발에 대한 기술적 청사진과 구체적인 실행 계획을 정의합니다. 기획서의 핵심 기능인 '지능형 태깅 엔진'을 안정적이고 확장 가능하게 구축하고, Docker를 통해 개발 및 배포 효율성을 극대화하는 것을 목표로 합니다.

---

## 2. 기술 스택 (Tech Stack)

*   **언어/프레임워크:** **Python / FastAPI**
    *   **선정 이유:** Python의 풍부한 AI/ML 생태계(Hugging Face, spaCy, Scikit-learn)를 활용하기에 최적이며, FastAPI는 현대적인 비동기 처리를 지원하고 배우기 쉬워 높은 생산성을 보장합니다.
*   **데이터베이스:** **PostgreSQL**
    *   **선정 이유:** 오랜 기간 검증된 안정성과 데이터 무결성을 제공하며, JSONB 타입을 지원하여 정형 데이터(사용자 정보)와 비정형 데이터(태그, 감성 분석 결과)를 유연하게 함께 관리할 수 있습니다.
*   **AI/NLP:** **Hugging Face Transformers, Google Gemini API, Scikit-learn**
    *   **선정 이유:** 사전 훈련된 최신 NLP 모델(예: KLUE-BERT)을 쉽게 활용하고, 서비스 특화 모델로 미세 조정(fine-tuning)하기 용이합니다. Gemini API는 초기 개발 단계에서 강력한 텍스트 분석 기능을 빠르게 테스트하고 구현하는 데 비용 효율적입니다.
*   **인프라:** **AWS (EC2, RDS, S3), Docker, Docker Compose**
    *   **선정 이유:** AWS는 스타트업 친화적인 프리티어와 뛰어난 확장성을 제공합니다. Docker는 개발-테스트-운영 환경을 일치시켜 "제 컴퓨터에서는 됐는데…"와 같은 문제를 원천적으로 방지하고, 배포 안정성과 이식성을 높입니다.

---

## 3. Docker 기반 아키텍처 및 DB 스키마

### 3.1. Docker 기반 아키텍처

안정적이고 확장 가능한 백엔드 운영을 위해 Docker 컨테이너 기반으로 시스템을 구축합니다.

*   **`Dockerfile` (FastAPI App):**
    *   Python 공식 이미지를 기반으로 애플리케이션 의존성(`requirements.txt`)을 설치합니다.
    *   FastAPI 애플리케이션을 Uvicorn과 같은 ASGI(Asynchronous Server Gateway Interface) 서버로 실행합니다.
    *   소스 코드를 컨테이너에 복사하고 외부 요청을 받을 포트(예: 8000)를 노출합니다.

*   **`docker-compose.yml`:**
    *   **`app` (FastAPI):** 위 `Dockerfile`을 빌드하여 FastAPI 애플리케이션 컨테이너를 정의합니다. DB 컨테이너에 의존하도록 설정합니다.
    *   **`db` (PostgreSQL):** PostgreSQL 공식 이미지를 사용하여 데이터베이스 컨테이너를 정의합니다. 데이터 영속성을 위해 호스트 시스템의 특정 경로와 컨테이너의 데이터 경로를 볼륨(volume)으로 연결합니다. (예: `./data:/var/lib/postgresql/data`)
    *   **`worker` (Celery - Optional):** AI 태깅과 같이 시간이 오래 걸리는 작업을 백그라운드에서 처리하기 위한 비동기 작업 큐 컨테이너입니다. (MVP 이후 도입)
    *   **`nginx` (Reverse Proxy - Optional):** Nginx를 리버스 프록시로 사용하여 API 게이트웨이 역할을 수행하고, 로드 밸런싱, SSL 인증서 처리 등을 담당하여 보안과 확장성을 강화합니다. (공식 출시 시 도입)

### 3.2. 데이터베이스 스키마 (PostgreSQL)

```sql
-- 사용자 정보
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    provider VARCHAR(50) DEFAULT 'email',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 일기
CREATE TABLE diaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    image_url VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 태그
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- 일기와 태그의 관계 (다대다)
CREATE TABLE diary_tags (
    diary_id INTEGER REFERENCES diaries(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    source VARCHAR(20) DEFAULT 'manual', -- 'manual', 'ai_rule', 'ai_model'
    PRIMARY KEY (diary_id, tag_id)
);

-- 분석 결과 (JSONB 활용)
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    diary_id INTEGER UNIQUE REFERENCES diaries(id) ON DELETE CASCADE,
    sentiment JSONB, -- 예: {"label": "positive", "score": 0.98}
    entities JSONB, -- 예: [{"text": "김민준", "type": "PERSON"}, {"text": "사무실", "type": "LOCATION"}]
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. 개발 Task 상세 (WBS 기반)

### Phase 1: MVP API 개발 (8주)

*   **Week 1-2: 환경 설정 및 DB 구축**
    *   [ ] `docker-compose.yml` 및 `Dockerfile`을 작성하여 로컬 개발 환경 구축
    *   [ ] FastAPI 프로젝트 초기 설정 및 PostgreSQL 연동 (SQLAlchemy ORM 사용)
    *   [ ] 위 DB 스키마를 기반으로 ORM 모델 정의 및 데이터베이스 마이그레이션 설정 (Alembic)

*   **Week 3-4: 사용자 인증 API**
    *   [ ] `POST /auth/signup`: 이메일 기반 회원가입 (비밀번호 해싱 처리)
    *   [ ] `POST /auth/login`: JWT(JSON Web Token) 기반 로그인 (Access/Refresh Token 발급)
    *   [ ] `POST /auth/oauth/{provider}`: 소셜 로그인 (Google, Apple) API
    *   [ ] `GET /users/me`: 인증된 사용자 정보 조회 (OAuth2PasswordBearer를 이용한 인증 미들웨어 구현)

*   **Week 5-6: 일기 CRUD API**
    *   [ ] `POST /diaries`: 새 일기 작성 (사진 업로드 시 AWS S3 연동 로직 포함)
    *   [ ] `GET /diaries`: 특정 기간의 일기 목록 조회 (페이지네이션 적용)
    *   [ ] `GET /diaries/{diary_id}`: 특정 일기 상세 조회
    *   [ ] `PUT /diaries/{diary_id}`: 일기 수정
    *   [ ] `DELETE /diaries/{diary_id}`: 일기 삭제

*   **Week 7-8: 태그, 검색 API 및 배포**
    *   [ ] `POST /diaries/{diary_id}/tags`: 수동으로 태그를 추가/관리하는 API
    *   [ ] `GET /search`: 텍스트 내용(Full-Text Search) 및 태그 기반 검색 API
    *   [ ] **초기 배포:** AWS EC2, RDS에 Docker 컨테이너를 배포하고, FE팀이 사용할 수 있도록 API 엔드포인트 제공

### Phase 2: 지능형 엔진 개발 및 통합 (MVP 출시 후, 8주)

*   **Week 9-12: AI 태깅 엔진 개발 (v0.1, v0.5)**
    *   [ ] **v0.1 (규칙 기반):** 일기 저장 시, 비동기 처리(Celery)를 통해 KoNLPy, spaCy 등을 활용하여 핵심 키워드(명사, 동사)를 추출하고 태그를 생성하는 로직 개발
    *   [ ] **v0.5 (외부 API 활용):** Google Gemini API 또는 AWS Comprehend를 연동하여 감성 분석 및 개체명 인식 기능을 구현하고, `analysis_results` 테이블에 저장
    *   [ ] `POST /ai/feedback`: AI가 생성한 태그에 대한 사용자 피드백(수정/삭제)을 수집하는 API (향후 모델 학습 데이터로 활용)

*   **Week 13-16: 분석 API 및 고도화**
    *   [ ] `GET /analytics/mood-over-time`: 기간별 감성 변화 데이터를 집계하여 제공하는 API
    *   [ ] `GET /analytics/correlation`: 특정 활동/인물 태그와 감성 태그의 상관관계를 분석하여 제공하는 API
    *   [ ] **v1.0 (자체 모델) 준비:** 수집된 사용자 피드백 데이터를 가공하여 Hugging Face의 KLUE-BERT 같은 한국어 모델을 미세 조정(fine-tuning)하기 위한 데이터셋 구축 파이프라인 설계
    *   [ ] **모니터링 및 로깅:** ELK Stack 또는 AWS CloudWatch를 통해 API 성능 모니터링 및 에러 로깅 시스템 구축
    *   [ ] **수익화:** Stripe 등 결제 게이트웨이를 연동하여 구독 모델(TagMind Pro)을 위한 API 구현
