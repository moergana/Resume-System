package org.kira.resumesystem.config;

import io.github.bucket4j.distributed.ExpirationAfterWriteStrategy;
import io.github.bucket4j.distributed.proxy.ProxyManager;
import io.github.bucket4j.redis.lettuce.Bucket4jLettuce;
import io.github.bucket4j.redis.lettuce.cas.LettuceBasedProxyManager;
import io.lettuce.core.RedisClient;
import io.lettuce.core.RedisURI;
import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.codec.ByteArrayCodec;
import io.lettuce.core.codec.RedisCodec;
import io.lettuce.core.codec.StringCodec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;

import java.time.Duration;

import static org.kira.resumesystem.utils.Constants.BUCKET_EXPIRATION;

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

    /**
     * 配置Bucket4j的ProxyManager，实现分布式限流（基于Lettuce连接Redis）
     * @return ProxyManager<String>
     */
    @Bean
    public ProxyManager<String> bucket4jProxyManager() {
        // 配置Redis连接
        RedisURI redisURI = RedisURI.Builder.redis(host)
                .withPort(port)
                .withPassword(password.toCharArray())
                .withDatabase(database)
                .build();
        // 创建Redis客户端
        RedisClient redisClient = RedisClient.create(redisURI);
        // 建立Redis连接
        StatefulRedisConnection<String, byte[]> connection = redisClient.connect(
                RedisCodec.of(StringCodec.UTF8, new ByteArrayCodec())
        );
        // 创建并返回LettuceBasedProxyManager
        return Bucket4jLettuce.casBasedBuilder(connection)
                // 设置桶的过期策略
                .expirationAfterWrite(
                        ExpirationAfterWriteStrategy.basedOnTimeForRefillingBucketUpToMax(BUCKET_EXPIRATION)
                )
                .build();
    }
}
