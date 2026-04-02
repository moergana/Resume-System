package org.kira.gateway.filter;

import cn.hutool.json.JSONUtil;
import cn.hutool.jwt.JWT;
import cn.hutool.jwt.JWTValidator;
import cn.hutool.jwt.signers.JWTSigner;
import cn.hutool.jwt.signers.JWTSignerUtil;
import lombok.extern.slf4j.Slf4j;
import org.kira.gateway.config.JwtProperties;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 全局 JWT 认证过滤器
 * 在网关层统一完成 JWT 验证，下游服务（Java 后端、Python 后端）无需各自实现认证逻辑
 *
 * 验证通过后，将用户信息（user_id, role）注入下游请求的 Header 中，
 * 下游服务可以直接从 Header 中获取用户身份
 */
@Slf4j
@Component
public class JwtAuthGlobalFilter implements GlobalFilter, Ordered {
    private final JWTSigner jwtSigner;
    private final List<String> excludePaths;
    private final AntPathMatcher pathMatcher = new AntPathMatcher();

    public JwtAuthGlobalFilter(KeyPair keyPair, JwtProperties jwtProperties) {
        this.jwtSigner = JWTSignerUtil.createSigner("rs256", keyPair);
        this.excludePaths = jwtProperties.getExcludePaths();
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().value();

        // 1. 判断是否白名单路径
        //    注意：Gateway 路由配置了 StripPrefix=1（去掉 /api 或 /ai 前缀后再转发），
        //    但自定义过滤器通常优先级较高，会在 StripPrefix 之前执行，因此这里收到的 path 仍然带有前缀（如 /api/user/login）。
        //    需要在匹配时去掉前缀再比较。
        if (isExcludedPath(path)) {
            return chain.filter(exchange);
        }

        // 2. 从 Header 获取 JWT Token
        String token = request.getHeaders().getFirst("Authorization");
        
        // 3. 如果 Header 中没有，尝试从 Cookie 中获取（支持 window.open 等浏览器直接访问的方式）
        if (token == null || token.isEmpty()) {
            HttpCookie cookie = request.getCookies().getFirst("token");
            if (cookie != null) {
                token = cookie.getValue();
            }
        }

        if (token == null || token.isEmpty()) {
            log.info("请求未携带Token，拒绝访问: {}", path);
            return writeUnauthorizedResponse(exchange, "请求未携带Token，请重新登录");
        }

        // 4. 解析和验证 JWT
        try {
            JWT jwt = JWT.of(token).setSigner(jwtSigner);
            // 验证签名
            if (!jwt.verify()) {
                log.info("Token签名验证失败: {}", path);
                return writeUnauthorizedResponse(exchange, "无效的Token，请重新登录");
            }
            // 验证过期时间
            JWTValidator.of(jwt).validateDate();

            // 4. 提取用户信息
            Object userId = jwt.getPayload("user_id");
            Object role = jwt.getPayload("role");
            if (userId == null) {
                log.info("Token中缺少用户信息: {}", path);
                return writeUnauthorizedResponse(exchange, "无效的Token，请重新登录");
            }

            // 5. 验证用户角色与请求头中的 Role 是否匹配
            String requestRole = request.getHeaders().getFirst("Role");
            if (requestRole != null && !role.toString().equals(requestRole)) {
                log.info("用户角色不匹配，拒绝访问: {}", path);
                return writeUnauthorizedResponse(exchange, "您的身份没有足够的访问权限，拒绝访问");
            }

            // 6. 将用户信息注入下游请求 Header
            ServerHttpRequest mutatedRequest = request.mutate()
                    .header("X-User-Id", userId.toString())
                    .header("X-User-Role", role.toString())
                    .build();

            return chain.filter(exchange.mutate().request(mutatedRequest).build());
        } catch (Exception e) {
            log.error("解析Token失败: {}", e.getMessage());
            return writeUnauthorizedResponse(exchange, "无效的Token，请重新登录");
        }
    }

    /**
     * 判断当前路径是否在白名单中
     * 路由配置了 StripPrefix=1，但过滤器执行在 StripPrefix 之前，
     * 所以需要将路径去掉第一级前缀（如 /api）再与白名单比较
     */
    private boolean isExcludedPath(String path) {
        // 去掉第一级路径前缀（如 /api/user/login -> /user/login）
        String strippedPath = stripFirstSegment(path);
        for (String pattern : excludePaths) {
            if (pathMatcher.match(pattern, strippedPath) || pathMatcher.match(pattern, path)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 去掉路径的第一级段落
     * 例如 /api/user/login -> /user/login
     */
    private String stripFirstSegment(String path) {
        if (path == null || path.length() <= 1) {
            return path;
        }
        int secondSlash = path.indexOf('/', 1);
        if (secondSlash == -1) {
            return "/";
        }
        return path.substring(secondSlash);
    }

    /**
     * 写入 401 未授权的 JSON 响应
     */
    private Mono<Void> writeUnauthorizedResponse(ServerWebExchange exchange, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);

        // 构造响应体。响应体内包括以下键值对：
        // - success: 表示请求是否成功（此处为 false）
        // - code: 响应状态码（此处为 401）
        // - msg: 提示信息（如 "请求未携带Token，请重新登录"）
        Map<String, Object> result = new HashMap<>();
        result.put("success", false);
        result.put("code", HttpStatus.UNAUTHORIZED.value());
        result.put("msg", message);

        String body = JSONUtil.toJsonStr(result);
        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    /**
     * 过滤器执行顺序：0
     * 在限流过滤器之后执行（限流优先级更高，Order=-1）
     */
    @Override
    public int getOrder() {
        return 0;
    }
}
