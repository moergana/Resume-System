package org.kira.resumesystem.config;

import io.github.bucket4j.distributed.proxy.ProxyManager;
import lombok.RequiredArgsConstructor;
import org.kira.resumesystem.interceptor.AuthLoginInterceptor;
import org.kira.resumesystem.interceptor.BucketInterceptor;
import org.kira.resumesystem.interceptor.RedisBucketInterceptor;
import org.kira.resumesystem.utils.JwtTool;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@RequiredArgsConstructor
public class MvcConfig implements WebMvcConfigurer {
    // 通过自动注入的方式获取拦截器实例
    // 不要使用new的方式创建拦截器，否则拦截器内部的依赖无法注入
    private final AuthLoginInterceptor authLoginInterceptor;
    // private final BucketInterceptor bucketInterceptor;
    private final RedisBucketInterceptor redisBucketInterceptor;

    /**
     * 添加拦截器的方法
     * @param registry InterceptorRegistry
     */
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(authLoginInterceptor)   // 添加登录拦截器
                .addPathPatterns("/**")     // 拦截所有请求路径
                .excludePathPatterns(       // 排除不需要认证的路径
                        "/user/login",
                        "/user/register",
                        "/user/register/emailCode",
                        "/user/resetPassword",
                        "/user/resetPassword/emailCode"
                )
                .order(0);  // 设置拦截器的执行顺序，登录token验证优先级最高

        /*
        registry.addInterceptor(bucketInterceptor)   // 添加令牌桶拦截器，用于限流
                .addPathPatterns("/**");    // 拦截所有请求路径
        */
        registry.addInterceptor(redisBucketInterceptor)   // 添加基于Redis的令牌桶拦截器，用于分布式限流
                .addPathPatterns("/**")     // 拦截所有请求路径
                .order(1);      // 设置拦截器的执行顺序，限流操作在登录验证之后
    }

    /**
     * 配置跨域请求规则的方法。该方法存在一个问题：
     * 浏览器在跨域前会发送一个预检请求（OPTIONS请求）到目标资源以确定是否允许跨域
     * 但 OPTIONS 请求不会带有自定义的信息（比如验证身份的token），如果被拦截器拦截，可能会导致跨域失败
     * @param registry CorsRegistry
     */
    /*
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")  // 允许跨域访问的路径
                .allowedOrigins("http://localhost:5173")    // 添加允许跨域访问的源
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")  // 允许的HTTP方法
                .allowedHeaders("*")    // 允许的请求头Header
                .allowCredentials(true)    // 是否允许携带 Cookie
                .maxAge(3600);  // 预检请求的缓存时间，单位为秒
    }
    */

    /**
     * 使用 Filter 处理跨域，他在 DispatcherServlet 之前执行，因此优先级高于拦截器
     * 解决预检请求（OPTIONS 请求）被拦截器拦截导致跨域失败的问题
     */
    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();
        // 被允许访问的域名
        // 使用addAllowedOriginPattern（而不是addAllowedOrigin）以支持通配符
        config.addAllowedOriginPattern("http://localhost:*");
        config.addAllowedOriginPattern("http://127.0.0.1:*");
        // 允许携带 Cookie
        config.setAllowCredentials(true);
        // 允许所有的请求头
        config.addAllowedHeader("*");
        // 允许所有的请求方法 (GET, POST, PUT, OPTIONS 等)
        config.addAllowedMethod("*");

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}
