package org.kira.resumesystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.entity.po.User;

public interface IUserService extends IService<User> {
    Result login(UserDTO userDTO);

    Result register(UserDTO userDTO);

    Result sendResetPasswordEmailCode(UserDTO userDTO);

    Result resetPassword(UserDTO userDTO);

    Result modifyEmail(UserDTO userDTO);

    Result sendModifyEmailCode(UserDTO userDTO);

    Result sendRegisterEmailCode(UserDTO userDTO);
}
