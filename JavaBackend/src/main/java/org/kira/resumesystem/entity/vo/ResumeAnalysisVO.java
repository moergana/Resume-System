package org.kira.resumesystem.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * ResumeAnalysis View Object，用于保存前端展示所需的关于ResumeAnalysis的信息
 */
@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
public class ResumeAnalysisVO {
    /**
     * ID，主键，用于唯一标识一条简历分析记录
     */
    private Long id = 0L;

    /**
     * 用户ID (对于真实的用户数据，userId应该大于0)
     */
    private Long userId = 0L;

    /**
     * 请求类型（如“简历分析建议”使用resume_advise）
     */
    private String requestType = "";

    /**
     * 简历ID (对于真实的简历数据，resumeId应该大于0)
     */
    private Long resumeId = 0L;

    /**
     * 简历名称（用于前端向用户展示）
     */
    private String resumeName = "";

    /**
     * JD ID (对于真实的JD数据，jdID应该大于0)
     */
    private Long jdId = 0L;

    /**
     * JD名称（用于前端向用户展示）
     */
    private String jdName = "";

    /**
     * 职位标题
     */
    private String title = "";

    /**
     * 公司名称
     */
    private String company = "";

    /**
     * 工作地点
     */
    private String location = "";

    /**
     * 薪资
     */
    private String salary = "";

    /**
     * 职位描述
     */
    private String description = "";

    /**
     * 职位要求
     */
    private String requirements = "";

    /**
     * 职位福利
     */
    private String bonus = "";

    /**
     * 分析状态（0：待分析，1：分析中，2：分析完成，3：分析失败）
     */
    private Integer status = -1;

    /**
     * 分析结果（JSON格式）
     */
    private String analysisResult = "";

    /**
     * 检索到的相似简历信息列表
     */
    private List<Map<String, Object>> retrievedResumes = Collections.emptyList();

    /**
     * 检索到的相似JD信息列表
     */
    private List<Map<String, Object>> retrievedJds = Collections.emptyList();

    /**
     * 创建时间
     */
    private LocalDateTime createTime = LocalDateTime.now();
}
