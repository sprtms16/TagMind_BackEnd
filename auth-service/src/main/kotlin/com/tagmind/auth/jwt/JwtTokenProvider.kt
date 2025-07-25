package com.tagmind.auth.jwt

import io.jsonwebtoken.Jwts
import io.jsonwebtoken.SignatureAlgorithm
import io.jsonwebtoken.security.Keys
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Component
import java.security.Key
import java.util.Date

@Component
class JwtTokenProvider(
    @Value("\${jwt.secret}")
    private val secret: String,
    @Value("\${jwt.access-token-expiration-ms}")
    private val accessTokenExpirationMs: Long,
    @Value("\${jwt.refresh-token-expiration-ms}")
    private val refreshTokenExpirationMs: Long
) {

    private val key: Key = Keys.hmacShaKeyFor(secret.toByteArray())

    fun createAccessToken(userId: Long): String {
        return Jwts.builder()
            .setSubject(userId.toString())
            .setIssuedAt(Date())
            .setExpiration(Date(System.currentTimeMillis() + accessTokenExpirationMs))
            .signWith(key, SignatureAlgorithm.HS256)
            .compact()
    }

    fun createRefreshToken(userId: Long): String {
        return Jwts.builder()
            .setSubject(userId.toString())
            .setIssuedAt(Date())
            .setExpiration(Date(System.currentTimeMillis() + refreshTokenExpirationMs))
            .signWith(key, SignatureAlgorithm.HS256)
            .compact()
    }

    fun validateToken(token: String): Boolean {
        return try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun getUserIdFromToken(token: String): Long {
        val claims = Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token).body
        return claims.subject.toLong()
    }

    // JWKS (JSON Web Key Set) 제공 로직은 HS256 (대칭키) 방식에서는 공개키/개인키 개념이 없으므로
    // JWKS 엔드포인트는 RS256 (비대칭키) 방식에서 주로 사용됩니다.
    // 현재는 HS256을 사용하므로 JWKS 엔드포인트는 구현하지 않습니다.
    // 만약 비대칭키 방식으로 변경한다면 해당 로직을 추가해야 합니다.
}
