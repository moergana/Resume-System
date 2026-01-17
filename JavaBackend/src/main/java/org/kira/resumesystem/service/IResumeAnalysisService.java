package org.kira.resumesystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.po.ResumeAnalysis;
import org.kira.resumesystem.entity.vo.ResumeAnalysisVO;

import java.util.List;

public interface IResumeAnalysisService extends IService<ResumeAnalysis> {
    Result listResumeAnalysis();

    Result pageListResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    List<ResumeAnalysisVO> convertResumeAnalysisListToVOList(List<ResumeAnalysis> analysisList);

    Result getResumeAnalysisById(Long id);

    Result getResumeAnalysisVOById(Long id);

    Result getResumeJdDiffer(Long resumeId, Long jdId);

    Result getResumeAdvice(Long resumeId, Long jdId);

    Result getJDMatch(Long resumeId);

    Result getResumeMatch(Long jdId);

    Result deleteResumeAnalysisById(Long id);
}
