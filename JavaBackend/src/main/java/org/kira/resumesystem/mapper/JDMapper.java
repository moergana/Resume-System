package org.kira.resumesystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Param;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.po.JD;

public interface JDMapper extends BaseMapper<JD> {
    /**
     * 根据筛选条件分页查询JD列表
     * @param page 分页对象
     * @param condition 筛选条件
     * @return 分页后的JD列表
     */
    Page<JD> selectJDsByCondition(Page<JD> page, @Param("condition") FilterCondition condition);
}
