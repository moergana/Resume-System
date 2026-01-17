package org.kira.resumesystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.po.Resume;

public interface ResumeMapper extends BaseMapper<Resume> {
    /**
     * 根据筛选条件分页查询简历
     * @param page 分页参数
     * @param condition 筛选条件
     * @return 分页后的简历列表
     */
    Page<Resume> selectResumesByCondition(Page<Resume> page, @Param("condition") FilterCondition condition);
}
