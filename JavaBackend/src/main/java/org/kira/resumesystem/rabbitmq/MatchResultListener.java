package org.kira.resumesystem.rabbitmq;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.json.JSONUtil;
import com.rabbitmq.client.Channel;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.ResumeAnalysisDTO;
import org.kira.resumesystem.entity.po.ResumeAnalysis;
import org.kira.resumesystem.service.IResumeAnalysisService;
import org.springframework.amqp.core.ExchangeTypes;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.rabbit.annotation.*;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;

import static org.kira.resumesystem.config.mq.RabbitMqConfig.*;
import static org.kira.resumesystem.utils.Constants.RESUME_ANALYSIS_FAILED_STATUS;
import static org.kira.resumesystem.utils.Constants.RESUME_ANALYSIS_FINISHED_STATUS;
import static org.kira.resumesystem.utils.RedisConstants.RESUME_ANALYSIS_KEY;

@Slf4j
@Component
@RequiredArgsConstructor
public class MatchResultListener {
    private final IResumeAnalysisService resumeAnalysisService;
    private final StringRedisTemplate stringRedisTemplate;

    /**
     * 处理JD匹配结果消息
     * 需要注意：消息需要手动确认和手动拒绝，并且被拒绝的消息不重新入队
     * @param message 消息对象
     * @param channel 信道对象
     */
    @RabbitListener(bindings = @QueueBinding(value = @Queue(
                value = JD_MATCH_RESULT_QUEUE_NAME,
                durable = "true",
                arguments = {
                        @Argument(name = "x-queue-mode", value = "lazy"),
                        @Argument(name = "x-dead-letter-exchange", value = MATCH_DLX_NAME),
                        @Argument(name = "x-dead-letter-routing-key", value = MATCH_RESULT_DLQ_ROUTING_KEY),
                }
            ),
            exchange = @Exchange(
                    value = MATCH_EXCHANGE_NAME,
                    durable = "true",
                    type = ExchangeTypes.DIRECT
            ),
            key = {JD_MATCH_RESULT_ROUTING_KEY}
        )
    )
    public void dealJDMatchResult(Message message, Channel channel) {
        try {
            // 从message中获取ResumeAnalysisDTO对象
            String messageBody = new String(message.getBody(), StandardCharsets.UTF_8);
            ResumeAnalysisDTO resumeAnalysisDTO = JSONUtil.toBean(messageBody, ResumeAnalysisDTO.class);
            // 处理JD匹配结果消息
            Long userId = resumeAnalysisDTO.getUserId();
            Long resumeId = resumeAnalysisDTO.getResumeId();
            Long jdId = resumeAnalysisDTO.getJdID();
            String requestType = resumeAnalysisDTO.getRequestType();
            log.info("Received JD match result: User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.", userId, resumeId, jdId, requestType);
            // 首先判断分析结果的状态码
            Integer status = resumeAnalysisDTO.getStatus();
            if (status.equals(RESUME_ANALYSIS_FINISHED_STATUS)) {
                log.info("JD match completed successfully for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}. Saving results by updating existing record...", userId, resumeId, jdId, requestType);
            }
            else if (status.equals(RESUME_ANALYSIS_FAILED_STATUS)) {
                log.error("JD match failed for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.", userId, resumeId, jdId, requestType);
            }
            // 构造ResumeAnalysis对象，保存到数据库中
            ResumeAnalysis resumeAnalysis = new ResumeAnalysis();
            BeanUtil.copyProperties(resumeAnalysisDTO, resumeAnalysis, "retrievedResumes", "retrievedJds");
            resumeAnalysis.setRetrievedResumes(JSONUtil.toJsonStr(resumeAnalysisDTO.getRetrievedResumes()));
            resumeAnalysis.setRetrievedJds(JSONUtil.toJsonStr(resumeAnalysisDTO.getRetrievedJds()));
            // 保存到数据库
            // log.info("JD match result to be saved to database: {}", resumeAnalysis);
            resumeAnalysisService.updateById(resumeAnalysis);
            log.info("JD match result updated to database successfully.");

            // 检查Redis中是否有对应的缓存，如果有则删除缓存（强制更新缓存）
            String redisKey = RESUME_ANALYSIS_KEY + resumeAnalysis.getId();
            Boolean deleted = stringRedisTemplate.delete(redisKey);
            if (deleted != null && deleted) {
                log.info("Deleted Redis cache for key: {} after JD match result updated to database.", redisKey);
            }

            // 手动确认消息已被成功处理
            long deliveryTag = message.getMessageProperties().getDeliveryTag();
            channel.basicAck(deliveryTag, false);
        } catch (Exception e) {
            log.error("Error processing JD match result message: {}", e.getMessage());
            // 处理失败，拒绝消息并不重新入队
            try {
                long deliveryTag = message.getMessageProperties().getDeliveryTag();
                channel.basicNack(deliveryTag, false, false);   // NACK的消息不重新入队
            } catch (Exception ex) {
                log.error("Error sending NACK for JD match result message: {}", ex.getMessage());
                throw new RuntimeException(ex);
            }
            throw new RuntimeException(e);
        }
    }

    /**
     * 处理简历匹配结果消息
     * 需要注意：消息需要手动确认和手动拒绝，并且被拒绝的消息不重新入队
     * @param message 消息对象
     * @param channel 信道对象
     */
    @RabbitListener(bindings = @QueueBinding(value = @Queue(
                value = RESUME_MATCH_RESULT_QUEUE_NAME,
                durable = "true",
                arguments = {
                        @Argument(name = "x-queue-mode", value = "lazy"),
                        @Argument(name = "x-dead-letter-exchange", value = MATCH_DLX_NAME),
                        @Argument(name = "x-dead-letter-routing-key", value = MATCH_RESULT_DLQ_ROUTING_KEY),
                }
        ),
                exchange = @Exchange(
                        value = MATCH_EXCHANGE_NAME,
                        durable = "true",
                        type = ExchangeTypes.DIRECT
                ),
                key = {RESUME_MATCH_RESULT_ROUTING_KEY}
        )
    )
    public void dealResumeMatchResult(Message message, Channel channel) {
        try {
            // 从message中获取ResumeAnalysisDTO对象
            String messageBody = new String(message.getBody(), StandardCharsets.UTF_8);
            ResumeAnalysisDTO resumeAnalysisDTO = JSONUtil.toBean(messageBody, ResumeAnalysisDTO.class);
            // 处理JD匹配结果消息
            Long userId = resumeAnalysisDTO.getUserId();
            Long resumeId = resumeAnalysisDTO.getResumeId();
            Long jdId = resumeAnalysisDTO.getJdID();
            String requestType = resumeAnalysisDTO.getRequestType();
            log.info("Received resume match result: User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.", userId, resumeId, jdId, requestType);
            // 首先判断分析结果的状态码
            Integer status = resumeAnalysisDTO.getStatus();
            if (status.equals(RESUME_ANALYSIS_FINISHED_STATUS)) {
                log.info("Resume match completed successfully for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}. Saving results by updating existing record...", userId, resumeId, jdId, requestType);
            }
            else if (status.equals(RESUME_ANALYSIS_FAILED_STATUS)) {
                log.error("Resume match failed for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.", userId, resumeId, jdId, requestType);
            }
            // 构造ResumeAnalysis对象，保存到数据库中
            ResumeAnalysis resumeAnalysis = new ResumeAnalysis();
            BeanUtil.copyProperties(resumeAnalysisDTO, resumeAnalysis, "retrievedResumes", "retrievedJds");
            resumeAnalysis.setRetrievedResumes(JSONUtil.toJsonStr(resumeAnalysisDTO.getRetrievedResumes()));
            resumeAnalysis.setRetrievedJds(JSONUtil.toJsonStr(resumeAnalysisDTO.getRetrievedJds()));
            // 保存到数据库
            // log.info("Resume match result to be saved to database: {}", resumeAnalysis);
            resumeAnalysisService.updateById(resumeAnalysis);
            log.info("Resume match result updated to database successfully.");

            // 检查Redis中是否有对应的缓存，如果有则删除缓存（强制更新缓存）
            String redisKey = RESUME_ANALYSIS_KEY + resumeAnalysis.getId();
            Boolean deleted = stringRedisTemplate.delete(redisKey);
            if (deleted != null && deleted) {
                log.info("Deleted Redis cache for key: {} after resume match result updated to database.", redisKey);
            }

            // 手动确认消息已被成功处理
            long deliveryTag = message.getMessageProperties().getDeliveryTag();
            channel.basicAck(deliveryTag, false);
        } catch (Exception e) {
            log.error("Error processing resume match result message: {}", e.getMessage());
            // 处理失败，拒绝消息并不重新入队
            try {
                long deliveryTag = message.getMessageProperties().getDeliveryTag();
                channel.basicNack(deliveryTag, false, false);   // NACK的消息不重新入队
            } catch (Exception ex) {
                log.error("Error sending NACK for resume match result message: {}", ex.getMessage());
                throw new RuntimeException(ex);
            }
            throw new RuntimeException(e);
        }
    }
}
