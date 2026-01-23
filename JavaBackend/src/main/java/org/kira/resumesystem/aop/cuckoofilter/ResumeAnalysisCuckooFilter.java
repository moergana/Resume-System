package org.kira.resumesystem.aop.cuckoofilter;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.ResumeAnalysisDTO;
import org.kira.resumesystem.utils.RedisCuckooFilterTool;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import static org.kira.resumesystem.utils.RedisConstants.RESUME_ANALYSIS_CUCKOO_FILTER_KEY;

@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class ResumeAnalysisCuckooFilter {
    private final RedisCuckooFilterTool redisCuckooFilterTool;

    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.ResumeAnalysisServiceImpl.getResumeAnalysis*ById(..))")
    public void getPointcut() {}


    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.ResumeAnalysisServiceImpl.generate*(..))")
    public void addPointcut() {}


    @Pointcut("execution(* org.kira.resumesystem.service.serviceImpl.ResumeAnalysisServiceImpl.deleteResumeAnalysisById(..))")
    public void deletePointcut() {}

    @Around("getPointcut()")
    public Object aroundGet(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object[] args = proceedingJoinPoint.getArgs();
        Long id = (Long) args[0];
        String analysisId = String.valueOf(id);
        if (redisCuckooFilterTool.exists(RESUME_ANALYSIS_CUCKOO_FILTER_KEY, analysisId)) {
            log.info("Resume Analysis ID {} found in Cuckoo Filter, proceeding with redis and database query.", id);
            return proceedingJoinPoint.proceed();
        } else {
            log.info("Resume Analysis ID {} not found in Cuckoo Filter, skipping redis and database query.", id);
            return Result.fail("Resume analysis record not found."); // 或者返回一个适当的失败结果
        }
    }

    @Around("addPointcut()")
    @Transactional(rollbackFor = Exception.class)
    public Object aroundAdd(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object[] args = proceedingJoinPoint.getArgs();
        ResumeAnalysisDTO resumeAnalysisDTO = (ResumeAnalysisDTO) args[0];
        Object proceedResult = proceedingJoinPoint.proceed();
        Result result = (Result) proceedResult;
        if (result.getCode() != 200) {
            boolean added = redisCuckooFilterTool.addnx(RESUME_ANALYSIS_CUCKOO_FILTER_KEY, String.valueOf(resumeAnalysisDTO.getId()));
            if (added) {
                log.info("Successfully added Resume Analysis ID {} to Cuckoo Filter.", resumeAnalysisDTO.getId());
            } else {
                log.error("Failed to add Resume Analysis ID {} to Cuckoo Filter.", resumeAnalysisDTO.getId());
                throw new RuntimeException("Failed to add Resume Analysis ID to Cuckoo Filter.");
            }
        }
        else {
            log.info("Resume Analysis request generated failed, not adding to Cuckoo Filter.");
        }
        return proceedResult;
    }

    @Around("deletePointcut()")
    @Transactional(rollbackFor = Exception.class)
    public Object aroundDelete(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object[] args = proceedingJoinPoint.getArgs();
        Long id = (Long) args[0];
        String resumeAnalysisId = String.valueOf(id);
        Object proceedResult = proceedingJoinPoint.proceed();
        Result result = (Result) proceedResult;
        if (result.getCode() == 200) {
            boolean deleted = redisCuckooFilterTool.delete(RESUME_ANALYSIS_CUCKOO_FILTER_KEY, resumeAnalysisId);
            if (deleted) {
                log.info("Deleted Resume Analysis ID {} from Cuckoo Filter after Resume Analysis deletion.", id);
            } else {
                log.error("Resume Analysis ID {} was not present in Cuckoo Filter during Resume Analysis deletion.", id);
                throw new RuntimeException("Failed to delete Resume Analysis ID from Cuckoo Filter.");
            }
        } else {
            log.info("Resume Analysis ID {} deletion failed, not removing from Cuckoo Filter.", id);
        }
        return proceedResult;
    }
}
