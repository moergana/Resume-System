package org.kira.resumesystem.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 用于封装筛选条件的DTO类
 */
@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
public class FilterCondition {
    private Long id = null;  // id筛选条件，用于模糊匹配
    private Long userId = null;  // userId筛选条件。用于模糊匹配
    private String resumeKeyword = null;  // 简历关键词筛选条件，可用于模糊匹配
    private String jdKeyword = null;  // JD关键词筛选条件，可用于模糊匹配
    private List<String> requestType = null;  // 请求类型筛选条件
    private List<Integer> status = null;  // 状态筛选条件
    private Double min_salary = null;   // 最低薪资筛选条件
    private Double max_salary = null;   // 最高薪资筛选条件
    private String period = null;        // 发放薪资的周期筛选条件
    private LocalDateTime startCreateTime = null;   // 起始创建时间筛选条件
    private LocalDateTime endCreateTime = null;     // 终止创建时间筛选条件
    private LocalDateTime startUpdateTime = null;   // 起始更新时间筛选条件
    private LocalDateTime endUpdateTime = null;     // 终止更新时间筛选条件
}
