package org.kira.resumesystem.utils;

import java.time.Duration;

public class Constants {
    // 用户角色对应的整数值
    public static final Integer CANDIDATE_ROLE = 0;    // 求职者角色
    public static final Integer RECRUITER_ROLE = 1;    // 招聘者角色

    // 支持处理的相关文件后缀名
    public static final String PDF_FILE_SUFFIX = ".pdf";    // PDF文件后缀名
    public static final String DOC_FILE_SUFFIX = ".doc";    // DOC文件后缀名
    public static final String DOCX_FILE_SUFFIX = ".docx";  // DOCX文件后缀名
    public static final String PPT_TILE_SUFFIX = ".ppt";    // PPT文件后缀名
    public static final String PPTX_TILE_SUFFIX = ".pptx";  // PPTX文件后缀名
    // 支持的图片文件后缀名列表
    public static final String[] IMAGE_FILE_SUFFIX_LIST = new String[] {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"
    };
    // 支持上传的文件后缀名列表
    public static final String[] SUPPORTED_FILE_UPLOAD_SUFFIX_LIST = new String[] {
        PDF_FILE_SUFFIX, DOC_FILE_SUFFIX, DOCX_FILE_SUFFIX, PPT_TILE_SUFFIX, PPTX_TILE_SUFFIX
    };
    
    // 简历分析状态对应的整数值
    public static final Integer RESUME_ANALYSIS_WAITING_STATUS = 0;    // 等待分析状态
    public static final Integer RESUME_ANALYSIS_ANALYSING_STATUS = 1;   // 分析中状态
    public static final Integer RESUME_ANALYSIS_FINISHED_STATUS = 2;    // 分析完成状态
    public static final Integer RESUME_ANALYSIS_FAILED_STATUS = 3;      // 分析失败状态

    // 各种请求类型对应的字符串常量值
    public static final String REQUEST_RESUME_UPLOAD = "resume_upload";    // 简历上传请求
    public static final String REQUEST_JD_UPLOAD = "jd_upload";            // 招聘信息上传请求
    public static final String REQUEST_RESUME_JD_DIFFER = "resume_jd_differ";    // 简历与招聘信息对比请求
    public static final String REQUEST_RESUME_ADVISE = "resume_advise";    // 简历优化建议请求
    public static final String REQUEST_JD_MATCH = "jd_match";            // 招聘信息匹配请求
    public static final String REQUEST_RESUME_MATCH = "resume_match";    // 简历匹配请求
    public static final String REQUEST_RESUME_DELETE = "resume_delete";    // 简历删除请求
    public static final String REQUEST_JD_DELETE = "jd_delete";            // 招聘信息删除请求

    // Bucket限流参数
    public static final Integer BUCKET_CAPACITY = 100;           // 桶的容量
    public static final Integer BUCKET_REFILL_TOKENS = 5;        // 每次补充的令牌数
    public static final Duration BUCKET_REFILL_PERIOD = Duration.ofSeconds(1);     // 补充令牌的时间间隔
    public static final Duration BUCKET_EXPIRATION = Duration.ofHours(1);     // 桶的过期时间
}
