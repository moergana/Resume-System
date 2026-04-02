package org.kira.gateway.filter;

import cn.hutool.json.JSONUtil;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.BandwidthBuilder;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.BucketConfiguration;
import io.github.bucket4j.distributed.proxy.ProxyManager;
import lombok.extern.slf4j.Slf4j;
import org.kira.gateway.config.RateLimitProperties;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;

/**
 * 全局限流过滤器
 * 实现两层限流机制：
 * 1. 全局令牌桶 —— 大容量、快恢复，防止多 IP 流量汇聚冲垮后端服务
 * 2. IP 级令牌桶 —— 限制单个 IP 的请求频率，防止恶意刷接口
 *
 * 执行优先级高于 JWT 认证过滤器（Order=-1），
 * 确保即使是未认证的恶意请求也能被限流拦截
 */
@Slf4j
@Component
public class RateLimitGlobalFilter implements GlobalFilter, Ordered {

    private static final String BUCKET_KEY_PREFIX_IP = "gateway:rate_limit:ip:";
    private static final String BUCKET_KEY_GLOBAL = "gateway:rate_limit:global";

    private final ProxyManager<String> proxyManager;
    private final RateLimitProperties rateLimitProperties;

    public RateLimitGlobalFilter(ProxyManager<String> proxyManager,
                                  RateLimitProperties rateLimitProperties) {
        this.proxyManager = proxyManager;
        this.rateLimitProperties = rateLimitProperties;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // 1. 全局限流检查
        Bucket globalBucket = getGlobalBucket();
        if (!globalBucket.tryConsume(1)) {
            log.warn("全局流量已达上限，暂时限流");
            return writeTooManyRequestsResponse(exchange, "系统繁忙，请稍后再试");
        }

        // 2. IP 级限流检查
        String clientIp = getClientIp(exchange.getRequest());
        Bucket ipBucket = getIpBucket(clientIp);
        if (!ipBucket.tryConsume(1)) {
            log.warn("IP {} 访问过于频繁，暂被限流", clientIp);
            return writeTooManyRequestsResponse(exchange, "请求过于频繁，请稍后再试");
        }

        return chain.filter(exchange);
    }

    /**
     * 获取全局限流桶
     */
    private Bucket getGlobalBucket() {
        RateLimitProperties.BucketConfig config = rateLimitProperties.getGlobal();
        Bandwidth bandwidth = BandwidthBuilder.builder()
                .capacity(config.getCapacity())
                .refillIntervally(config.getRefillTokens(), Duration.ofSeconds(config.getRefillSeconds()))
                .build();
        Supplier<BucketConfiguration> bucketConfig = () -> BucketConfiguration.builder()
                .addLimit(bandwidth)
                .build();
        return proxyManager.builder().build(BUCKET_KEY_GLOBAL, bucketConfig);
    }

    /**
     * 获取指定 IP 的限流桶
     */
    private Bucket getIpBucket(String ip) {
        RateLimitProperties.BucketConfig config = rateLimitProperties.getIp();
        Bandwidth bandwidth = BandwidthBuilder.builder()
                .capacity(config.getCapacity())
                .refillIntervally(config.getRefillTokens(), Duration.ofSeconds(config.getRefillSeconds()))
                .build();
        Supplier<BucketConfiguration> bucketConfig = () -> BucketConfiguration.builder()
                .addLimit(bandwidth)
                .build();
        return proxyManager.builder().build(BUCKET_KEY_PREFIX_IP + ip, bucketConfig);
    }

    /**
     * 获取客户端真实 IP
     * 优先从 X-Forwarded-For 和 X-Real-Ip 头中获取（适用于有反向代理的场景），
     * 否则从连接中直接获取远端地址
     */
    private String getClientIp(ServerHttpRequest request) {
        // 尝试从常见的代理头中获取真实 IP
        String ip = request.getHeaders().getFirst("X-Forwarded-For");
        if (ip != null && !ip.isEmpty() && !"unknown".equalsIgnoreCase(ip)) {
            // X-Forwarded-For 可能包含多个 IP（逗号分隔），取第一个
            return ip.split(",")[0].trim();
        }
        ip = request.getHeaders().getFirst("X-Real-Ip");
        if (ip != null && !ip.isEmpty() && !"unknown".equalsIgnoreCase(ip)) {
            return ip;
        }
        // 从连接中获取
        InetSocketAddress remoteAddress = request.getRemoteAddress();
        if (remoteAddress != null && remoteAddress.getAddress() != null) {
            return remoteAddress.getAddress().getHostAddress();
        }
        return "unknown";
    }

    /**
     * 写入 429 Too Many Requests 的 JSON 响应
     */
    private Mono<Void> writeTooManyRequestsResponse(ServerWebExchange exchange, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> result = new HashMap<>();
        result.put("success", false);
        result.put("code", HttpStatus.TOO_MANY_REQUESTS.value());
        result.put("msg", message);

        String body = JSONUtil.toJsonStr(result);
        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    /**
     * 过滤器执行顺序：-1（优先于 JWT 认证过滤器）
     * 限流应在认证之前执行，确保恶意请求不会消耗认证逻辑的计算资源
     */
    @Override
    public int getOrder() {
        return -1;
    }
}
