package org.kira.resumesystem.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

@Data
@Accessors(chain = true)
@AllArgsConstructor
@NoArgsConstructor
public class Result {
    /**
     * 状态码
     */
    private Integer code;

    /**
     * 提示信息
     */
    private String message;

    /**
     * 返回的数据内容
     */
    private Object data;

    /**
     * 生成成功结果对象，默认状态码200
     * @param data 返回的数据内容
     * @return 成功结果对象
     */
    static public Result success(Object data) {
        return new Result(200, "Success", data);
    }

    /**
     * 生成成功结果对象，默认状态码200，包含提示信息和数据内容
     * @param message 提示信息
     * @param data 返回的数据内容
     * @return 成功结果对象
     */
    static public Result success(String message, Object data) {
        return new Result(200, message, data);
    }

    /**
     * 生成失败结果对象，需自行指定状态码
     * @param code 状态码
     * @param message 提示信息
     * @return 失败结果对象
     */
    static public Result fail(Integer code, String message) {
        return new Result(code, message, null);
    }

    /**
     * 生成失败结果对象，默认状态码500
     * @param message 提示信息
     * @return 失败结果对象
     */
    static public Result fail(String message) {
        return new Result(500, message, null);
    }
}
