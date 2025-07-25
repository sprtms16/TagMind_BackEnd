package com.tagmind.auth.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity
import org.springframework.security.config.annotation.web.configuration.WebSecurityCustomizer
import org.springframework.security.web.SecurityFilterChain

@Configuration
@EnableWebSecurity
class SecurityConfig {

    @Bean
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain {
        http
            .csrf { it.disable() } // CSRF 비활성화
            .authorizeHttpRequests { authz ->
                authz
                    .requestMatchers("/auth/**").permitAll() // /auth/** 경로는 인증 없이 접근 허용
                    .anyRequest().authenticated() // 나머지 모든 요청은 인증 필요
            }
        return http.build()
    }

    @Bean
    fun webSecurityCustomizer(): WebSecurityCustomizer {
        return WebSecurityCustomizer { web ->
            web.ignoring().requestMatchers(
                "/auth/**",
                "/.well-known/jwks.json" // JWKS 엔드포인트도 인증 없이 접근 허용
            )
        }
    }
}
