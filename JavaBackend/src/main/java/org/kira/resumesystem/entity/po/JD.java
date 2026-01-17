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
@TableName(value = "tb_jd")
public class JD {
    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    /**
     * 用户ID
     */
    @TableField("user_id")
    private Long userId;

    /**
     * 职位标题
     */
    @TableField("title")
    private String title;

    /**
     * 公司名称
     */
    @TableField("company")
    private String company;

    /**
     * 工作地点
     */
    @TableField("location")
    private String location;

    /**
     * 薪资
     */
    @TableField("salary")
    private String salary;

    /**
     * 职位描述
     */
    @TableField("description")
    private String description;

    /**
     * 职位要求
     */
    @TableField("requirements")
    private String requirements;

    /**
     * 职位福利
     */
    @TableField("bonus")
    private String bonus;

    /**
     * JD文件路径(可选)
     * 如果有上传JD文件，则存储文件路径
     */
    @TableField("file_path")
    private String filePath;

    /**
     * 创建时间
     */
    @TableField("create_time")
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    @TableField("update_time")
    private LocalDateTime updateTime;
}
