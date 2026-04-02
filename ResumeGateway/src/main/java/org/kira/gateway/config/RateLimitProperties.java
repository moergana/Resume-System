package org.kira.gateway.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * 限流配置属性
 */
@Data
@Component
@ConfigurationProperties(prefix = "rate-limit")
public class RateLimitProperties {
    private BucketConfig ip;        // IP 级别限流参数
    private BucketConfig global;    // 全局限流参数
    private Integer bucketExpirationHours;  // 限流桶在 Redis 中的过期时间（小时）

    @Data
    public static class BucketConfig {
        private Integer capacity;       // 桶容量
        private Integer refillTokens;   // 每次补充的令牌数
        private Integer refillSeconds;  // 补充间隔（秒）
    }
}
