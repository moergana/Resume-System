package org.kira.resumesystem.controller;

import org.junit.jupiter.api.Test;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.service.serviceImpl.JDServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
public class JDControllerTests {
    // @Autowired
    // private MockMvc mockMvc;    // MockMvc 用于模拟 HTTP 请求

    @Autowired
    private JDController jdController;

    @MockBean
    private JDServiceImpl jdService;   // Mock IJDService，避免真实调用

    /**
     * listJDs接口测试：有效测试用例
     */
    @Test
    public void list_valid() throws Exception {
        // 1. 模拟 listJDs 行为
        when(jdService.listJDs()).thenReturn(Result.success("found JDs successfully.", new ArrayList<>()));

        // 2. 执行请求并验证
        // 对于大量记录的方法，单元测试不应该依赖真实数据量，而是验证交互和结构
        /*mockMvc.perform(get("/jd/list"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));*/

        Result result = jdController.listJDs();
        assert result.getCode() == 200;
    }

    /**
     * uploadJDFile接口测试：有效测试用例
     */
    @Test
    public void upload_valid() throws Exception {
        // 1. 准备 MockMultipartFile
        // 参数名 "jd" 必须匹配 controller 中 @RequestParam("jd")
        MockMultipartFile file = new MockMultipartFile(
                "jd",
                "test.pdf",
                "application/pdf",
                "Hello, World!".getBytes()
        );

        // 2. 模拟 service 行为
        when(jdService.upload((MultipartFile) any())).thenReturn(Result.success("upload successfully"));

        // 3. 执行 upload 请求
        /*mockMvc.perform(multipart("/jd/upload/file").file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));*/
        Result result = jdController.uploadJDFile(file);
        assert result.getCode() == 200;
    }

    /**
     * deleteJDById接口测试：有效测试用例
     */
    @Test
    public void delete_valid() throws Exception {
        Long id = 1L;
        // 1. 模拟 delete 行为
        when(jdService.deleteJDById(id)).thenReturn(Result.success("delete successfully"));

        // 2. 执行 delete 请求
        // 此时由于 Service 是 Mock 的，所以不会真实删除数据库或文件，避免了污染
        /*mockMvc.perform(delete("/jd/" + id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(200));*/
        Result result = jdController.deleteJDById(id);
        assert result.getCode() == 200;
    }
}
