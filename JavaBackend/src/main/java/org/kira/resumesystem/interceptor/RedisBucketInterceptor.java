package org.kira.resumesystem.interceptor;

import cn.hutool.http.HttpStatus;
import cn.hutool.json.JSONUtil;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.BandwidthBuilder;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.BucketConfiguration;
import io.github.bucket4j.distributed.proxy.ProxyManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.function.Supplier;

import static org.kira.resumesystem.utils.Constants.*;
import static org.kira.resumesystem.utils.RedisConstants.BUCKET4J_KEY_PREFIX;

@Slf4j
@Component
@RequiredArgsConstructor
public class RedisBucketInterceptor implements HandlerInterceptor {
    // 以下是基于Bucket4j-redis的分布式令牌桶限流实现代码
    // 相比基于内存的限流方案，分布式限流可以在多实例部署时共享限流状态
    // 同时，限流桶的状态存储在Redis中，并在创建的时候设置过期时间（ProxyManager中设置），避免占用空间无限增长的问题

    // 使用Bucket4j-redis实现分布式令牌桶限流，redis客户端使用lettuce
    private final ProxyManager<String> bucket4jProxyManager;

    /**
     * 根据IP地址获取对应的限流桶，如果获取不到则创建一个新的桶
     * 创建Bucket时，使用ProxyManager创建新的限流桶，该桶的状态存储在Redis中
     * 因此需要传入IP地址构建Key，用于区分不同IP的限流状态
     * @param ip IP地址
     * @return 限流桶
     */
    private Bucket getBucket(String ip) {
        // 定义桶的配置
        Bandwidth bandwidth = BandwidthBuilder.builder()
                .capacity(BUCKET_CAPACITY)
                .refillIntervally(BUCKET_REFILL_TOKENS, BUCKET_REFILL_PERIOD)
                .build();
        // 使用Supplier延迟创建BucketConfiguration
        Supplier<BucketConfiguration> bucketConfiguration = () -> BucketConfiguration.builder()
                .addLimit(bandwidth)
                .build();
        // 使用IP地址构建Redis中的Key
        String redisKey = BUCKET4J_KEY_PREFIX + ip;
        // 使用ProxyManager从Redis中获取或创建Bucket
        return bucket4jProxyManager.builder().build(redisKey, bucketConfiguration);
    }

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws Exception {
        // 获取请求的IP地址
        String ip = request.getRemoteAddr();
        // 从ProxyManager中获取对应IP的Bucket
        Bucket bucket = getBucket(ip);
        // 尝试从桶中消费一个令牌
        if (bucket.tryConsume(1)) {
            // 有令牌，允许访问
            return true;
        } else {
            // 无令牌，拒绝访问
            log.warn("IP {} 访问过于频繁，暂被限流", ip);
            response.setStatus(HttpStatus.HTTP_TOO_MANY_REQUESTS); // 429 Too Many Requests
            response.setContentType("application/json;charset=UTF-8");
            // 设置响应体内容
            Result result = Result.fail(HttpStatus.HTTP_TOO_MANY_REQUESTS, "请求过于频繁，请稍后再试");
            String resultJSON = JSONUtil.toJsonStr(result);
            response.getWriter().write(resultJSON);
            return false;
        }
    }
}
