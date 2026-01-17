package org.kira.resumesystem.config.mq;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 消息序列化配置类
 * 由于AMQP中默认使用的是JDK自带的序列化，存在很多问题，所以建议自行替换Converter
 * 这里使用的是Jackson2JsonMessageConverter，将消息转换为JSON格式
 */
@Configuration
public class SerializeConfig {
    @Bean
    public MessageConverter jackson2JsonMessageConverter() {
        // Jackson2JsonMessageConverter默认不支持LocalDateTime和LocalDate的序列化和反序列化，若需要支持，可以自行配置ObjectMapper
        // 1. 创建ObjectMapper
        ObjectMapper objectMapper = new ObjectMapper();
        // 2. 注册 JavaTimeModule 以支持Java 8日期时间类型
        objectMapper.registerModule(new JavaTimeModule());
        // 默认情况下，JavaTimeModule会将日期时间类型序列化为数组，如果需要将其序列化为字符串，可以禁用WRITE_DATES_AS_TIMESTAMPS特性
        objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        // 3. 创建Jackson2JsonMessageConverter并设置ObjectMapper
        return new Jackson2JsonMessageConverter(objectMapper);
    }
}
