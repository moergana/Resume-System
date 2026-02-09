package org.kira.resumesystem.config;

import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;

@Slf4j
@Configuration
public class RedissonConfig {
    // 从application.yaml中获取连接Redis的配置属性
    @Value("${spring.redis.host}")
    private String host;
    @Value("${spring.redis.port}")
    private String port;
    @Value("${spring.redis.database}")
    private String database;
    @Value("${spring.redis.password}")
    private String password;

    /**
     * 配置Redisson客户端
     * @return Redisson客户端实例
     */
    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer().setAddress("redis://" + host + ":" + port);
        if (password != null && !password.isEmpty()) {
            config.useSingleServer().setPassword(password);
        }
        if (database != null && !database.isEmpty()) {
            try {
                config.useSingleServer().setDatabase(Integer.parseInt(database));
            } catch (NumberFormatException e) {
                log.error("Failed to parse database index: {}. Using default database 0.", database);
            }
        }
        config.useSingleServer()
                .setConnectionPoolSize(10)
                .setConnectionMinimumIdleSize(5)
                .setIdleConnectionTimeout(10000)
                .setConnectTimeout(5000)
                .setTimeout(3000)
                .setRetryAttempts(3)
                .setRetryInterval(1000);
        return Redisson.create(config);
    }
}
