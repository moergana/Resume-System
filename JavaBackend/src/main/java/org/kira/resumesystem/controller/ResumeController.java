package org.kira.resumesystem.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.service.IResumeService;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;


@Slf4j
@RestController
@RequestMapping("/resume")
@RequiredArgsConstructor
public class ResumeController {
    private final IResumeService resumeService;

    /**
     * 获取系统中所有的简历信息
     * 注意：该方法不进行分页，可能会返回大量数据
     * @return 简历列表
     */
    @GetMapping("/list-all")
    public Result listAllResumes() {
        log.info("Listing all resumes in the system.");
        return resumeService.listAllResumes();
    }

    /**
     * 获取当前登录用户的所有简历信息
     * 注意：该方法不进行分页，可能会返回大量数据
     * @return 简历列表
     */
    @GetMapping("/list")
    public Result listResumes() {
        log.info("Listing all resumes of the current login user.");
        return resumeService.listResumes();
    }

    /**
     * 分页当前用户的简历信息
     * @param page 页码
     * @param size 每页大小
     * @param filterCondition 过滤条件
     * @return 分页的简历列表
     */
    @PostMapping("/list/page")
    public Result listResumesByPage(@RequestParam("page") Integer page,
                                    @RequestParam("size") Integer size,
                                    @RequestBody FilterCondition filterCondition) {
        log.info("Listing current user's resumes on page: {}, size: {}", page, size);
        return resumeService.pageListUserResumes(page, size, filterCondition);
    }

    /**
     * 分页获取系统中所有的简历信息
     * @param page 页码
     * @param size 每页大小
     * @param filterCondition 过滤条件
     * @return 分页的简历列表
     */
    @PostMapping("/list-all/page")
    public Result listAllResumesByPage(@RequestParam("page") Integer page,
                                       @RequestParam("size") Integer size,
                                       @RequestBody FilterCondition filterCondition) {
        log.info("Listing all resumes in the system on page: {}, size: {}", page, size);
        return resumeService.pageListAllResumes(page, size, filterCondition);
    }

    @GetMapping("/{id}")
    public Result getResumeById(@PathVariable("id") Long id) {
        log.info("Fetching resume with ID: {}", id);
        return resumeService.getResumeDTOById(id);
    }

    @DeleteMapping("/{id}")
    public Result deleteResumeById(@PathVariable("id") Long id) {
        log.info("Deleting resume with ID: {}", id);
        return resumeService.deleteResumeById(id);
    }

    @PostMapping("/download/{id}")
    public ResponseEntity<FileSystemResource> downloadResume(@PathVariable("id") Long id) {
        log.info("Downloading resume with ID: {}", id);
        return resumeService.downloadResume(id);
    }

    @PostMapping("/upload/file")
    public Result uploadResume(@RequestParam("resume") MultipartFile file) {
        return resumeService.upload(file);
    }
}
