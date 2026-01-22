package org.kira.resumesystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.JDDTO;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.po.JD;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;

public interface IJDService extends IService<JD> {
    Result listJDs();

    Result pageListJDs(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    Result pageListUserJDs(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    Result pageListAllJDs(Integer pageNum, Integer pageSize, FilterCondition filterCondition);

    Result getJDById(Long id);

    Result getJDDTOById(Long id);

    ResponseEntity<FileSystemResource> downloadJD(Long id);

    Result upload(MultipartFile file);

    Result upload(JDDTO jdDTO);

    Result deleteJDById(Long id);

    Result listAllJDs();
}
