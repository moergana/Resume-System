package org.kira.resumesystem.utils;

import java.time.Duration;

public class Constants {
    // 用户角色对应的整数值
    public static final Integer CANDIDATE_ROLE = 0;
    public static final Integer RECRUITER_ROLE = 1;

    // 简历分析状态对应的整数值
    public static final Integer RESUME_ANALYSIS_WAITING_STATUS = 0;
    public static final Integer RESUME_ANALYSIS_ANALYSING_STATUS = 1;
    public static final Integer RESUME_ANALYSIS_FINISHED_STATUS = 2;
    public static final Integer RESUME_ANALYSIS_FAILED_STATUS = 3;

    // 各种请求类型对应的字符串常量值
    public static final String REQUEST_RESUME_UPLOAD = "resume_upload";
    public static final String REQUEST_JD_UPLOAD = "jd_upload";
    public static final String REQUEST_RESUME_JD_DIFFER = "resume_jd_differ";
    public static final String REQUEST_RESUME_ADVISE = "resume_advise";
    public static final String REQUEST_JD_MATCH = "jd_match";
    public static final String REQUEST_RESUME_MATCH = "resume_match";
    public static final String REQUEST_RESUME_DELETE = "resume_delete";
    public static final String REQUEST_JD_DELETE = "jd_delete";

    // Bucket限流参数
    public static final Integer BUCKET_CAPACITY = 100;           // 桶的容量
    public static final Integer BUCKET_REFILL_TOKENS = 5;      // 每次补充的令牌数
    public static final Duration BUCKET_REFILL_PERIOD = Duration.ofSeconds(1);     // 补充令牌的时间间隔
    public static final Duration BUCKET_EXPIRATION = Duration.ofHours(1);     // 桶的过期时间
}
