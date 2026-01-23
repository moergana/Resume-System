package org.kira.resumesystem.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.service.IResumeAnalysisService;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/resumeAnalysis")
@RequiredArgsConstructor
public class ResumeAnalysisController {
    private final IResumeAnalysisService IResumeAnalysisService;

    /**
     * 获取当前登录用户的所有简历分析记录
     * 注意：该方法不进行分页，可能会返回大量数据
     * @return 简历分析记录列表
     */
    @GetMapping("/list")
    public Result listResumeAnalysis() {
        log.info("Listing all resume analysis records of the current login user.");
        return IResumeAnalysisService.listResumeAnalysis();
    }

    @GetMapping("/{id}")
    public Result getResumeAnalysisById(@PathVariable("id") Long id) {
        log.info("Getting resume analysis record with ID: {}.", id);
        return IResumeAnalysisService.getResumeAnalysisVOById(id);
    }

    /**
     * 分页获取当前用户的简历分析记录
     * @param page 页码
     * @param size 每页大小
     * @param filterCondition 过滤条件
     * @return 分页的简历分析记录
     */
    @PostMapping("/list/page")
    public Result listResumeAnalysisByPage(@RequestParam("page") Integer page,
                                           @RequestParam("size") Integer size,
                                           @RequestBody FilterCondition filterCondition) {
        log.info("Listing current user's resume analysis records on page: {}, size: {}", page, size);
        return IResumeAnalysisService.pageListUserResumeAnalysis(page, size, filterCondition);
    }

    @DeleteMapping("/{id}")
    public Result deleteResumeAnalysisById(@PathVariable("id") Long id) {
        log.info("Deleting resume analysis record with ID: {}.", id);
        return IResumeAnalysisService.deleteResumeAnalysisById(id);
    }

    @GetMapping("/resume_jd_differ")
    public Result getResumeJdDiffer(@RequestParam("resume_id") Long resume_id, @RequestParam("jd_id") Long jd_id) {
        log.info("Requesting resume-JD difference analysis for Resume ID: {}, JD ID: {}.", resume_id, jd_id);
        return IResumeAnalysisService.generateResumeJdDiffer(resume_id, jd_id);
    }

    @GetMapping("/resume_advice")
    public Result getResumeAdvice(@RequestParam("resume_id") Long resume_id, @RequestParam("jd_id") Long jd_id) {
        log.info("Requesting resume advice for Resume ID: {}, JD ID: {}.", resume_id, jd_id);
        return IResumeAnalysisService.generateResumeAdvice(resume_id, jd_id);
    }

    @GetMapping("/jd_match")
    public Result getJDMatch(@RequestParam("resume_id") Long resume_id) {
        log.info("Querying matched JD for resume ID: {}", resume_id);
        return IResumeAnalysisService.generateJDMatch(resume_id);
    }

    @GetMapping("/resume_match")
    public Result getResumeMatch(@RequestParam("jd_id") Long jd_id) {
        log.info("Querying matched resumes for JD ID: {}", jd_id);
        return IResumeAnalysisService.generateResumeMatch(jd_id);
    }
}
