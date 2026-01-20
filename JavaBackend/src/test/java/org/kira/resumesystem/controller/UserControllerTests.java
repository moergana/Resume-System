package org.kira.resumesystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.junit.jupiter.api.Test;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.entity.po.User;
import org.kira.resumesystem.service.serviceImpl.UserServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
public class UserControllerTests {
    @Autowired
    private UserController userController;
    @Autowired
    private UserServiceImpl userServiceImpl;

    /**
     * 登录测试用例：有效用户名和密码
     */
    @Test
    public void Login_valid() throws InterruptedException {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("test");
        userDTO.setPassword("123");
        userDTO.setRole(0);
        Result result = userController.login(userDTO);
        if (result.getCode() != 200) {
            System.out.println("Login_valid Error: " + result.getMessage());
            Thread.sleep(4000);     // 可能是多次无效用例触发了冷却时间，等待几个秒后重试
            result = userController.login(userDTO);
        }
        assert result.getCode() == 200;
    }

    /**
     * 登录测试用例：空用户名
     */
    @Test
    public void Login_no_username() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("");
        userDTO.setPassword("wrongPassword");
        userDTO.setRole(0);
        Result result = userController.login(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 登录测试用例：错误用户名
     */
    @Test
    public void Login_error_username() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("wrongUsername");
        userDTO.setPassword("123");
        userDTO.setRole(0);
        Result result = userController.login(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 登录测试用例：空密码
     */
    @Test
    public void Login_no_password() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("test");
        userDTO.setPassword("");
        userDTO.setRole(0);
        Result result = userController.login(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 登录测试用例：错误密码
     */
    @Test
    public void Login_error_password() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("test");
        userDTO.setPassword("wrongPassword");
        userDTO.setRole(0);
        Result result = userController.login(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 登录测试用例：错误角色
     */
    @Test
    public void Login_error_role() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("test");
        userDTO.setPassword("123");
        userDTO.setRole(1);
        Result result = userController.login(userDTO);
        assert result.getCode() != 200;

        userDTO.setRole(2);
        result = userController.login(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 注册测试用例：有效用户名和密码
     */
    // @Test
    public void Register_valid() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("MockNewUser");
        userDTO.setPassword("MockNewPassword");
        userDTO.setRole(0);
        Result result = userController.register(userDTO);
        assert result.getCode() == 200;
        // 清理测试数据
        userServiceImpl.remove(new LambdaQueryWrapper<User>()
                .eq(User::getUsername, "MockNewUser")
                .eq(User::getPassword, "MockNewPassword")
                .eq(User::getRole, 0)
        );
    }

    /**
     * 注册测试用例：已存在的用户名
     */
    @Test
    public void Register_existing_username() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("test");
        userDTO.setPassword("SomePassword");
        userDTO.setRole(0);
        Result result = userController.register(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 注册测试用例：空用户名
     */
    @Test
    public void Register_empty_username() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("");
        userDTO.setPassword("SomePassword");
        userDTO.setRole(0);
        Result result = userController.register(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 注册测试用例：空密码
     */
    @Test
    public void Register_empty_password() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("NewUser");
        userDTO.setPassword("");
        userDTO.setRole(0);
        Result result = userController.register(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 注册测试用例：空角色
     */
    @Test
    public void Register_empty_role() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("NewUser");
        userDTO.setPassword("SomePassword");
        // 不设置角色
        Result result = userController.register(userDTO);
        assert result.getCode() != 200;
    }

    /**
     * 注册测试用例：无效角色
     */
    @Test
    public void Register_invalid_role() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("NewUser");
        userDTO.setPassword("SomePassword");
        userDTO.setRole(3); // 无效角色
        Result result = userController.register(userDTO);
        assert result.getCode() != 200;
    }
}
