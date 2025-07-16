# TagMind Backend

> **TagMind 애플리케이션의 핵심 로직과 지능형 태깅 엔진을 담당하는 백엔드 서버**

이 리포지토리는 FastAPI(Python)를 기반으로 구축되었으며, PostgreSQL 데이터베이스와 상호작용하고, 지능형 기능들을 위한 AI/NLP 모델을 서빙합니다. 모든 인프라는 Docker를 통해 관리되어 개발 및 배포의 일관성과 안정성을 보장합니다.

---

## 목차

- [아키텍처](#아키텍처)
- [기술 스택](#기술-스택)
- [API 문서](#api-문서)
- [프로젝트 설정 및 실행](#프로젝트-설정-및-실행)
- [환경 변수](#환경-변수)
- [트러블슈팅](#트러블슈팅)

## 아키텍처

- **FastAPI Application:** 메인 애플리케이션 로직, API 엔드포인트 제공
- **PostgreSQL:** 사용자 데이터, 일기, 태그 등 모든 데이터 저장
- **Docker & Docker Compose:** 개발 및 운영 환경 컨테이너화
- **(Optional) Nginx:** 리버스 프록시, 로드 밸런싱
- **(Optional) Celery & Redis:** 비동기 작업 처리 (AI 태깅 등)

## 기술 스택

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (with Alembic for migrations)
- **AI/NLP:** Hugging Face Transformers, KoNLPy, Scikit-learn
- **Infrastructure:** Docker, AWS (EC2, RDS, S3)

## API 문서

API 엔드포인트에 대한 상세한 명세는 [Swagger UI](http://localhost:8000/docs) 또는 [Redoc](http://localhost:8000/redoc)을 통해 확인할 수 있습니다. (서버 실행 후)

## 프로젝트 설정 및 실행

1.  **Docker 설치:** [공식 문서](https://docs.docker.com/get-docker/)를 참고하여 Docker와 Docker Compose를 설치합니다.
2.  **리포지토리 클론:**
    ```bash
    git clone https://github.com/sprtms16/TagMind_BackEnd.git
    cd TagMind_BackEnd
    ```
3.  **환경 변수 파일 생성:** `.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 아래 [환경 변수](#환경-변수) 섹션을 참고하여 내용을 채웁니다.
    ```bash
    cp .env.example .env
    ```
4.  **Docker 컨테이너 실행:**
    ```bash
    docker-compose up -d --build
    ```

## 환경 변수

프로젝트 실행을 위해 루트 디렉토리에 `.env` 파일이 필요합니다.

```env
# .env.example

# PostgreSQL
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=tagmind_db
DATABASE_URL=postgresql://your_db_user:your_db_password@db:5432/tagmind_db

# JWT
JWT_SECRET_KEY=your_super_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your_s3_bucket_name
```

## 트러블슈팅

이 섹션에는 프로젝트 진행 중 발생한 주요 에러와 해결 과정을 기록합니다.

| 날짜       | 문제 상황 | 해결 과정 | 참고 링크 |
| ---------- | --------- | --------- | --------- |
| 2025-07-16 | 예: `docker-compose up` 시 DB 연결 실패 | `.env` 파일의 `DATABASE_URL` 포트가 `db:5432`로 올바르게 설정되었는지 확인 | -         |

