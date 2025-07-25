package com.tagmind.auth

import com.google.auth.oauth2.GoogleCredentials
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import java.io.FileInputStream
import java.io.IOException

@SpringBootApplication
class AuthServiceApplication

fun main(args: Array<String>) {
    runApplication<AuthServiceApplication>(*args)
}

@Configuration
class FirebaseConfig {

    @Bean
    fun firebaseApp(): FirebaseApp {
        try {
            val serviceAccountPath = System.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                ?: throw IllegalArgumentException("GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")

            val serviceAccount = FileInputStream(serviceAccountPath)

            val options = FirebaseOptions.builder()
                .setCredentials(GoogleCredentials.fromStream(serviceAccount))
                .build()

            return FirebaseApp.initializeApp(options)
        } catch (e: IOException) {
            throw RuntimeException("Failed to initialize Firebase Admin SDK", e)
        }
    }
}
