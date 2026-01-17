package org.kira.resumesystem.config.mq;

import org.springframework.amqp.core.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

/**
 * RabbitMQ配置类
 * 负责配置RabbitMq的exchanges、queues和bindings等
 */
@Configuration
public class RabbitMqConfig {

    public static final String UPLOAD_EXCHANGE_NAME = "upload.direct";
    public static final String RESUME_UPLOAD_QUEUE_NAME = "resume.upload.queue";
    public static final String RESUME_UPLOAD_ROUTING_KEY = "resume.upload.routing";

    /**
     * 配置上传(upload)的Direct Exchange
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange uploadDirectExchange() {
        return ExchangeBuilder.directExchange(UPLOAD_EXCHANGE_NAME)
                .durable(true) // 设置交换机为持久化
                .build();
    }

    /**
     * 配置简历上传的队列
     * @return Queue对象
     */
    @Bean
    public Queue resumeUploadQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", UPLOAD_DLX_NAME);
        args.put("x-dead-letter-routing-key", UPLOAD_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(RESUME_UPLOAD_QUEUE_NAME) // 设置队列为持久化
                .lazy() // 设置为懒加载队列，消息存储在磁盘上，减少内存使用
                .withArguments(args) // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 绑定简历上传队列到上传交换机
     * @param uploadDirectExchange 上传Direct Exchange
     * @param resumeUploadQueue 简历上传队列
     * @return Binding对象
     */
    @Bean
    public Binding resumeUploadBinding(DirectExchange uploadDirectExchange, Queue resumeUploadQueue) {
        return BindingBuilder
                .bind(resumeUploadQueue)
                .to(uploadDirectExchange)
                .with(RESUME_UPLOAD_ROUTING_KEY);
    }

    public static final String JD_UPLOAD_QUEUE_NAME = "jd.upload.queue";
    public static final String JD_UPLOAD_ROUTING_KEY = "jd.upload.routing";

    /**
     * 配置JD上传的队列
     * @return Queue对象
     */
    @Bean
    public Queue jdUploadQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", UPLOAD_DLX_NAME);
        args.put("x-dead-letter-routing-key", UPLOAD_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(JD_UPLOAD_QUEUE_NAME) // 设置队列为持久化
                .lazy() // 设置为懒加载队列，消息存储在磁盘上，减少内存使用
                .withArguments(args) // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 绑定JD上传队列到上传交换机
     * @param uploadDirectExchange 上传Direct Exchange
     * @param jdUploadQueue JD上传队列
     * @return Binding对象
     */
    @Bean
    public Binding jdUploadBinding(DirectExchange uploadDirectExchange, Queue jdUploadQueue) {
        return BindingBuilder
                .bind(jdUploadQueue)
                .to(uploadDirectExchange)
                .with(JD_UPLOAD_ROUTING_KEY);
    }


    public final static String ANALYSE_EXCHANGE_NAME = "analyse.direct";
    public final static String ANALYSE_REQUEST_QUEUE_NAME = "analyse.request.queue";
    public final static String ANALYSE_REQUEST_ROUTING_KEY = "analyse.request.routing";

    /**
     * 配置简历分析的Direct Exchange
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange analyseDirectExchange() {
        return ExchangeBuilder.directExchange(ANALYSE_EXCHANGE_NAME)
                .durable(true) // 设置交换机为持久化
                .build();
    }

    /**
     * 配置简历分析的队列
     * @return Queue对象
     */
    @Bean
    public Queue analyseQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", ANALYSE_DLX_NAME);
        args.put("x-dead-letter-routing-key", ANALYSE_REQUEST_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(ANALYSE_REQUEST_QUEUE_NAME) // 设置队列为持久化
                .lazy() // 设置为懒加载队列，消息存储在磁盘上，减少内存使用
                .withArguments(args)    // 可以在这里添加额外的队列参数
                .build();
    }

    @Bean
    public Binding analyseBinding(DirectExchange analyseDirectExchange, Queue analyseQueue) {
        return BindingBuilder
                .bind(analyseQueue)
                .to(analyseDirectExchange)
                .with(ANALYSE_REQUEST_ROUTING_KEY);
    }

    public static final String ANALYSE_RESULT_QUEUE_NAME = "analyse.result.queue";
    public static final String ANALYSE_RESULT_ROUTING_KEY = "analyse.result.routing";

    /**
     * 配置简历分析结果的队列
     * @return Queue对象
     */
    @Bean
    public Queue analyseResultQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", ANALYSE_DLX_NAME);
        args.put("x-dead-letter-routing-key", ANALYSE_RESULT_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(ANALYSE_RESULT_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }

    public static final String MATCH_EXCHANGE_NAME = "match.direct";
    public static final String JD_MATCH_REQUEST_QUEUE_NAME = "jd.match.request.queue";
    public static final String RESUME_MATCH_REQUEST_QUEUE_NAME = "resume.match.request.queue";
    public static final String JD_MATCH_REQUEST_ROUTING_KEY = "jd.match.request.routing";
    public static final String RESUME_MATCH_REQUEST_ROUTING_KEY = "resume.match.request.routing";

    /**
     * 配置匹配(match)请求的Direct Exchange
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange matchDirectExchange() {
        return ExchangeBuilder.directExchange(MATCH_EXCHANGE_NAME)
                .durable(true)
                .build();
    }

    /**
     * 配置JD匹配请求的队列
     * @return Queue对象
     */
    @Bean
    public Queue jdMatchQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", MATCH_DLX_NAME);
        args.put("x-dead-letter-routing-key", MATCH_REQUEST_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(JD_MATCH_REQUEST_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 配置简历匹配请求的队列
     * @return Queue对象
     */
    @Bean
    public Queue resumeMatchQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", MATCH_DLX_NAME);
        args.put("x-dead-letter-routing-key", MATCH_REQUEST_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(RESUME_MATCH_REQUEST_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 绑定JD匹配请求队列到匹配交换机
     * @param matchDirectExchange 匹配Direct Exchange
     * @param jdMatchQueue JD匹配请求队列
     * @return Binding对象
     */
    @Bean
    public Binding jdMatchBinding(DirectExchange matchDirectExchange, Queue jdMatchQueue) {
        return BindingBuilder
                .bind(jdMatchQueue)
                .to(matchDirectExchange)
                .with(JD_MATCH_REQUEST_ROUTING_KEY);
    }

    /**
     * 绑定简历匹配请求队列到匹配交换机
     * @param matchDirectExchange 匹配Direct Exchange
     * @param resumeMatchQueue 简历匹配请求队列
     * @return Binding对象
     */
    @Bean
    public Binding resumeMatchBinding(DirectExchange matchDirectExchange, Queue resumeMatchQueue) {
        return BindingBuilder
                .bind(resumeMatchQueue)
                .to(matchDirectExchange)
                .with(RESUME_MATCH_REQUEST_ROUTING_KEY);
    }

    public static final String JD_MATCH_RESULT_QUEUE_NAME = "jd.match.result.queue";
    public static final String JD_MATCH_RESULT_ROUTING_KEY = "jd.match.result.routing";
    public static final String RESUME_MATCH_RESULT_QUEUE_NAME = "resume.match.result.queue";
    public static final String RESUME_MATCH_RESULT_ROUTING_KEY = "resume.match.result.routing";

    /**
     * 配置JD匹配结果的队列
     * @return Queue对象
     */
    @Bean
    public Queue jdMatchResultQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", MATCH_DLX_NAME);
        args.put("x-dead-letter-routing-key", MATCH_RESULT_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(JD_MATCH_RESULT_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 配置简历匹配结果的队列
     * @return Queue对象
     */
    @Bean
    public Queue resumeMatchResultQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", MATCH_DLX_NAME);
        args.put("x-dead-letter-routing-key", MATCH_RESULT_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(RESUME_MATCH_RESULT_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }


    public static final String DELETE_EXCHANGE_NAME = "delete.direct";
    public static final String RESUME_DELETE_QUEUE_NAME = "resume.delete.queue";
    public static final String RESUME_DELETE_ROUTING_KEY = "resume.delete.routing";
    public static final String JD_DELETE_QUEUE_NAME = "jd.delete.queue";
    public static final String JD_DELETE_ROUTING_KEY = "jd.delete.routing";

    /**
     * 配置删除(delete)的Direct Exchange
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange deleteDirectExchange() {
        return ExchangeBuilder.directExchange(DELETE_EXCHANGE_NAME)
                .durable(true)
                .build();
    }

    /**
     * 配置简历删除的队列
     * @return Queue对象
     */
    @Bean
    public Queue resumeDeleteQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", DELETE_DLX_NAME);
        args.put("x-dead-letter-routing-key", DELETE_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(RESUME_DELETE_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 绑定简历删除队列到删除交换机
     * @param deleteDirectExchange 删除Direct Exchange
     * @param resumeDeleteQueue 简历删除队列
     * @return Binding对象
     */
    @Bean
    public Binding resumeDeleteBinding(DirectExchange deleteDirectExchange, Queue resumeDeleteQueue) {
        return BindingBuilder
                .bind(resumeDeleteQueue)
                .to(deleteDirectExchange)
                .with(RESUME_DELETE_ROUTING_KEY);
    }

    /**
     * 配置JD删除的队列
     * @return Queue对象
     */
    @Bean
    public Queue jdDeleteQueue() {
        // 配置额外的队列参数
        Map<String, Object> args = new HashMap<>();
        // 设置死信交换机和死信路由键
        args.put("x-dead-letter-exchange", DELETE_DLX_NAME);
        args.put("x-dead-letter-routing-key", DELETE_DLQ_ROUTING_KEY);

        return QueueBuilder
                .durable(JD_DELETE_QUEUE_NAME)
                .lazy()
                .withArguments(args)   // 可以在这里添加额外的队列参数
                .build();
    }

    /**
     * 绑定JD删除队列到删除交换机
     * @param deleteDirectExchange 删除Direct Exchange
     * @param jdDeleteQueue JD删除队列
     * @return Binding对象
     */
    @Bean
    public Binding jdDeleteBinding(DirectExchange deleteDirectExchange, Queue jdDeleteQueue) {
        return BindingBuilder
                .bind(jdDeleteQueue)
                .to(deleteDirectExchange)
                .with(JD_DELETE_ROUTING_KEY);
    }



    /******************
     * 死信交换机和死信队列的配置
     ******************/

    public static final String ANALYSE_DLX_NAME = "analyse.dlx";
    public static final String ANALYSE_REQUEST_DLQ_NAME = "analyse.request.dlq";
    public static final String ANALYSE_REQUEST_DLQ_ROUTING_KEY = "analyse.request.dlq.routing";
    public static final String ANALYSE_RESULT_DLQ_NAME = "analyse.result.dlq";
    public static final String ANALYSE_RESULT_DLQ_ROUTING_KEY = "analyse.result.dlq.routing";

    /**
     * 配置简历分析的死信交换机
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange analyseDLX() {
        return ExchangeBuilder.directExchange(ANALYSE_DLX_NAME)
                .durable(true)
                .build();
    }

    /**
     * 配置简历分析请求的死信队列
     * @return Queue对象
     */
    @Bean
    public Queue analyseRequestDLQ() {
        return QueueBuilder
                .durable(ANALYSE_REQUEST_DLQ_NAME)
                .lazy()
                .build();
    }

    /**
     * 绑定简历分析死信队列到死信交换机
     * @param analyseDLX 简历分析的死信交换机
     * @param analyseRequestDLQ 简历分析请求的死信队列
     * @return Binding对象
     */
    @Bean
    public Binding analyseDLQBinding(DirectExchange analyseDLX, Queue analyseRequestDLQ) {
        return BindingBuilder
                .bind(analyseRequestDLQ)
                .to(analyseDLX)
                .with(ANALYSE_REQUEST_DLQ_ROUTING_KEY);
    }

    /**
     * 配置简历分析结果的死信队列
     * @return Queue对象
     */
    @Bean
    public Queue analyseResultDLQ() {
        return QueueBuilder
                .durable(ANALYSE_RESULT_DLQ_NAME)
                .lazy()
                .build();
    }

    /**
     * 绑定简历分析结果死信队列到死信交换机
     * @param analyseDLX 简历分析的死信交换机
     * @param analyseResultDLQ 简历分析结果的死信队列
     * @return Binding对象
     */
    @Bean
    public Binding analyseResultDLQBinding(DirectExchange analyseDLX, Queue analyseResultDLQ) {
        return BindingBuilder
                .bind(analyseResultDLQ)
                .to(analyseDLX)
                .with(ANALYSE_RESULT_DLQ_ROUTING_KEY);
    }


    public static final String MATCH_DLX_NAME = "match.dlx";
    public static final String MATCH_REQUEST_DLQ_NAME = "match.request.dlq";
    public static final String MATCH_REQUEST_DLQ_ROUTING_KEY = "match.request.dlq.routing";
    public static final String MATCH_RESULT_DLQ_NAME = "match.result.dlq";
    public static final String MATCH_RESULT_DLQ_ROUTING_KEY = "match.result.dlq.routing";

    /**
     * 配置匹配请求的死信队列
     * @return Queue对象
     */
    @Bean
    public DirectExchange matchDLX() {
        return ExchangeBuilder.directExchange(MATCH_DLX_NAME)
                .durable(true)
                .build();
    }

    /**
     * 配置匹配请求的死信队列
     * @return Queue对象
     */
    @Bean
    public Queue matchRequestDLQ() {
        return QueueBuilder
                .durable(MATCH_REQUEST_DLQ_NAME)
                .lazy()
                .build();
    }

    /**
     * 绑定匹配请求死信队列到死信交换机
     * @param matchDLX 匹配请求的死信交换机
     * @param matchRequestDLQ 匹配请求的死信队列
     * @return Binding对象
     */
    @Bean
    public Binding matchRequestDLQBinding(DirectExchange matchDLX, Queue matchRequestDLQ) {
        return BindingBuilder
                .bind(matchRequestDLQ)
                .to(matchDLX)
                .with(MATCH_REQUEST_DLQ_ROUTING_KEY);
    }

    /**
     * 配置匹配结果的死信队列
     * @return Queue对象
     */
    @Bean
    public Queue matchResultDLQ() {
        return QueueBuilder
                .durable(MATCH_RESULT_DLQ_NAME)
                .lazy()
                .build();
    }

    /**
     * 绑定匹配结果死信队列到死信交换机
     * @param matchDLX 匹配请求的死信交换机
     * @param matchResultDLQ 匹配结果的死信队列
     * @return Binding对象
     */
    @Bean
    public Binding matchResultDLQBinding(DirectExchange matchDLX, Queue matchResultDLQ) {
        return BindingBuilder
                .bind(matchResultDLQ)
                .to(matchDLX)
                .with(MATCH_RESULT_DLQ_ROUTING_KEY);
    }


    public static final String UPLOAD_DLX_NAME = "upload.dlx";
    public static final String UPLOAD_DLQ_NAME = "upload.dlq";
    public static final String UPLOAD_DLQ_ROUTING_KEY = "upload.dlq.routing";

    /**
     * 配置上传的死信交换机
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange uploadDLX() {
        return ExchangeBuilder.directExchange(UPLOAD_DLX_NAME)
                .durable(true)
                .build();
    }

    /**
     * 配置上传的死信队列
     * @return Queue对象
     */
    @Bean
    public Queue uploadDLQ() {
        return QueueBuilder
                .durable(UPLOAD_DLQ_NAME)
                .lazy()
                .build();
    }

    /**
     * 绑定上传死信队列到死信交换机
     * @param uploadDLX 上传的死信交换机
     * @param uploadDLQ 上传的死信队列
     * @return Binding对象
     */
    @Bean
    public Binding uploadDLQBinding(DirectExchange uploadDLX, Queue uploadDLQ) {
        return BindingBuilder
                .bind(uploadDLQ)
                .to(uploadDLX)
                .with(UPLOAD_DLQ_ROUTING_KEY);
    }


    public static final String DELETE_DLX_NAME = "delete.dlx";
    public static final String DELETE_DLQ_NAME = "delete.dlq";
    public static final String DELETE_DLQ_ROUTING_KEY = "delete.dlq.routing";

    /**
     * 配置删除的死信交换机
     * @return DirectExchange对象
     */
    @Bean
    public DirectExchange deleteDLX() {
        return ExchangeBuilder.directExchange(DELETE_DLX_NAME)
                .durable(true)
                .build();
    }

    /**
     * 配置删除的死信队列
     * @return Queue对象
     */
    @Bean
    public Queue deleteDLQ() {
        return QueueBuilder
                .durable(DELETE_DLQ_NAME)
                .lazy()
                .build();
    }

    /**
     * 绑定删除死信队列到死信交换机
     * @param deleteDLX 删除的死信交换机
     * @param deleteDLQ 删除的死信队列
     * @return Binding对象
     */
    @Bean
    public Binding deleteDLQBinding(DirectExchange deleteDLX, Queue deleteDLQ) {
        return BindingBuilder
                .bind(deleteDLQ)
                .to(deleteDLX)
                .with(DELETE_DLQ_ROUTING_KEY);
    }

}
