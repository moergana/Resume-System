package org.kira.resumesystem;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan(value = "org.kira.resumesystem.mapper")
public class ResumeSystemApplication {

    public static void main(String[] args) {
        SpringApplication.run(ResumeSystemApplication.class, args);
    }

}
