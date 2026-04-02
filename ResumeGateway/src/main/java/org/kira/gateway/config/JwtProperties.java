package org.kira.gateway.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * JWT 配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {
    private String location;        // 密钥库位置
    private String alias;           // 密钥别名
    private String password;        // 密钥密码
    private Integer tokenTTL;       // token 有效期（秒）
    private List<String> excludePaths;  // 不需要 JWT 验证的白名单路径
}
