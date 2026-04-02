package org.kira.resumesystem.interceptor;

import cn.hutool.json.JSONUtil;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.utils.UserThreadLocal;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.nio.charset.StandardCharsets;

/**
 * 内部用户信息解析拦截器
 * 从网关转发的请求 Header 中提取用户信息（X-User-Id, X-User-Role），
 * 并存入 ThreadLocal，供后续业务层使用。
 *
 * 该拦截器替代了原来的 AuthLoginInterceptor。
 * JWT 认证逻辑已迁移到 Gateway 网关层统一处理，
 * 此处仅负责从网关注入的 Header 中读取已验证的用户身份。
 */
@Slf4j
@Component
public class InternalUserInterceptor implements HandlerInterceptor {

    @Value("${security.gateway.enabled:true}")
    private boolean gatewayProtectionEnabled;

    @Value("${security.gateway.internal-secret:}")
    private String internalSecret;

    @Value("${security.gateway.internal-secret-header:X-Internal-Secret}")
    private String internalSecretHeader;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 对预检请求直接放行
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        // 如果开启了网关密钥校验功能，则校验网关内部共享密钥，防止前端或第三方直接伪造用户头绕过网关
        if (gatewayProtectionEnabled && internalSecret != null && !internalSecret.isEmpty()) {
            String requestSecret = request.getHeader(internalSecretHeader);
            if (!internalSecret.equals(requestSecret)) {
                log.warn("非法请求来源，缺失或错误的网关内部密钥，uri={}", request.getRequestURI());
                writeUnauthorizedResponse(response, "请求来源非法，请通过网关访问");
                return false;
            }
        }

        // 从网关转发的 Header 中获取用户信息
        String userId = request.getHeader("X-User-Id");
        String userRole = request.getHeader("X-User-Role");

        if (userId == null || userId.isEmpty()) {
            log.warn("缺失 X-User-Id，拒绝访问，uri={}", request.getRequestURI());
            writeUnauthorizedResponse(response, "未携带用户身份信息，请重新登录");
            return false;
        }

        try {
            UserThreadLocal.set(Long.valueOf(userId));
        } catch (NumberFormatException e) {
            log.warn("无法解析 X-User-Id: {}", userId);
            writeUnauthorizedResponse(response, "用户身份信息无效，请重新登录");
            return false;
        }

        if (userRole == null || userRole.isEmpty()) {
            log.debug("请求未携带 X-User-Role，uri={}", request.getRequestURI());
        }

        // 允许请求继续（认证和限流已由网关完成）
        return true;
    }

    private void writeUnauthorizedResponse(HttpServletResponse response, String message) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        String responseBody = JSONUtil.toJsonStr(Result.fail(HttpServletResponse.SC_UNAUTHORIZED, message));
        response.getWriter().write(responseBody);
    }

    /**
     * 请求处理完成后清理 ThreadLocal，防止内存泄漏
     */
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        UserThreadLocal.remove();
    }
}
