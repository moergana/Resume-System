package org.kira.resumesystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.po.ResumeAnalysis;

public interface ResumeAnalysisMapper extends BaseMapper<ResumeAnalysis> {
    /**
     * 根据条件分页查询简历分析记录
     * @param page 分页对象
     * @param condition 筛选条件
     * @return 分页结果
     */
    Page<ResumeAnalysis> selectResumeAnalysisByCondition(Page<ResumeAnalysis> page, @Param("condition") FilterCondition condition);
}
