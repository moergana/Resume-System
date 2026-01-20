package org.kira.resumesystem.interceptor;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.po.User;
import org.kira.resumesystem.utils.JwtTool;
import org.kira.resumesystem.utils.UserThreadLocal;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 * 添加登录拦截器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AuthLoginInterceptor implements HandlerInterceptor {
    private final JwtTool jwtTool;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 1. 从请求的header中尝试获取JWT
        try {
            String jwt = request.getHeader("Authorization");
            Integer role = Integer.valueOf(request.getHeader("Role"));
            // 2. 如果没有获取到JWT，说明用户未登录，拒绝访问
            if (jwt == null || jwt.isEmpty()) {
                log.info("请求未携带Token，拒绝访问");
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                response.setHeader("Message", "请求未携带Token，请重新登录");
                return false;
            }
            // 3. 如果获取到JWT，则尝试解析JWT，验证其有效性
            User user = jwtTool.parseToken(jwt);
            // 4. JWT解析成功后，验证用户角色是否匹配
            if (!user.getRole().equals(role)) {
                log.info("用户角色不匹配，拒绝访问");
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                response.setHeader("Message", "您的身份没有足够的访问权限，拒绝访问");
                return false;
            }
            // 验证完毕后，将用户ID存入ThreadLocal，供后续业务使用
            UserThreadLocal.set(user.getId());
            // 创建一个新的JWT并放入响应头，延长用户会话
            String newJwt = jwtTool.createToken(user);
            response.setHeader("Authorization", newJwt);
        } catch (Exception e) {
            log.error("解析Token失败: {}", e.getMessage());
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setHeader("Message", "无效的Token，请重新登录");
            return false;
        }
        // 4. JWT有效，允许访问
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) throws Exception {
        // 清理ThreadLocal中的用户信息，防止内存泄漏
        UserThreadLocal.remove();
    }
}
