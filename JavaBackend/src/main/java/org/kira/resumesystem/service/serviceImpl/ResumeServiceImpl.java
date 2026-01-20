package org.kira.resumesystem.service.serviceImpl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.config.FileProperties;
import org.kira.resumesystem.entity.dto.*;
import org.kira.resumesystem.entity.po.Resume;
import org.kira.resumesystem.exceptions.DbException;
import org.kira.resumesystem.exceptions.FileException;
import org.kira.resumesystem.mapper.ResumeMapper;
import org.kira.resumesystem.service.IResumeService;
import org.kira.resumesystem.utils.UserThreadLocal;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.core.io.FileSystemResource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

import static org.kira.resumesystem.config.mq.RabbitMqConfig.*;
import static org.kira.resumesystem.utils.Constants.*;
import static org.kira.resumesystem.utils.FileTool.parsePath;
import static org.kira.resumesystem.utils.FileTool.getOriginalFileName;
import static org.kira.resumesystem.utils.RedisConstants.*;


@Slf4j
@Service
@RequiredArgsConstructor
@EnableConfigurationProperties(value = {FileProperties.class})
public class ResumeServiceImpl extends ServiceImpl<ResumeMapper, Resume> implements IResumeService {
    private final FileProperties fileProperties;
    private final StringRedisTemplate stringRedisTemplate;
    private final RabbitTemplate rabbitTemplate;

    /**
     * 列出系统中所有用户的所有简历
     * 注意：该方法不会返回Resume记录的所有属性，只返回用于前端显示的必要属性
     * 需要查询数据库的属性包括：id, userId, file_path, createTime, updateTime
     * @return Result 包含所有简历列表的结果对象
     */
    @Override
    public Result listAllResumes() {
        log.info("Listing all resumes in the system.");
        List<ResumeDTO> resumeList = lambdaQuery()
                .select(
                        Resume::getId,
                        Resume::getUserId,
                        Resume::getFilePath,
                        Resume::getCreateTime,
                        Resume::getUpdateTime
                )
                .orderByDesc(Resume::getUpdateTime)
                .list()
                .stream().map(resume -> {
                    ResumeDTO dto = new ResumeDTO();
                    BeanUtil.copyProperties(resume, dto);
                    dto.setName(getOriginalFileName(resume.getFilePath())); // 从保存路径中获取简历的原始文件名并设置到dto中
                    return dto;
                }).collect(Collectors.toList());
        if (resumeList.isEmpty()) {
            log.info("No resumes found in the system.");
            return Result.success("No resumes found.", null);
        }
        log.info("Found {} resumes in the system.", resumeList.size());
        return Result.success("Resumes found successfully.", resumeList);
    }

    /**
     * 列出当前用户的所有简历
     * 注意：该方法不会返回Resume记录的所有属性，只返回用于前端显示的必要属性
     * 需要查询数据库的属性包括：id, userId, file_path, createTime, updateTime
     * @return Result 包含简历列表的结果对象
     */
    @Override
    public Result listResumes() {
        Long userId = UserThreadLocal.get();
        log.info("Listing resumes for user ID: {}", userId);
        List<ResumeDTO> resumeList = lambdaQuery()
                .select(
                        Resume::getId,
                        Resume::getUserId,
                        Resume::getFilePath,
                        Resume::getCreateTime,
                        Resume::getUpdateTime
                )
                .eq(Resume::getUserId, userId)
                .orderByDesc(Resume::getUpdateTime)
                .list()
                .stream().map(resume -> {
                    ResumeDTO dto = new ResumeDTO();
                    BeanUtil.copyProperties(resume, dto);
                    dto.setName(getOriginalFileName(resume.getFilePath())); // 从保存路径中获取简历的原始文件名并设置到dto中
                    return dto;
                }).collect(Collectors.toList());
        if (resumeList.isEmpty()) {
            log.info("No resumes found for user ID: {}", userId);
            return Result.success("No resumes found.", null);
        } else {
            log.info("Found {} Resumes for user ID: {}", resumeList.size(), userId);
            return Result.success("Resumes found successfully.", resumeList);
        }
    }

    /**
     * 分页列出所有用户的简历
     * 注意：该方法不会返回Resume记录的所有属性，只返回用于前端显示的必要属性
     * 需要查询数据库的属性包括：id, userId, file_path, createTime, updateTime
     * @param pageNum 页码
     * @param pageSize 每页大小
     * @return Result 包含简历列表的结果对象
     */
    @Override
    public Result pageListResumes(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        log.info("Listing resumes on page {}, page size {}", pageNum, pageSize);
        // 创建Page分页对象
        Page<Resume> page = new Page<>(pageNum, pageSize);
        // 将当前用户的ID设置到过滤条件中，确保只查询该用户的简历
        filterCondition.setUserId(UserThreadLocal.get());
        // 使用Mapper中自定义的分页查询方法，传入分页对象和过滤条件
        baseMapper.selectResumesByCondition(page, filterCondition);
        // 将查询得到的Resume对象列表转换为ResumeDTO对象列表
        List<ResumeDTO> resumeDTOList = page.getRecords().stream()
                .map(resume -> {
                    ResumeDTO dto = new ResumeDTO();
                    BeanUtil.copyProperties(resume, dto);
                    dto.setName(getOriginalFileName(resume.getFilePath())); // 从保存路径中获取简历的原始文件名并设置到dto中
                    return dto;
                }).collect(Collectors.toList());
        // 将resumeDTOList封装为PageResult对象返回
        PageResult<ResumeDTO> pageResult = new PageResult<>(
                page.getPages(),
                page.getTotal(),
                page.getCurrent(),
                page.getSize(),
                resumeDTOList
        );
        if (resumeDTOList.isEmpty()) {
            log.info("No resumes found on page {}, page size {}", pageNum, pageSize);
            return Result.success("No resumes found.", pageResult);
        }
        log.info("Found {} Resumes on page {}, page size {}", resumeDTOList.size(), pageNum, pageSize);
        return Result.success("Resumes found successfully " + "on page " + pageNum + ", page size "+ pageSize + ".", pageResult);
    }

    /**
     * 根据简历ID获取简历在数据库中的全部信息
     * @param id 简历ID
     * @return Result 包含简历基本信息的结果对象，类型为Resume
     */
    @Override
    public Result getResumeById(Long id) {
        // 根据简历ID查询简历信息
        // 1. 根据id构建简历在redis中的key，并尝试从redis中获取缓存的简历信息
        String redisKey = RESUME_KEY + id;
        String resumeJSON = stringRedisTemplate.opsForValue().get(redisKey);
        Resume resume;
        if (resumeJSON != null && !resumeJSON.isEmpty()) {
            // 2. 如果缓存存在，则直接获取缓存的Resume对象
            log.info("Resume found in Redis cache with key: {}", redisKey);
            resume = JSONUtil.toBean(resumeJSON, Resume.class);
        }
        else if (resumeJSON != null) {
            // 3. 如果缓存存在但为空字符串，说明之前查询过该id但不存在对应的简历，命中了空缓存，直接返回未找到结果
            log.info("Resume not found in Redis cache with key: {} (NULL cache hit).", redisKey);
            // 刷新空缓存的过期时间
            stringRedisTemplate.expire(redisKey, COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("Resume not found.");
        }
        else {
            // 4. 如果缓存不存在，则尝试查询数据库获取简历信息
            log.info("Resume not found in Redis cache with key: {}. Fetching resume from database with ID: {}.", redisKey, id);
            resume = getById(id);
        }
        if (resume == null) {
            log.info("Resume not found in database with ID: {}", id);
            // 5. 未能找到该id对应的简历。为避免缓存穿透，缓存一个空值，设置较短的过期时间
            stringRedisTemplate.opsForValue().set(redisKey, "", COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("Resume not found.");
        }
        log.info("Resume found with ID: {}", id);
        // 6. 将查询到的简历信息缓存到Redis中，设置合理的过期时间
        String resumeToCache = JSONUtil.toJsonStr(resume);
        stringRedisTemplate.opsForValue().set(redisKey, resumeToCache, RESUME_TTL, RESUME_TTL_UNIT);
        return Result.success("Resume found successfully.", resume);
    }

    /**
     * 根据简历ID获取简历的全部信息
     * @param id 简历ID
     * @return  Result 包含简历详细信息的结果对象，类型为ResumeDTO
     */
    @Override
    public Result getResumeDTOById(Long id) {
        // 1. 根据简历ID查询简历信息
        Result resumeResult = getResumeById(id);
        if (resumeResult.getData() == null) {
            log.info("Resume not found with ID: {}", id);
            return Result.fail("Resume not found.");
        }
        // 2. 获取Resume对象
        Resume resume = (Resume) resumeResult.getData();
        // 6. 找到该id对应的简历，将Resume对象转换为ResumeDTO对象
        ResumeDTO resumeDTO = new ResumeDTO();
        BeanUtil.copyProperties(resume, resumeDTO);
        resumeDTO.setName(getOriginalFileName(resume.getFilePath())); // 从保存路径中获取简历的原始文件名并设置到dto中
        log.info("Successfully converted Resume to ResumeDTO.");
        return Result.success("Resume found successfully.", resumeDTO);
    }

    /**
     * 根据简历ID删除简历记录及对应的简历文件
     * 同时还需要通知向量数据库删除对应的简历嵌入记录
     * @param id 简历ID
     * @return Result 删除结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result deleteResumeById(Long id) {
        log.info("Trying deleting resume with ID: {}", id);
        Resume resume = getById(id);
        if (resume == null) {
            log.info("Resume not found with ID: {}", id);
            return Result.fail("Resume not found.");
        }
        String filePath = resume.getFilePath();
        // 删除数据库中的简历记录
        boolean removed = removeById(id);
        if (!removed) {
            log.error("Failed to delete resume record from database with ID: {}", id);
            return Result.fail("Failed to delete resume.");
        }
        // 构建该id对应的简历在redis中的key，并尝试删除缓存
        try {
            String redisKey = RESUME_KEY + id;
            if (Boolean.TRUE.equals(stringRedisTemplate.hasKey(redisKey))) {
                log.info("Deleting resume cache from Redis with key: {}", redisKey);
                stringRedisTemplate.delete(redisKey);
                log.info("Deleted resume cache successfully from Redis with key: {}", redisKey);
            } else {
                log.info("No resume cache found needs to delete in Redis with key: {}.", redisKey);
            }
        } catch (Exception e) {
            log.error("Failed to delete resume cache from Redis for resume ID: {}: {}", id, e.getMessage());
            throw new RuntimeException("Failed to delete resume cache from Redis.", e);
        }
        // 发送一个消息到rabbitmq，通知向量数据库删除对应的简历嵌入记录
        try {
            ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
            resumeAnalysisDTO.setUserId(resume.getUserId());    // 设置用户ID
            resumeAnalysisDTO.setRequestType(REQUEST_RESUME_DELETE);    // 设置请求类型为简历删除
            resumeAnalysisDTO.setResumeId(resume.getId());   // 设置简历ID
            log.info("Sending resume delete message to RabbitMQ for resume ID: {}", resumeAnalysisDTO.getResumeId());
            rabbitTemplate.convertAndSend(
                    DELETE_EXCHANGE_NAME,
                    RESUME_DELETE_ROUTING_KEY,
                    resumeAnalysisDTO
            );
            log.info("Resume delete message sent to RabbitMQ successfully for resume ID: {}", resumeAnalysisDTO.getResumeId());
        } catch (Exception e) {
            log.error("Failed to send resume delete message to RabbitMQ: {}", e.getMessage());
            throw new RuntimeException("Failed to send resume delete message to RabbitMQ.", e);
        }

        // 删除本地磁盘上的简历文件
        try {
            File file = new File(filePath);
            if (file.exists()) {
                if (file.delete()) {
                    log.info("Deleted resume file from disk: {}", filePath);
                } else {
                    log.error("Failed to delete resume file from disk: {}", filePath);
                    return Result.fail("Failed to delete resume file from disk.");
                }
            } else {
                log.warn("Resume file not found on disk, nothing to delete: {}", filePath);
            }
        } catch (Exception e) {
            log.error("Error occurred while deleting resume file from disk: {}", e.getMessage());
            throw new FileException("Error occurred while deleting resume file from disk.", e);
        }
        log.info("Resume deleted successfully with ID: {}", id);
        return Result.success("Resume deleted successfully.");
    }

    /**
     * 根据简历ID下载简历文件
     * @param id 简历ID
     * @return ResponseEntity 包含简历文件资源的响应实体
     */
    @Override
    public ResponseEntity<FileSystemResource> downloadResume(Long id) {
        // 查询简历信息
        log.info("Downloading resume with ID: {}", id);
        Resume resume = getById(id);
        if (resume == null) {
            log.info("Resume not found with ID: {}", id);
            return ResponseEntity.notFound().build();
        }
        String filePath = resume.getFilePath();
        File file = new File(filePath);
        if (!file.exists()) {
            log.info("Resume file not found at path: {}", filePath);
            return ResponseEntity.notFound().build();
        }

        try {
            // 设置响应头，指定文件名和Content-Disposition（即浏览器提示下载的文件名）
            HttpHeaders headers = new HttpHeaders();
            headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getName() + "\"");

            // 创建带有文件资源的ResponseEntity，并返回
            return ResponseEntity.ok()
                    .headers(headers)
                    .contentLength(file.length())
                    .contentType(Files.probeContentType(file.toPath()) != null
                            ? MediaType.parseMediaType(Files.probeContentType(file.toPath()))
                            : MediaType.APPLICATION_OCTET_STREAM)
                    .body(new FileSystemResource(file));
        } catch (IOException e) {
            log.error("Error occurred while preparing resume file for download: {}", e.getMessage());
            throw new FileException("Error occurred while preparing resume file for download.", e);
        }
    }

    /**
     * 上传简历文件
     * @param file 简历文件
     * @return Result 上传结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result upload(MultipartFile file) {
        String file_name = file.getOriginalFilename();
        // 首先判断上传的文件名是否有效，从而避免空文件上传
        if (file_name == null || file_name.isEmpty()) {
            log.error("Invalid file name: {}", file_name);
            return Result.fail("The uploaded file is empty.");
        }
        // 判断是否为pdf格式的文件
        if (!file_name.endsWith(".pdf")) {
            log.error("Invalid file format for file: {}. Only PDF files are allowed.", file_name);
            return Result.fail("Only PDF files are allowed.");
        }
        log.info("Resume file uploading ...");
        String save_path = fileProperties.getResume_save_path();
        // 简历上传后采用本地保存
        // 首先检查简历保存的根目录是否存在
        File dir = new File(save_path);
        if (!dir.exists()) {
            log.info("Resume save root dir doesn't exist. Trying to create: {}", save_path);
            if(dir.mkdirs()) {
                log.info("Created directory: {}", save_path);
            } else {
                log.error("Failed to create directory: {}", save_path);
                return Result.fail("Failed to create resume save directory.");
            }
        }
        // 然后检查以用户ID命名的子目录是否存在
        Path path = Path.of(save_path, UserThreadLocal.get().toString());
        dir = new File(path.toString());
        if (!dir.exists()) {
            log.info("User resume save dir doesn't exist. Trying to create: {}", path);
            if (dir.mkdirs()) {
                log.info("Created directory: {}", path);
            } else {
                log.error("Failed to create directory: {}", path);
                return Result.fail("Failed to create user resume save directory.");
            }
        }
        // 构建简历文件的保存路径
        int extension_pos = file_name.lastIndexOf(".");
        String new_file_name = file_name.substring(0, extension_pos) + "_" + UUID.randomUUID() + file_name.substring(extension_pos);    // 为避免文件名冲突，在文件名后（扩展名前）添加UUID
        path = Path.of(path.toString(), new_file_name);
        String resume_path = path.toString();
        ResumeDTO resumeDTO = new ResumeDTO();

        // 构造Resume实体对象
        Resume resume = new Resume();
        resume.setUserId(UserThreadLocal.get());
        resume.setFilePath(resume_path);
        resume.setCreateTime(LocalDateTime.now());
        resume.setUpdateTime(LocalDateTime.now());
        try {
            // 将新的简历文件的相关信息写入数据库表
            boolean success = save(resume);     // 保存成功后，save方法会自动将数据库生成的ID回填到resume对象中
            if (!success) {
                log.error("Failed to save resume info to database for user ID: {}", UserThreadLocal.get());
                return Result.fail("Resume upload failed: unable to save resume info to database.");
            }
            BeanUtil.copyProperties(resume, resumeDTO);
            resumeDTO.setName(file_name); // 设置简历的原始文件名
        } catch (Exception e) {
            log.error("Failed to save resume info to database: {}", e.getMessage());
            throw new DbException("Failed to save resume info to database due to an exception.", e);
        }

        try {
            // 保存简历文件到本地磁盘
            file.transferTo(new File(resume_path));
            log.info("Resume uploaded successfully: {}", file_name);
            log.info("Saved resume file to disk at path: {}", resume_path);
        } catch (Exception e) {
            log.error("Resume upload failed: {}", e.getMessage());
            throw new FileException("Resume upload failed due to an exception.", e);
        }

        try {
            // 发送一个消息到rabbitmq，通知向量数据库将新的简历信息嵌入
            // 首先要构造消息体ResumeAnalysisDTO对象
            ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
            resumeAnalysisDTO.setUserId(UserThreadLocal.get());     // 设置用户ID
            resumeAnalysisDTO.setRequestType(REQUEST_RESUME_UPLOAD); // 设置请求类型为简历上传
            resumeAnalysisDTO.setResumeId(resume.getId());      // 设置简历ID
            resumeAnalysisDTO.setResumeFilePath(resume_path);   // 设置简历文件路径
            // 手动转换文件路径为wsl可访问路径（因为python程序部署在wsl内）
            String wsl_resumePath = parsePath(resumeAnalysisDTO.getResumeFilePath());
            resumeAnalysisDTO.setResumeFilePath(wsl_resumePath);    // 设置简历文件路径修改为wsl路径
            resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
            resumeAnalysisDTO.setCreateTime(resume.getCreateTime());    // 设置创建时间
            log.info("Prepared resume upload message for User ID: {}, Resume ID: {}.",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId());

            // 发送消息到RabbitMQ的指定交换机和路由键
            log.info("Sending resume upload message to RabbitMQ for resume ID: {}", resumeAnalysisDTO.getResumeId());
            rabbitTemplate.convertAndSend(
                    UPLOAD_EXCHANGE_NAME,
                    RESUME_UPLOAD_ROUTING_KEY,
                    resumeAnalysisDTO
            );
        } catch (Exception e) {
            log.error("Resume upload failed: {}", e.getMessage());
            throw new RuntimeException("Resume upload failed due to an exception.", e);
        }
        return Result.success("Resume uploaded successfully.", resumeDTO);
    }
}
