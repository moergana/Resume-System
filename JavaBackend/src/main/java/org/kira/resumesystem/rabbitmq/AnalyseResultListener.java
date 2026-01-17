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
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;

import static org.kira.resumesystem.config.mq.RabbitMqConfig.*;
import static org.kira.resumesystem.utils.Constants.RESUME_ANALYSIS_FAILED_STATUS;
import static org.kira.resumesystem.utils.Constants.RESUME_ANALYSIS_FINISHED_STATUS;

@Slf4j
@Component
@RequiredArgsConstructor
public class AnalyseResultListener {
    private final IResumeAnalysisService resumeAnalysisService;

    /**
     * 监听简历分析结果的消息队列
     * 需要注意：消息需要手动确认和手动拒绝，并且被拒绝的消息不重新入队
     * @param message 消息对象
     * @param channel 信道对象
     * （由于已经在SerializeConfig类中配置了Jackson2JsonMessageConverter消息转换对象，
     * 所以发送的消息会自动转化为JSON字符串，如果参数不是Message对象，消息则会自动JSON转为指定类型的对象）
     */
    @RabbitListener(bindings = @QueueBinding(
            value = @Queue(
                value = ANALYSE_RESULT_QUEUE_NAME,
                durable = "true",
                arguments = {
                        @Argument(name = "x-queue-mode", value = "lazy"),
                        @Argument(name = "x-dead-letter-exchange", value = ANALYSE_DLX_NAME),
                        @Argument(name = "x-dead-letter-routing-key", value = ANALYSE_RESULT_DLQ_ROUTING_KEY),
                }
            ),
            exchange = @Exchange(
                    value = ANALYSE_EXCHANGE_NAME,
                    durable = "true",
                    type = ExchangeTypes.DIRECT
            ),
            key = {ANALYSE_RESULT_ROUTING_KEY}
        )
    )
    public void dealAnalysisResult(Message message, Channel channel) {
        try {
            // 获取消息体并转换为ResumeAnalysisDTO对象
            String messageBody = new String(message.getBody(), StandardCharsets.UTF_8);
            ResumeAnalysisDTO analysisResultDTO = JSONUtil.toBean(messageBody, ResumeAnalysisDTO.class);
            // 将DTO对象转换为PO对象
            ResumeAnalysis analysisResult = new ResumeAnalysis();
            BeanUtil.copyProperties(analysisResultDTO, analysisResult);
            Long userId = analysisResult.getUserId();
            Long resumeId = analysisResult.getResumeId();
            Long jdId = analysisResult.getJdID();
            String requestType = analysisResult.getRequestType();
            log.info("Received resume analysis result: User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.", userId, resumeId, jdId, requestType);
            // 首先判断分析结果的状态码
            Integer status = analysisResult.getStatus();
            if (status.equals(RESUME_ANALYSIS_FINISHED_STATUS)) {
                log.info("Resume analysis completed successfully for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}. Saving results by updating existing record...", userId, resumeId, jdId, requestType);
            }
            else if (status.equals(RESUME_ANALYSIS_FAILED_STATUS)) {
                log.error("Resume analysis failed for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.", userId, resumeId, jdId, requestType);
            }
            // 保存分析结果到数据库
            resumeAnalysisService.updateById(analysisResult);
            log.info("Resume analysis results updated successfully for User ID: {}, Resume ID: {}, JD ID: {}.", userId, resumeId, jdId);

            // 手动确认消息已被成功处理
            long deliveryTag = message.getMessageProperties().getDeliveryTag();
            channel.basicAck(deliveryTag, false);
        } catch (Exception e) {
            log.error("Error processing resume analysis result message: {}", e.getMessage());
            // 处理异常情况，拒绝消息并不重新入队列
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
