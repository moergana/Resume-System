package org.kira.resumesystem.aop.cuckoofilter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.kira.resumesystem.entity.dto.JDDTO;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.utils.RedisCuckooFilterTool;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import static org.kira.resumesystem.utils.RedisConstants.JD_CUCKOO_FILTER_KEY;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class JDCuckooFilter {
    private final RedisCuckooFilterTool redisCuckooFilterTool;

    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.JDServiceImpl.getJD*ById(..))")
    public void getPointcut() {}


    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.JDServiceImpl.upload(..))")
    public void addPointcut() {}


    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.JDServiceImpl.deleteJDById(..))")
    public void deletePointcut() {}

    @Around("getPointcut()")
    public Object aroundGet(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object[] args = proceedingJoinPoint.getArgs();
        Long id = (Long) args[0];
        String jdId = String.valueOf(id);
        if (redisCuckooFilterTool.exists(JD_CUCKOO_FILTER_KEY, jdId)) {
            log.info("JD ID {} found in Cuckoo Filter, proceeding with redis and database query.", id);
            return proceedingJoinPoint.proceed();
        } else {
            log.info("JD ID {} not found in Cuckoo Filter, skipping redis and database query.", id);
            return Result.fail("JD not found.");
        }
    }

    @Around("addPointcut()")
    @Transactional(rollbackFor = Exception.class)
    public Object aroundAdd(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object proceedResult = proceedingJoinPoint.proceed();
        Result result = (Result) proceedResult;
        if (result.getCode() == 200) {
            Object data = result.getData();
            JDDTO jddto = (JDDTO) data;
            Long id = jddto.getId();
            String jdId = String.valueOf(id);
            log.info("Adding JD ID {} to JD Cuckoo Filter after upload.", id);
            boolean addnxed = redisCuckooFilterTool.addnx(JD_CUCKOO_FILTER_KEY, jdId);
            if (addnxed) {
                log.info("Added JD ID {} to Cuckoo Filter after upload.", id);
            } else {
                log.error("Failed to add JD ID {} to Cuckoo Filter after upload.", id);
                throw new RuntimeException("Failed to add JD ID to Cuckoo Filter.");
            }
        }
        else {
            log.info("JD upload failed, not adding to Cuckoo Filter.");
        }
        return proceedResult;
    }

    @Around("deletePointcut()")
    @Transactional(rollbackFor = Exception.class)
    public Object aroundDelete(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object[] args = proceedingJoinPoint.getArgs();
        Long id = (Long) args[0];
        String jdId = String.valueOf(id);
        Object proceedResult = proceedingJoinPoint.proceed();
        Result result = (Result) proceedResult;
        if (result.getCode() == 200) {
            log.info("Deleting JD ID {} from JD Cuckoo Filter after JD deletion.", id);
            boolean deleteSuccess = redisCuckooFilterTool.delete(JD_CUCKOO_FILTER_KEY, jdId);
            if (deleteSuccess) {
                log.info("Deleted JD ID {} from Cuckoo Filter after JD deletion.", id);
            } else {
                log.info("JD ID {} was not present in Cuckoo Filter during JD deletion.", id);
                throw new RuntimeException("Failed to delete JD ID from Cuckoo Filter.");
            }
        } else {
            log.info("JD deletion failed, not removing from Cuckoo Filter.");
        }
        return proceedResult;
    }
}
