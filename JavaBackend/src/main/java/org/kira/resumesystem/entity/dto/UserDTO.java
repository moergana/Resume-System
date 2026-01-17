package org.kira.resumesystem.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
public class UserDTO {
    /**
     * 用户名
     */
    private String username = "";

    /**
     * 密码
     */
    private String password = "";

    /**
     * 角色 0-求职者 1-招聘者
     */
    private Integer role = -1;

    /**
     * 登录token
     */
    private String token = "";
}
