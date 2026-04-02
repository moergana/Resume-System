package org.kira.resumesystem.config;

import lombok.RequiredArgsConstructor;
import org.kira.resumesystem.interceptor.InternalUserInterceptor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.Arrays;
import java.util.List;

/**
 * MVC 配置
 *
 * 网关改造后的变更说明：
 * - JWT 认证拦截器（AuthLoginInterceptor）→ 迁移至 Gateway 网关层
 * - 限流拦截器（RedisBucketInterceptor）→ 迁移至 Gateway 网关层
 * - CORS 配置（CorsFilter）→ 迁移至 Gateway 网关层
 *
 * 保留的功能：
 * - InternalUserInterceptor：从网关转发的 Header 中解析用户身份信息
 */
@Configuration
@RequiredArgsConstructor
public class MvcConfig implements WebMvcConfigurer {
    private final InternalUserInterceptor internalUserInterceptor;

    private static final List<String> PUBLIC_PATHS = Arrays.asList(
            "/user/login",
            "/user/register",
            "/user/register/emailCode",
            "/user/resetPassword",
            "/user/resetPassword/emailCode",
            "/error"
    );

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(internalUserInterceptor)
                .addPathPatterns("/**")     // 拦截所有请求
                .excludePathPatterns(PUBLIC_PATHS)
                .order(0);
    }
}
