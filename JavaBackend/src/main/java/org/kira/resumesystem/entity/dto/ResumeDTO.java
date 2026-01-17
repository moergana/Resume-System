package org.kira.resumesystem.entity.dto;

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
public class ResumeDTO {
    /**
     * 主键
     */
    private Long id;

    /**
     * 所属的用户ID (对于真实的用户数据，userId应该大于0)
     */
    private Long userId = 0L;

    /**
     * 简历名称（用于前端向用户展示）
     */
    private String name = "";

    /**
     * 创建时间
     */
    private LocalDateTime createTime = LocalDateTime.now();

    /**
     * 更新时间
     */
    private LocalDateTime updateTime = LocalDateTime.now();
}
