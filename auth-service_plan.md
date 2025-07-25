# TagMind Auth Service (Kotlin) 개발 계획

## 1. 목표
Firebase Authentication을 통해 소셜 로그인(Google, Apple 등) 및 이메일/비밀번호 인증을 처리하고, 이를 기반으로 TagMind 서비스 내부에서 사용할 JWT(JSON Web Token)를 발급하는 인증 서비스를 구축합니다. 이 서비스는 API Gateway 뒤에서 동작하며, 다른 리소스 서비스(FastAPI)는 이 서비스가 발급한 JWT를 통해 사용자 인증을 수행합니다.

## 2. 주요 기능
1.  **Firebase Admin SDK 초기화**: Firebase 서비스 계정 키를 사용하여 Admin SDK를 초기화합니다.
2.  **사용자 관리**:
    *   Firebase UID를 기반으로 내부 데이터베이스에 사용자 정보를 저장/조회합니다. (최초 로그인 시 사용자 생성)
    *   사용자 엔티티(User Entity) 정의 및 JPA Repository 구현.
3.  **JWT (JSON Web Token) 발급 및 관리**:
    *   Access Token: 단기 유효성, API 접근 권한 부여.
    *   Refresh Token: 장기 유효성, Access Token 재발급용.
    *   JWT 생성, 서명, 유효성 검증 로직 구현.
4.  **인증 API 엔드포인트**:
    *   `POST /auth/firebase-login`: 클라이언트로부터 Firebase ID Token을 받아 유효성을 검증하고, 내부 JWT(Access/Refresh Token)를 발급합니다.
    *   `GET /.well-known/jwks.json`: 다른 서비스(예: FastAPI 리소스 서비스)가 JWT의 서명을 검증할 수 있도록 공개키(JWKS)를 제공합니다.
    *   (선택) `POST /auth/refresh-token`: Refresh Token을 사용하여 새로운 Access Token을 발급합니다.
5.  **보안 설정**: Spring Security를 사용하여 API 엔드포인트 보안 및 JWT 필터 체인 구성.

## 3. 기술 스택
*   **언어**: Kotlin
*   **프레임워크**: Spring Boot 3.2.x
*   **의존성**:
    *   `spring-boot-starter-web`: 웹 애플리케이션
    *   `spring-boot-starter-security`: 보안
    *   `spring-boot-starter-data-jpa`: 데이터베이스 연동
    *   `postgresql`: PostgreSQL JDBC 드라이버
    *   `firebase-admin`: Firebase ID Token 검증
    *   `jjwt-api`, `jjwt-impl`, `jjwt-jackson`: JWT 생성 및 파싱
    *   `spring-boot-starter-validation`: 유효성 검증
    *   `spring-boot-starter-actuator`: 모니터링 (선택)

## 4. 구현 상세 계획

### 4.1. Firebase Admin SDK 초기화
*   `AuthServiceApplication.kt` 또는 별도의 설정 클래스에서 `FirebaseApp.initializeApp()` 호출.
*   `serviceAccountKey.json` 파일 경로를 환경 변수(`GOOGLE_APPLICATION_CREDENTIALS`)로 주입받아 사용.

### 4.2. 사용자 엔티티 및 Repository
*   `User` 엔티티 정의 (`id`, `firebaseUid`, `email` 등).
*   `UserRepository` (Spring Data JPA) 정의.

### 4.3. JWT 유틸리티 클래스 (`JwtTokenProvider`)
*   JWT 생성 메서드: `createAccessToken(userId: Long)`, `createRefreshToken(userId: Long)`.
    *   `jjwt` 라이브러리 사용.
    *   서명에 사용할 비밀 키(Secret Key)는 환경 변수 또는 설정 파일에서 관리.
    *   Access Token과 Refresh Token의 유효 기간 설정.
*   JWT 유효성 검증 메서드: `validateToken(token: String)`.
*   JWT에서 사용자 정보(클레임) 추출 메서드: `getUserIdFromToken(token: String)`.
*   JWKS(JSON Web Key Set) 엔드포인트 제공 로직:
    *   `/.well-known/jwks.json` 경로로 접근 시, JWT 서명에 사용된 공개 키를 JWKS 형식으로 반환.

### 4.4. 인증 컨트롤러 (`AuthController`)
*   **`POST /auth/firebase-login`**:
    *   요청 바디: `firebaseIdToken: String`.
    *   `FirebaseAuth.getInstance().verifyIdToken(firebaseIdToken)` 호출하여 Firebase ID Token 검증.
    *   검증 성공 시, `decodedToken.getUid()`를 사용하여 Firebase UID 추출.
    *   `UserRepository`를 통해 해당 `firebaseUid`를 가진 사용자를 조회하거나, 없으면 새로 생성하여 DB에 저장.
    *   `JwtTokenProvider`를 사용하여 Access Token과 Refresh Token 생성.
    *   응답: `accessToken`, `refreshToken`.
*   **`GET /.well-known/jwks.json`**:
    *   `JwtTokenProvider`에서 JWKS를 반환하는 메서드를 호출하여 응답.

### 4.5. Spring Security 설정 (`SecurityConfig`)
*   `WebSecurityCustomizer`를 사용하여 `/auth/**` 및 `/.well-known/jwks.json` 경로에 대한 인증을 비활성화 (모든 사용자 접근 허용).
*   나머지 경로에 대해서는 JWT 기반 인증 필터 적용 (추후 필요 시).

## 5. 테스트 계획
*   **단위 테스트**: `JwtTokenProvider`의 JWT 생성/검증 로직, `UserRepository`의 DB 연동 로직.
*   **통합 테스트**: `AuthController`의 `/auth/firebase-login` 엔드포인트가 Firebase ID Token을 올바르게 처리하고 JWT를 발급하는지 확인.
*   **Docker Compose 연동 테스트**: 모든 서비스(Gateway, Auth, Resource, DB)가 Docker 환경에서 정상적으로 통신하는지 확인.

## 6. 진행 방식
1.  `auth-service` 프로젝트에 Firebase Admin SDK 초기화 코드 추가.
2.  `User` 엔티티 및 `UserRepository` 구현.
3.  `JwtTokenProvider` 클래스 구현 (JWT 생성, 검증, JWKS 제공).
4.  `AuthController` 구현 (`/auth/firebase-login`, `/.well-known/jwks.json`).
5.  Spring Security 설정.
6.  `docker-compose up --build -d` 명령으로 전체 시스템 재시작 및 테스트.
