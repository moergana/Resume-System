package org.kira.resumesystem.config.mq;

import org.kira.resumesystem.utils.UserThreadLocal;
import org.springframework.amqp.core.MessagePostProcessor;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * RabbitTemplate配置类
 * 用于配置生产者和消费者的消息后置处理器，以实现用户信息（或其他信息）的自动传递和自动解析
 */
@Configuration
public class RabbitTemplateConfig {
    /**
     * 生产者的消息后置处理器
     * 在消息发送前，将用户信息添加到消息头中
     * @return MessagePostProcessor
     */
    @Bean
    public MessagePostProcessor producerMessagePostProcessor() {
        return message -> {
            // 将用户ID保存到消息的headers中，供消费者使用
            Long userID = UserThreadLocal.get();
            if(userID != null) {
                message.getMessageProperties().setHeader("userID", userID);
            }
            return message;
        };
    }

    /**
     * 配置RabbitTemplate，添加消息后置处理器
     * @param connectionFactory ConnectionFactory
     * @param producerMessagePostProcessor MessagePostProcessor
     * @return RabbitTemplate
     */
    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory, MessagePostProcessor producerMessagePostProcessor, MessageConverter messageConverter) {
        RabbitTemplate rabbitTemplate = new RabbitTemplate(connectionFactory);
        // 设置消息后置处理器。注意这是对rabbitTemplate发送的所有消息生效的全局性配置
        // 需要注意：rabbitTemplate的内部维护了一个消息处理器队列（类似于拦截器队列），允许添加多个消息处理器
        rabbitTemplate.setBeforePublishPostProcessors(producerMessagePostProcessor);
        // 手动设置消息转换器（该消息转换器在SerializeConfig.java中定义，为Jackson2JsonMessageConverter）
        rabbitTemplate.setMessageConverter(messageConverter);
        return rabbitTemplate;
    }

    /**
     * 消费者的消息后置处理器
     * 在消息接收后，从消息头中提取用户信息进行处理
     * @return MessagePostProcessor
     */
    @Bean
    public MessagePostProcessor consumerMessagePostProcessor() {
        return message -> {
            // 消费者端可以从消息头中获取用户ID进行处理
            Object userID = message.getMessageProperties().getHeaders().get("userID");
            if(userID != null) {
                // 这里可以根据需要将userID设置到线程上下文中，供后续处理使用
                Long uid = Long.valueOf(userID.toString());
                UserThreadLocal.set(uid);
            }
            return message;
        };
    }

    /**
     * 配置消费者的RabbitListenerContainerFactory，添加消息后置处理器
     * @param connectionFactory ConnectionFactory
     * @param consumerMessagePostProcessor MessagePostProcessor
     * @return SimpleRabbitListenerContainerFactory
     */
    @Bean
    public SimpleRabbitListenerContainerFactory consumerRabbitTemplate(ConnectionFactory connectionFactory, MessagePostProcessor consumerMessagePostProcessor, MessageConverter messageConverter) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        factory.setConnectionFactory(connectionFactory);
        // 设置消费者端的消息后置处理器
        factory.setAfterReceivePostProcessors(consumerMessagePostProcessor);
        // 手动设置消息转换器（该消息转换器在SerializeConfig.java中定义，为Jackson2JsonMessageConverter）
        factory.setMessageConverter(messageConverter);
        return factory;
    }
}
