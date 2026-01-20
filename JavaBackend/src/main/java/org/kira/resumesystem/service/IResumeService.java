package org.kira.resumesystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.po.Resume;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;

public interface IResumeService extends IService<Resume> {
    Result upload(MultipartFile file);

    Result listResumes();

    Result pageListResumes(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    Result getResumeById(Long id);

    Result getResumeDTOById(Long id);

    ResponseEntity<FileSystemResource> downloadResume(Long id);

    Result deleteResumeById(Long id);

    Result listAllResumes();
}
