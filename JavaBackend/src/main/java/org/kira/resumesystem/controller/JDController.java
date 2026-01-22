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

    /**
     * 获取系统中所有的JD信息
     * 注意：该方法不进行分页，可能会返回大量数据
     * @return JD列表
     */
    @GetMapping("/list-all")
    public Result listAllJDs() {
        log.info("Listing all JDs in the system.");
        return jdService.listAllJDs();
    }

    /**
     * 获取当前登录用户的所有JD信息
     * 注意：该方法不进行分页，可能会返回大量数据
     * @return JD列表
     */
    @GetMapping("/list")
    public Result listJDs() {
        log.info("Listing all JDs of the current login user.");
        return jdService.listJDs();
    }

    /**
     * 分页当前用户的JD信息
     * @param page 页码
     * @param size 每页大小
     * @param filterCondition 过滤条件
     * @return 分页的JD列表
     */
    @PostMapping("/list/page")
    public Result listJDsByPage(@RequestParam("page") Integer page,
                                @RequestParam("size") Integer size,
                                @RequestBody FilterCondition filterCondition) {
        log.info("Listing current user's JDs on page: {}, size: {}", page, size);
        return jdService.pageListUserJDs(page, size, filterCondition);
    }

    /**
     * 分页获取系统中所有的JD信息
     * @param page 页码
     * @param size 每页大小
     * @param filterCondition 过滤条件
     * @return 分页的JD列表
     */
    @PostMapping("/list-all/page")
    public Result listAllJDsByPage(@RequestParam("page") Integer page,
                                   @RequestParam("size") Integer size,
                                   @RequestBody FilterCondition filterCondition) {
        log.info("Listing all JDs on page: {}, size: {}", page, size);
        return jdService.pageListAllJDs(page, size, filterCondition);
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
