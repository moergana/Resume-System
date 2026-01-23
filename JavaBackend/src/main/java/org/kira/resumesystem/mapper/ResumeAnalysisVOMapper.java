package org.kira.resumesystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.vo.ResumeAnalysisVO;

public interface ResumeAnalysisVOMapper extends BaseMapper<ResumeAnalysisVO> {
    /**
     * 根据条件分页查询简历分析记录的VO对象
     * @param page 分页对象
     * @param condition 筛选条件
     * @return 分页结果
     */
    Page<ResumeAnalysisVO> pageSelectResumeAnalysisVOByCondition(Page<ResumeAnalysisVO> page, @Param("condition") FilterCondition condition);
}
