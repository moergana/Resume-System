package org.kira.resumesystem.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.util.List;
@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
public class PageResult<T> {
    private Long pages;     // 总页数
    private Long total;     // 总记录数
    private Long current;   // 当前页码
    private Long size;      // 每页记录数(页面大小)
    private List<T> records;    // 当前页记录列表
}
