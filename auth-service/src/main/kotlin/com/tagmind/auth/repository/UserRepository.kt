package com.tagmind.auth.repository

import com.tagmind.auth.domain.User
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface UserRepository : JpaRepository<User, Long> {
    fun findByFirebaseUid(firebaseUid: String): User?
    fun findByEmail(email: String): User?
}
