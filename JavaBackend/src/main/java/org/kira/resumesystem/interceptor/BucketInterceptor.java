package org.kira.resumesystem.interceptor;

import cn.hutool.http.HttpStatus;
import cn.hutool.json.JSONUtil;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.BandwidthBuilder;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.BucketConfiguration;
import io.github.bucket4j.distributed.proxy.ProxyManager;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Supplier;

import static org.kira.resumesystem.utils.Constants.*;
import static org.kira.resumesystem.utils.RedisConstants.BUCKET4J_KEY_PREFIX;

@Slf4j
@Component
public class BucketInterceptor implements HandlerInterceptor {
    // 以下是基于Bucket4j的令牌桶限流实现代码，支持按IP地址限流
    // 但是以下方法存在缺陷：当有大量不同IP地址访问时，会导致buckets Map无限增长，可能引发内存问题
    // 同时，由于使用的是内存中的Map，无法在多实例部署时共享限流状态
    // 因此在生产环境中，建议使用分布式限流方案，如使用Redis等外部存储来维护限流状态

    // 每个IP地址对应一个Bucket，单独流量控制。注意要使用ConcurrentHashMap以保证Map操作的线程安全
    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

    /**
     * 创建一个限流桶
     * @param capacity 桶的容量
     * @param refillTokens 每次补充的令牌数
     * @param refillPeriod 补充令牌的时间周期
     * @return 限流桶
     */
    private Bucket createBucket(Integer capacity, Integer refillTokens, Duration refillPeriod) {
        Bandwidth bandwidth = BandwidthBuilder.builder()
                .capacity(capacity)
                .refillIntervally(refillTokens, refillPeriod)
                .build();
        return Bucket.builder()
                .addLimit(bandwidth)
                .build();
    }

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws Exception {
        String ip = request.getRemoteAddr();
        Bucket bucket = buckets.computeIfAbsent(
                ip, k -> createBucket(BUCKET_CAPACITY, BUCKET_REFILL_TOKENS, BUCKET_REFILL_PERIOD)
        );
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
