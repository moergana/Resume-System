package org.kira.resumesystem.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.FilterCondition;
import org.kira.resumesystem.entity.dto.JDDTO;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.service.IJDService;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@RestController
@RequestMapping("/jd")
@RequiredArgsConstructor
public class JDController {
    private final IJDService jdService;

    @GetMapping("/list-all")
    public Result listAllJDs() {
        log.info("Listing all JDs in the system.");
        return jdService.listAllJDs();
    }

    @GetMapping("/list")
    public Result listJDs() {
        log.info("Listing all JDs of the current login user.");
        return jdService.listJDs();
    }

    @PostMapping("/list/page")
    public Result listJDsByPage(@RequestParam("page") Integer page,
                                @RequestParam("size") Integer size,
                                @RequestBody FilterCondition filterCondition) {
        log.info("Listing JDs on page: {}, size: {}", page, size);
        return jdService.pageListJDs(page, size, filterCondition);
    }

    @GetMapping("/{id}")
    public Result getJDById(@PathVariable Long id) {
        log.info("Fetching JD with ID: {}", id);
        return jdService.getJDDTOById(id);
    }

    @DeleteMapping("/{id}")
    public Result deleteJDById(@PathVariable Long id) {
        log.info("Deleting JD with ID: {}", id);
        return jdService.deleteJDById(id);
    }

    @GetMapping("/download/{id}")
    public ResponseEntity<FileSystemResource> downloadJD(@PathVariable Long id) {
        log.info("Downloading JD with ID: {}", id);
        return jdService.downloadJD(id);
    }

    @PostMapping("/upload/file")
    public Result uploadJDFile(@RequestParam("jd") MultipartFile file) {
        return jdService.upload(file);
    }

    @PostMapping("/upload/info")
    public Result uploadJDInfo(@RequestBody JDDTO jdDTO) {
        return jdService.upload(jdDTO);
    }
}
