package com.tagmind.auth.controller

import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthException
import com.tagmind.auth.domain.User
import com.tagmind.auth.jwt.JwtTokenProvider
import com.tagmind.auth.repository.UserRepository
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.server.ResponseStatusException

data class FirebaseLoginRequest(val firebaseIdToken: String)
data class JwtResponse(val accessToken: String, val refreshToken: String)

@RestController
@RequestMapping("/auth")
class AuthController(
    private val userRepository: UserRepository,
    private val jwtTokenProvider: JwtTokenProvider
) {

    @PostMapping("/firebase-login")
    fun firebaseLogin(@RequestBody request: FirebaseLoginRequest): ResponseEntity<JwtResponse> {
        val firebaseIdToken = request.firebaseIdToken

        val decodedToken = try {
            FirebaseAuth.getInstance().verifyIdToken(firebaseIdToken)
        } catch (e: FirebaseAuthException) {
            throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Invalid Firebase ID Token", e)
        }

        val firebaseUid = decodedToken.uid
        val email = decodedToken.email ?: throw ResponseStatusException(HttpStatus.BAD_REQUEST, "Email not found in Firebase token")

        val user = userRepository.findByFirebaseUid(firebaseUid) ?: run {
            // User not found, create new user
            val newUser = User(firebaseUid = firebaseUid, email = email)
            userRepository.save(newUser)
        }

        val accessToken = jwtTokenProvider.createAccessToken(user.id)
        val refreshToken = jwtTokenProvider.createRefreshToken(user.id)

        return ResponseEntity.ok(JwtResponse(accessToken, refreshToken))
    }

    // JWKS 엔드포인트는 HS256 (대칭키) 방식에서는 공개키/개인키 개념이 없으므로 구현하지 않습니다.
    // 만약 비대칭키 방식으로 변경한다면 해당 로직을 추가해야 합니다.
}
