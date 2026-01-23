package org.kira.resumesystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
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
    // 给Mybatis-Plus注册PaginationInnerInterceptor拦截器后，会自动根据传入的Page对象进行分页处理
    // 因此不需要在xml中手动编写分页逻辑，只需编写查询条件逻辑即可
    Page<ResumeAnalysis> pageSelectResumeAnalysisByCondition(Page<ResumeAnalysis> page, @Param("condition") FilterCondition condition);
}
