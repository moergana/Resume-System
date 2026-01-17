package org.kira.resumesystem.config;

import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Slf4j
@Data
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {
    private String location;    // 密钥存放位置
    private String alias;       // 密钥别名
    private String password;    // 密钥密码
    private Integer tokenTTL;    // token有效期，单位为秒
}
