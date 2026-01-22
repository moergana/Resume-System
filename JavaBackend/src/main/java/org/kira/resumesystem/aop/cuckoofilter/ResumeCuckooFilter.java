package org.kira.resumesystem.aop.cuckoofilter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.ResumeDTO;
import org.kira.resumesystem.utils.RedisCuckooFilterTool;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import static org.kira.resumesystem.utils.RedisConstants.RESUME_CUCKOO_FILTER_KEY;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ResumeCuckooFilter {
    private final RedisCuckooFilterTool redisCuckooFilterTool;

    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.ResumeServiceImpl.getResumeById(..))")
    public void getPointcut() {}


    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.ResumeServiceImpl.upload(..))")
    public void addPointcut() {}


    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.ResumeServiceImpl.deleteResumeById(..))")
    public void deletePointcut() {}


    @Around("getPointcut()")
    public Object aroundGet(ProceedingJoinPoint joinPoint) throws Throwable {
        Object[] args = joinPoint.getArgs();
        Long id = (Long) args[0];
        String resumeId = String.valueOf(id);
        if (redisCuckooFilterTool.exists(RESUME_CUCKOO_FILTER_KEY, resumeId)) {
            return joinPoint.proceed();
        } else {
            log.info("Resume ID {} not found in Cuckoo Filter, skipping redis and database query.", id);
            return Result.fail("Resume not found.");
        }
    }

    @Around("addPointcut()")
    @Transactional(rollbackFor = Exception.class)
    public Object aroundAdd(ProceedingJoinPoint joinPoint) throws Throwable {
        Object proceedResult = joinPoint.proceed();
        Result result = (Result) proceedResult;
        if (result.getCode() == 200) {
            Object data = result.getData();
            ResumeDTO resumeDTO = (ResumeDTO) data;
            Long id = resumeDTO.getId();
            String resumeId = String.valueOf(id);
            boolean addnxed = redisCuckooFilterTool.addnx(RESUME_CUCKOO_FILTER_KEY, resumeId);
            if (addnxed) {
                log.info("Added Resume ID {} to Cuckoo Filter after upload.", id);
            } else {
                log.info("Failed to add Resume ID {} to Cuckoo Filter after upload.", id);
                throw new RuntimeException("Failed to add Resume ID to Cuckoo Filter.");
            }
        }
        else {
            log.info("Resume upload failed, not adding to Cuckoo Filter.");
        }
        return proceedResult;
    }

    @Around("deletePointcut()")
    @Transactional(rollbackFor = Exception.class)
    public Object aroundDelete(ProceedingJoinPoint joinPoint) throws Throwable {
        Object[] args = joinPoint.getArgs();
        Long id = (Long) args[0];
        String resumeId = String.valueOf(id);
        Object proceedResult = joinPoint.proceed();
        Result result = (Result) proceedResult;
        if (result.getCode() == 200) {
            boolean deleted = redisCuckooFilterTool.delete(RESUME_CUCKOO_FILTER_KEY, resumeId);
            if (deleted) {
                log.info("Deleted Resume ID {} from Cuckoo Filter after resume deletion.", id);
            } else {
                log.info("Resume ID {} was not present in Cuckoo Filter during resume deletion.", id);
                throw new RuntimeException("Failed to delete Resume ID from Cuckoo Filter.");
            }
        } else {
            log.info("Resume deletion failed, not removing from Cuckoo Filter.");
        }
        return proceedResult;
    }
}
