package org.kira.resumesystem.utils;

import java.util.concurrent.TimeUnit;

public class RedisConstants {
    public static final String USER_LOGIN_KEY = "user:login:";  // 用户登录信息key前缀
    public static final String USER_LOGIN_HASH_ID = "userId";   // 用户登录缓存中用户ID的key
    public static final String USER_LOGIN_HASH_PASSWORD = "password";   // 用户登录缓存中用户密码的key
    public static final String USER_LOGIN_HASH_ROLE = "role";   // 用户登录缓存中用户角色的key
    public static final String USER_LOGIN_HASH_EMAIL = "email";   // 用户登录缓存中用户邮箱的key
    public static final String USER_LOGIN_HASH_CD = USER_LOGIN_KEY + "cd_flag"; // 用户登录冷却key前缀
    // 用户登录信息缓存的TTL和单位
    public static final Long USER_LOGIN_TTL = 10L;   // 10 分钟
    public static final TimeUnit USER_LOGIN_TTL_UNIT = TimeUnit.MINUTES;
    // 用户登录冷却时间的TTL和单位，避免用户频繁尝试登录
    public static final Long USER_LOGIN_CD_TTL = 2L;   // 2 秒
    public static final TimeUnit USER_LOGIN_CD_TTL_UNIT = TimeUnit.SECONDS;

    // 用户注册冷却时间的TTL和单位，避免用户频繁尝试注册重复用户名
    public static final String USER_REGISTER_CD_KEY = "user:register:"; // 防止用户频繁尝试注册重复用户名的冷却key前缀
    public static final Long USER_REGISTER_CD_TTL = 3L;   // 3 秒
    public static final TimeUnit USER_REGISTER_CD_TTL_UNIT = TimeUnit.SECONDS;

    // 邮箱验证码在Redis中的缓存key前缀和TTL
    public static final String EMAIL_REGISTER_CODE_KEY = "email:register:code:"; // 注册邮箱验证码key前缀
    public static final String EMAIL_RESET_PASSWORD_CODE_KEY = "email:resetPassword:code:"; // 邮箱验证码key前缀
    public static final String EMAIL_MODIFY_EMAIL_CODE_KEY = "email:modifyEmail:code:"; // 修改邮箱验证码key前缀
    public static final Long EMAIL_CODE_TTL = 10L;   // 10 分钟
    public static final TimeUnit EMAIL_CODE_TTL_UNIT = TimeUnit.MINUTES;

    // 通用的空值缓存TTL和单位，防止缓存穿透
    public static final Long COMMON_NULL_TTL = 5L;   // 5 分钟
    public static final TimeUnit COMMON_NULL_TTL_UNIT = TimeUnit.MINUTES;

    // 简历在Redis中的缓存key前缀和TTL
    public static final String RESUME_KEY = "resume:"; // 简历详情缓存的key前缀
    public static final Long RESUME_TTL = 1L;   // 1 小时
    public static final TimeUnit RESUME_TTL_UNIT = TimeUnit.HOURS;
    public static final String RESUME_LOCK_KEY = "resume:lock:"; // 简历分布式锁key前缀
    public static final Long RESUME_LOCK_WAIT_TIME = 10L;   // 10 秒
    public static final Long RESUME_LOCK_TTL = 10L;   // 10 秒
    public static final TimeUnit RESUME_LOCK_TTL_UNIT = TimeUnit.SECONDS;

    // JD在Redis中的缓存key前缀和TTL
    public static final String JD_KEY = "jd:"; // JD详情缓存的key前缀
    public static final Long JD_TTL = 1L;   // 1 小时
    public static final TimeUnit JD_TTL_UNIT = TimeUnit.HOURS;
    public static final String JD_LOCK_KEY = "jd:lock:"; // JD分布式锁key前缀
    public static final Long JD_LOCK_WAIT_TIME = 10L;   // 10 秒
    public static final Long JD_LOCK_TTL = 10L;   // 10 秒
    public static final TimeUnit JD_LOCK_TTL_UNIT = TimeUnit.SECONDS;

    // 简历分析结果在Redis中的缓存key前缀和TTL
    public static final String RESUME_ANALYSIS_KEY = "resume_analysis:"; // 简历分析结果key前缀
    public static final Long RESUME_ANALYSIS_TTL = 1L;   // 1 天
    public static final TimeUnit RESUME_ANALYSIS_TTL_UNIT = TimeUnit.DAYS;
    public static final String RESUME_ANALYSIS_LOCK_KEY = "resume_analysis:lock:"; // 简历分析分布式锁key前缀
    public static final Long RESUME_ANALYSIS_LOCK_WAIT_TIME = 10L;   // 10 秒
    public static final Long RESUME_ANALYSIS_LOCK_TTL = 10L;   // 10 秒
    public static final TimeUnit RESUME_ANALYSIS_LOCK_TTL_UNIT = TimeUnit.SECONDS;

    public static final String MATCH_RESULT_KEY = "match_result:"; // 简历JD匹配结果key前缀
    public static final String JD_MATCH_RESULT_KEY = "jd_match_result:"; // JD匹配结果key前缀
    public static final String RESUME_MATCH_RESULT_KEY = "resume_match_result:"; // 简历匹配结果key前缀
    public static final Long MATCH_RESULT_TTL = 1L;   // 1 天
    public static final TimeUnit MATCH_RESULT_TTL_UNIT = TimeUnit.DAYS;

    // Bucket4j-redis相关的Redis常量
    public static final String BUCKET4J_KEY_PREFIX = "rate_limit:bucket4j:"; // Bucket4j限流key前缀

    // Cuckoo Filter（布谷鸟过滤器）相关的Redis常量
    public static final String CUCKOO_FILTER_KEY_PREFIX = "cuckoo_filter:"; // Cuckoo Filter key前缀
    public static final String RESUME_CUCKOO_FILTER_KEY = CUCKOO_FILTER_KEY_PREFIX + "resume"; // 用于存储简历ID的Cuckoo Filter key
    public static final String JD_CUCKOO_FILTER_KEY = CUCKOO_FILTER_KEY_PREFIX + "jd"; // 用于存储JD ID的Cuckoo Filter key
    public static final String RESUME_ANALYSIS_CUCKOO_FILTER_KEY = CUCKOO_FILTER_KEY_PREFIX + "resume_analysis"; // 用于存储简历分析ID的Cuckoo Filter key
    public static final Long RESUME_CUCKOO_FILTER_CAPACITY = 1000000L; // 简历Cuckoo Filter初始容量
    public static final Long JD_CUCKOO_FILTER_CAPACITY = 1000000L; // JD Cuckoo Filter初始容量
    public static final Long RESUME_ANALYSIS_CUCKOO_FILTER_CAPACITY = 3000000L; // 简历分析Cuckoo Filter初始容量
    public static final Long CUCKOO_FILTER_BUCKETSIZE = 4L;
    public static final Long CUCKOO_FILTER_MAXITERATIONS = 20L;
    public static final Long CUCKOO_FILTER_EXPANSION = 1L;
}
