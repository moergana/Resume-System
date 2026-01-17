package org.kira.resumesystem.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;

@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
public class JDDTO {
    /**
     * 主键
     */
    private Long id;

    /**
     * 所属的用户ID (对于真实的用户数据，userId应该大于0)
     */
    private Long userId = 0L;

    /**
     * 职位名称（用于前端向用户展示）
     */
    private String name = "";

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
     * 创建时间
     */
    private LocalDateTime createTime = LocalDateTime.now();

    /**
     * 更新时间
     */
    private LocalDateTime updateTime = LocalDateTime.now();
}
