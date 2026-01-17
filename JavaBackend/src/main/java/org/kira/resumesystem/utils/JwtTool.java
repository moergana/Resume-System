package org.kira.resumesystem.utils;

import cn.hutool.jwt.JWT;
import cn.hutool.jwt.JWTValidator;
import cn.hutool.jwt.signers.JWTSigner;
import cn.hutool.jwt.signers.JWTSignerUtil;
import org.kira.resumesystem.config.JwtProperties;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.entity.po.User;
import org.springframework.stereotype.Component;

import java.security.KeyPair;
import java.time.Duration;
import java.util.Date;

@Component
public class JwtTool {
    private final JWTSigner jwtSigner;  // JWT 签名者
    private final Duration tokenTTL;    // token 有效期，单位为秒

    /**
     * 构造函数，初始化 JWT 签名者
     * @param keyPair 用于签名和验证 JWT 的密钥对，这里由 Spring 容器注入，需要提前在配置类中生成 KeyPair 并注册为 Bean。
     */
    public JwtTool(KeyPair keyPair, JwtProperties jwtProperties) {
        this.jwtSigner = JWTSignerUtil.createSigner("rs256", keyPair);
        this.tokenTTL = Duration.ofSeconds(jwtProperties.getTokenTTL());
    }

    /**
     * 创建 token
     * @param userId 用户 ID
     * @return 生成的 token 字符串
     */
    public String createToken(User user) {
        Long userId = user.getId();
        Integer role = user.getRole();
        return JWT.create()
                .setPayload("user_id", userId)  // setPayload() 方法用于设置 JWT 的负载部分，这里我们设置了一个键为 "user_id" 的负载，值为传入的 userId 参数。需要注意这个字段是可以被解码出来的，所以不应该存放敏感信息。
                .setPayload("role", role)
                .setExpiresAt(new Date(System.currentTimeMillis() + tokenTTL.toMillis()))    // setExpiresAt() 方法用于设置过期时间。这个时间是一个 Date 对象，表示 JWT 过期时刻。在这里，我们通过当前时间加上传入的 ttl（有效期）来计算过期时刻。
                .setSigner(jwtSigner)   // setSigner() 方法用于设置签名者
                .sign();    // sign() 方法用于生成最终的 JWT 字符串
    }

    /**
     * 解析 token
     * @param token token 字符串
     * @return 解析 token 得到的用户 ID
     */
    public User parseToken(String token) {
        // 1. 判断token是否存在
        if (token == null) {
            throw new RuntimeException("用户未登录");
        }
        // 2. 根据token生成jwt对象
        JWT jwt;
        try {
            jwt = JWT.of(token).setSigner(jwtSigner);
        } catch (Exception e) {
            throw new RuntimeException("无效的token", e);
        }
        // 3. 验证jwt是否合法
        if (!jwt.verify()) {
            throw new RuntimeException("无效的token");
        }
        // 4. 验证jwt是否过期
        try {
            JWTValidator.of(jwt).validateDate();
        } catch (Exception e) {
            throw new RuntimeException("token已过期");
        }
        // 5. 获取用户信息： user_id 和 role
        Object userId = jwt.getPayload("user_id");
        Object role = jwt.getPayload("role");
        if (userId == null) {
            throw new RuntimeException("无效的token");
        }
        // 6. 返回用户信息
        try {
            User user = new User();
            user.setId(Long.valueOf(userId.toString()));
            user.setRole(Integer.valueOf(role.toString()));
            return user;
        } catch (NumberFormatException e) {
            throw new RuntimeException("无效的token");
        }
    }
}
