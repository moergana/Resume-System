package org.kira.gateway.config;

import io.github.bucket4j.distributed.ExpirationAfterWriteStrategy;
import io.github.bucket4j.distributed.proxy.ProxyManager;
import io.github.bucket4j.redis.lettuce.Bucket4jLettuce;
import io.lettuce.core.RedisClient;
import io.lettuce.core.RedisURI;
import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.codec.ByteArrayCodec;
import io.lettuce.core.codec.RedisCodec;
import io.lettuce.core.codec.StringCodec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * Bucket4j 分布式限流配置
 * 基于 Lettuce 连接 Redis，为限流桶提供持久化存储
 */
@Configuration
public class RateLimitConfig {
    @Value("${spring.redis.host}")
    private String host;
    @Value("${spring.redis.port}")
    private int port;
    @Value("${spring.redis.password}")
    private String password;
    @Value("${spring.redis.database}")
    private int database;

    @Bean
    public ProxyManager<String> bucket4jProxyManager(RateLimitProperties rateLimitProperties) {
        RedisURI redisURI = RedisURI.Builder.redis(host)
                .withPort(port)
                .withPassword(password.toCharArray())
                .withDatabase(database)
                .build();
        RedisClient redisClient = RedisClient.create(redisURI);
        StatefulRedisConnection<String, byte[]> connection = redisClient.connect(
                RedisCodec.of(StringCodec.UTF8, new ByteArrayCodec())
        );
        Duration expiration = Duration.ofHours(rateLimitProperties.getBucketExpirationHours());
        return Bucket4jLettuce.casBasedBuilder(connection)
                .expirationAfterWrite(
                        ExpirationAfterWriteStrategy.basedOnTimeForRefillingBucketUpToMax(expiration)
                )
                .build();
    }
}
