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

    @GetMapping("/list-all")
    public Result listAllJDs() {
        log.info("Listing all resumes in the system.");
        return resumeService.listAllJDs();
    }

    @GetMapping("/list")
    public Result listResumes() {
        log.info("Listing all resumes of the current login user.");
        return resumeService.listResumes();
    }

    @PostMapping("/list/page")
    public Result listResumesByPage(@RequestParam("page") Integer page,
                                    @RequestParam("size") Integer size,
                                    @RequestBody FilterCondition filterCondition) {
        log.info("Listing resumes on page: {}, size: {}", page, size);
        return resumeService.pageListResumes(page, size, filterCondition);
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
