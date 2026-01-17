package org.kira.resumesystem;

import cn.hutool.json.JSONUtil;
import lombok.RequiredArgsConstructor;
import org.junit.jupiter.api.Test;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Scanner;

@SpringBootTest
class ResumeSystemApplicationTests {
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Test
    void any_test() {
        List<String> list = List.of("Java", "Python", "C++");
        System.out.println(list);   // 输出原始列表，元素没有引号
        String jsonStr = JSONUtil.toJsonStr(list);  // 使用JSONUtil将列表序列化为JSON字符串，每个元素都有引号
        System.out.println("Serialized JSON: " + jsonStr);
    }

}
