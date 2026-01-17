package org.kira.resumesystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.entity.po.User;

public interface IUserService extends IService<User> {
    Result login(UserDTO userDTO);

    Result register(UserDTO userDTO);
}
