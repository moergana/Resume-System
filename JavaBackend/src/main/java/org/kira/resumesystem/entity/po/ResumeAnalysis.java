package org.kira.resumesystem.entity.po;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;

@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
@TableName(value = "tb_resume_analysis")
public class ResumeAnalysis {
    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * 简历分析所属的用户ID
     */
    @TableField("user_id")
    private Long userId;

    /**
     * 被分析的简历ID
     */
    @TableField("resume_id")
    private Long resumeId;

    /**
     * 关联的JD ID
     */
    @TableField("jd_id")
    private Long jdID;

    /**
     * 请求类型（如“简历分析建议”使用resume_advise）
     */
    @TableField("request_type")
    private String requestType;

    /**
     * 分析状态（0：待分析，1：分析中，2：分析完成，3：分析失败）
     */
    @TableField("status")
    private Integer status;

    /**
     * 分析结果（JSON格式）
     */
    @TableField("analysis_result")
    private String analysisResult;

    /**
     * 检索到的简历内容（JSON格式的列表）
     */
    @TableField("retrieved_resumes")
    private String retrievedResumes;

    /**
     * 检索到的JD内容（JSON格式的列表）
     */
    @TableField("retrieved_jds")
    private String retrievedJds;

    /**
     * 创建时间
     */
    @TableField("create_time")
    private LocalDateTime createTime;
}
