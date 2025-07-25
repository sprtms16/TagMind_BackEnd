package com.tagmind.auth.domain

import jakarta.persistence.*

@Entity
@Table(name = "users")
data class User(
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,

    @Column(unique = true, nullable = false)
    val firebaseUid: String,

    @Column(unique = true, nullable = false)
    val email: String
)
