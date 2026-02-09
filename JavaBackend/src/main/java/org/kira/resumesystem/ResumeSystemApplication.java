package org.kira.resumesystem;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration;

@SpringBootApplication(exclude = { SecurityAutoConfiguration.class } // 关闭Spring Security默认的自动配置，采用手动编码配置
)
@MapperScan(value = "org.kira.resumesystem.mapper")
public class ResumeSystemApplication {

    public static void main(String[] args) {
        SpringApplication.run(ResumeSystemApplication.class, args);
    }

}
