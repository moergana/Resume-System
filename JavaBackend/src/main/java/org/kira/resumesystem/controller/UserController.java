package org.kira.resumesystem.controller;

import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.service.IUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/user")
public class UserController {
    @Autowired
    private IUserService IUserService;

    @PostMapping("/login")
    public Result login(@RequestBody UserDTO userDTO) {
        log.info("User login attempt");
        return IUserService.login(userDTO);
    }

    @PostMapping("/register/emailCode")
    public Result sendRegisterEmailCode(@RequestBody UserDTO userDTO) {
        log.info("Sending registration email verification code");
        return IUserService.sendRegisterEmailCode(userDTO);
    }

    @PostMapping("/register")
    public Result register(@RequestBody UserDTO userDTO) {
        log.info("User registration attempt");
        return IUserService.register(userDTO);
    }

    @PostMapping("/resetPassword/emailCode")
    public Result sendResetPasswordEmailCode(@RequestBody UserDTO userDTO) {
        log.info("Sending email verification code");
        return IUserService.sendResetPasswordEmailCode(userDTO);
    }

    @PostMapping("/resetPassword")
    public Result resetPassword(@RequestBody UserDTO userDTO) {
        log.info("Resetting user password");
        return IUserService.resetPassword(userDTO);
    }

    @PostMapping("/modifyEmail/emailCode")
    public Result sendModifyEmailCode(@RequestBody UserDTO userDTO) {
        log.info("Sending email modification verification code");
        return IUserService.sendModifyEmailCode(userDTO);
    }

    @PostMapping("/modifyEmail")
    public Result modifyEmail(@RequestBody UserDTO userDTO) {
        log.info("Modifying user email");
        return IUserService.modifyEmail(userDTO);
    }
}
