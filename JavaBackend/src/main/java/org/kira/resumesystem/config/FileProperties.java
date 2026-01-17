package org.kira.resumesystem.config;

import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Slf4j
@Data
@ConfigurationProperties(prefix = "file")
public class FileProperties {
    private String resume_save_path; // 上传的简历文件保存路径
    private String jd_save_path;     // 上传的职位描述文件保存路径
}
