package org.kira.resumesystem.advice;

import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.exceptions.*;
import org.kira.resumesystem.utils.WebUtils;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.ObjectError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.util.NestedServletException;

import java.net.BindException;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 全局异常处理
 * 该类用于捕获和处理应用程序中的全局异常，确保系统的稳定性和用户体验。
 */
@RestControllerAdvice
@Slf4j
public class ExceptionAdvice {
    /**
     * 处理通用异常
     * @param e 通用异常对象
     * @return 包含错误信息的响应实体
     */
    private ResponseEntity<Result> processResponse(CommonException e){
        return ResponseEntity.status(e.getCode()).body(Result.fail(e.getMessage()));
    }

    /**
     * 处理数据库异常
     * @param e 数据库异常对象
     * @return 包含错误信息的响应实体
     */
    @ExceptionHandler(DbException.class)
    public Object handleDbException(DbException e) {
        log.error("数据库异常：", e);
        return processResponse(e);
    }

    /**
     * 处理文件处理异常
     * @param e 文件处理异常对象
     * @return 包含错误信息的响应实体
     */
    @ExceptionHandler(FileException.class)
    public Object handleFileException(FileException e) {
        log.error("文件处理异常：", e);
        return processResponse(e);
    }

    /**
     * 处理未授权异常
     * @param e 未授权异常对象
     * @return 包含错误信息的响应实体
     */
    @ExceptionHandler(UnauthorizedException.class)
    public Object handleUnauthorizedException(UnauthorizedException e) {
        log.error("未授权异常：", e);
        return processResponse(e);
    }

    /**
     * 处理错误请求异常
     * @param e 错误请求异常对象
     * @return 包含错误信息的响应实体
     */
    @ExceptionHandler(BadRequestException.class)
    public Object handleBadRequestException(BadRequestException e) {
        log.error("错误请求异常：", e);
        return processResponse(e);
    }

    /**
     * 处理禁止访问异常
     * @param e 禁止访问异常对象
     * @return 包含错误信息的响应实体
     */
    @ExceptionHandler(ForbiddenException.class)
    public Object handleForbiddenException(ForbiddenException e) {
        log.error("禁止访问异常：", e);
        return processResponse(e);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Object handleMethodArgumentNotValidException(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getAllErrors()
                .stream().map(ObjectError::getDefaultMessage)
                .collect(Collectors.joining("|"));
        log.error("请求参数校验异常 -> {}", msg);
        log.debug("", e);
        return processResponse(new BadRequestException(msg));
    }

    @ExceptionHandler(BindException.class)
    public Object handleBindException(BindException e) {
        log.error("请求参数绑定异常 ->BindException， {}", e.getMessage());
        log.debug("", e);
        return processResponse(new BadRequestException("请求参数格式错误"));
    }

    @ExceptionHandler(NestedServletException.class)
    public Object handleNestedServletException(NestedServletException e) {
        log.error("参数异常 -> NestedServletException，{}", e.getMessage());
        log.debug("", e);
        return processResponse(new BadRequestException("请求参数处理异常"));
    }

    @ExceptionHandler(Exception.class)
    public Object handleRuntimeException(Exception e) {
        log.error("其他异常 uri : {} -> ", Objects.requireNonNull(WebUtils.getRequest()).getRequestURI(), e);
        return processResponse(new CommonException("服务器内部异常", 500));
    }

    @ExceptionHandler(CommonException.class)
    public Object handleBadRequestException(CommonException e) {
        log.error("自定义异常 -> {} , 异常原因：{}  ",e.getClass().getName(), e.getMessage());
        log.debug("", e);
        return processResponse(e);
    }

}
