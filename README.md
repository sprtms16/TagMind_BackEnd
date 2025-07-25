# TagMind Backend

> **TagMind 애플리케이션의 핵심 로직을 담당하는 백엔드 서버**

이 리포지토리는 FastAPI(Python)를 기반으로 구축되었으며, PostgreSQL 데이터베이스와 상호작용합니다. 모든 인프라는 Docker를 통해 관리되어 개발 및 배포의 일관성과 안정성을 보장합니다.

---

## 목차

- [아키텍처](#아키텍처)
- [기술 스택](#기술-스택)
- [API 문서](#api-문서)
- [주요 변경 사항](#주요-변경-사항)
- [프로젝트 설정 및 실행](#프로젝트-설정-및-실행)
- [환경 변수](#환경-변수)
- [트러블슈팅](#트러블슈팅)

## 아키텍처

- **FastAPI Application:** 메인 애플리케이션 로직, API 엔드포인트 제공
- **PostgreSQL:** 사용자 데이터, 일기, 태그 등 모든 데이터 저장
- **Docker & Docker Compose:** 개발 및 운영 환경 컨테이너화
- **(Optional) Celery & Redis:** 비동기 작업 처리 (향후 확장 고려)

## 기술 스택

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (with Alembic for migrations)
- **Infrastructure:** Docker

## API 문서

API 엔드포인트에 대한 상세한 명세는 [Swagger UI](http://localhost:8000/docs) 또는 [Redoc](http://localhost:8000/redoc)을 통해 확인할 수 있습니다. (서버 실행 후)

## 주요 변경 사항

최근 업데이트를 통해 다음과 같은 개선 사항이 적용되었습니다:

- **의존성 관리**: 사용하지 않는 `boto3` 라이브러리 및 개발 도구(`black`, `flake8`)를 제거하여 프로젝트 경량화 및 불필요한 의존성을 줄였습니다.
- **데이터베이스 마이그레이션**: 파괴적이거나 중복되는 Alembic 마이그레이션 파일을 제거하고, `alembic.ini`에서 데이터베이스 자격 증명을 플레이스홀더로 대체하여 보안을 강화했습니다. `User` 모델의 `updated_at` 필드에 `server_default`를 추가하여 데이터 일관성을 확보했습니다.
- **트랜잭션 관리**: CRUD(Create, Read, Update, Delete) 함수 내에서 `db.commit()` 호출을 `db.flush()`로 변경하여 트랜잭션의 원자성을 개선하고, 커밋은 엔드포인트 레벨에서 처리하도록 변경했습니다.
- **코드 구조 개선**: `get_db` 함수를 중앙 집중화하여 코드 중복을 제거하고 유지보수성을 높였습니다.
- **API 개선**: `create_diary` 엔드포인트에서 이미지 업로드 로직을 분리하여 책임 분리를 명확히 했습니다. CORS 설정에 대한 주석을 추가하여 개발 환경에서의 유연성과 프로덕션 환경에서의 보안 고려사항을 명시했습니다.
- **성능 고려**: `search_diaries` 함수에서 `distinct()` 사용에 대한 성능 고려사항을 주석으로 추가했습니다.

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

# AWS (S3 upload logic removed from backend, this section might be deprecated)
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_S3_BUCKET_NAME=your_s3_bucket_name
```

## 트러블슈팅

이 섹션에는 프로젝트 진행 중 발생한 주요 에러와 해결 과정을 기록합니다.

| 날짜       | 문제 상황 | 해결 과정 | 참고 링크 |
| ---------- | --------- | --------- | --------- |
| 2025-07-17 | Frontend/Backend CORS 오류 | FastAPI 백엔드에서 `CORSMiddleware` 설정을 수정하여 모든 출처(`allow_origins=["*"]`)를 허용하도록 변경. 중복 선언된 미들웨어를 정리하고 Docker 이미지를 재빌드하여 해결. | - |
| 2025-07-17 | `passlib`와 `bcrypt` 버전 충돌 | `requirements.txt`에 `bcrypt==3.2.0` 버전을 명시적으로 추가하여 라이브러리 호환성 문제를 해결하고 Docker 이미지를 재빌드함. | - |
| 2025-07-16 | 예: iOS 빌드 시 Cocoapods 버전 충돌 | `pod repo update` 후 `pod install` 재실행 | -         |
