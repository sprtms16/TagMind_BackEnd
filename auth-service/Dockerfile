# 1. 빌드 스테이지: Gradle을 사용하여 애플리케이션을 빌드
FROM gradle:8.5-jdk17-jammy AS build
WORKDIR /home/gradle/src
COPY build.gradle.kts settings.gradle.kts ./
COPY src ./src
RUN gradle build --no-daemon

# 2. 실행 스테이지: 빌드된 JAR 파일만 복사하여 가벼운 이미지 생성
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /home/gradle/src/build/libs/*.jar app.jar
# 서비스 계정 키 파일 복사
COPY serviceAccountKey.json ./serviceAccountKey.json
ENTRYPOINT ["java", "-jar", "app.jar"]
