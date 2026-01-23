package org.kira.resumesystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.ResumeAnalysisDTO;
import org.kira.resumesystem.entity.po.ResumeAnalysis;
import org.kira.resumesystem.entity.vo.ResumeAnalysisVO;

import java.util.List;

public interface IResumeAnalysisService extends IService<ResumeAnalysis> {
    Result listResumeAnalysis();

    Result pageListResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    Result pageListUserResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    Result pageListAllResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    List<ResumeAnalysisVO> convertResumeAnalysisListToVOList(List<ResumeAnalysis> analysisList);

    Result getResumeAnalysisById(Long id);

    Result getResumeAnalysisById_UserId(Long id, Long userId);

    Result getResumeAnalysisVOById(Long id);

    Result generateResumeJdDiffer(Long resumeId, Long jdId);

    void HandleAnalyseRequest(ResumeAnalysisDTO resumeAnalysisDTO, String ExchangeName, String RoutingKey);

    Result generateResumeAdvice(Long resumeId, Long jdId);

    Result generateJDMatch(Long resumeId);

    Result generateResumeMatch(Long jdId);

    Result deleteResumeAnalysisById(Long id);
}
