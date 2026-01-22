package org.kira.resumesystem.service.serviceImpl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.config.FileProperties;
import org.kira.resumesystem.entity.dto.*;
import org.kira.resumesystem.entity.po.JD;
import org.kira.resumesystem.exceptions.DbException;
import org.kira.resumesystem.exceptions.FileException;
import org.kira.resumesystem.mapper.JDMapper;
import org.kira.resumesystem.service.IJDService;
import org.kira.resumesystem.utils.RedisCuckooFilterTool;
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

import javax.annotation.PostConstruct;
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
@EnableConfigurationProperties(value = {FileProperties.class})
@RequiredArgsConstructor
public class JDServiceImpl extends ServiceImpl<JDMapper, JD> implements IJDService {
    private final FileProperties fileProperties;
    private final StringRedisTemplate stringRedisTemplate;
    private final RabbitTemplate rabbitTemplate;
    private final RedisCuckooFilterTool redisCuckooFilterTool;

    @PostConstruct
    public void initCuckooFilter() {
        // 初始化JD Cuckoo Filter
        log.info("Initializing JD Cuckoo Filter...");
        boolean reserved = false;
        try {
            reserved = redisCuckooFilterTool.reserve(JD_CUCKOO_FILTER_KEY, JD_CUCKOO_FILTER_CAPACITY);
        } catch (Exception e) {
            // 由于redisCuckooFilterTool.reserve内部判断如果是该key已存在导致异常，则不抛出
            // 所以如果捕获到异常，则需要将该异常继续抛出
            log.error("Failed to initialize JD Cuckoo Filter: {}", e.getMessage());
            throw e;
        }
        if (reserved) {
            log.info("Initialized JD Cuckoo Filter successfully with key: {}, capacity {}.", JD_CUCKOO_FILTER_KEY, JD_CUCKOO_FILTER_CAPACITY);
        } else {
            log.info("JD Cuckoo Filter (key: {}) already exists.", JD_CUCKOO_FILTER_KEY);
            return;
        }
        log.info("Adding existing JD IDs into JD Cuckoo Filter ...");
        List<String> idList = lambdaQuery()
                .select(JD::getId)
                .list()
                .stream()
                .map(
                    jd -> String.valueOf(jd.getId())
                )
                .collect(Collectors.toList());
        redisCuckooFilterTool.batchAdd(JD_CUCKOO_FILTER_KEY, idList);
        log.info("Added existing JD IDs into Resume Cuckoo Filter successfully.");
    }

    public String getJdName(JD jd) {
        String name = getOriginalFileName(jd.getFilePath());
        if (name.isEmpty()) {
            name = jd.getTitle();   // 如果无法从路径中解析出文件名（路径为空），则使用标题作为JD名
        }
        return name;
    }

    /**
     * 列出系统中所有的职位描述（JD）
     * 注意：该方法不会返回JD的完整信息，只返回部分属性以供列表展示
     * 需要查询数据库的属性包括：id, userId, title, company, location, salary, file_path, createTime, updateTime
     * @return Result 包含职位描述列表的结果对象
     */
    @Override
    public Result listAllJDs() {
        List<JDDTO> jdList = lambdaQuery()
                .select(
                        JD::getId,
                        JD::getUserId,
                        JD::getTitle,
                        JD::getCompany,
                        JD::getLocation,
                        JD::getSalary,
                        JD::getFilePath,
                        JD::getCreateTime,
                        JD::getUpdateTime
                )
                .orderByDesc(JD::getUpdateTime)
                .list()
                .stream().map(jd -> {
                    JDDTO dto = new JDDTO();
                    // 复制JD实体对象的属性到DTO对象
                    // 注意部分属性不必展示在列表中，所以就不复制传递给前端
                    BeanUtil.copyProperties(jd, dto, "description", "requirements", "bonus");
                    dto.setName(getJdName(jd));
                    return dto;
                }).collect(Collectors.toList());
        if(jdList.isEmpty()) {
            log.info("No JDs found in the system.");
            return Result.success("No JDs found.", jdList);
        }
        log.info("Found {} JDs in the system.", jdList.size());
        return Result.success("JDs found successfully.", jdList);
    }

    /**
     * 列出当前用户的所有职位描述（JD）
     * 注意：该方法不会返回JD的完整信息，只返回部分属性以供列表展示
     * 需要查询数据库的属性包括：id, userId, title, company, location, salary, file_path, createTime, updateTime
     * @return Result 包含职位描述列表的结果对象
     */
    @Override
    public Result listJDs() {
        Long userId = UserThreadLocal.get();
        log.info("Listing JDs for user ID: {}", userId);
        List<JDDTO> jdList = lambdaQuery()
                .select(
                        JD::getId,
                        JD::getUserId,
                        JD::getTitle,
                        JD::getCompany,
                        JD::getLocation,
                        JD::getSalary,
                        JD::getFilePath,
                        JD::getCreateTime,
                        JD::getUpdateTime
                )
                .eq(JD::getUserId, userId)
                .orderByDesc(JD::getCreateTime)
                .list()
                .stream().map(jd -> {
                    JDDTO dto = new JDDTO();
                    BeanUtil.copyProperties(jd, dto);
                    dto.setName(getJdName(jd));
                    return dto;
                }).collect(Collectors.toList());
        if(jdList.isEmpty()) {
            log.info("No JDs found for user ID: {}", UserThreadLocal.get());
            return Result.success("No JDs found.", jdList);
        }
        log.info("Found {} JDs for user ID: {}", jdList.size(), userId);
        return Result.success("JDs found successfully.", jdList);
    }

    /**
     * 分页查询职位描述（JD）
     * （查询全部或者某用户的JD，取决于筛选条件filterCondition中的userId是否为null）
     * 注意：该方法不会返回JD的完整信息，只返回部分属性以供列表展示
     * 需要查询数据库的属性包括：id, userId, title, company, location, salary, file_path, createTime, updateTime
     * @param pageNum 页码
     * @param pageSize 每页大小
     * @return Result 包含职位描述列表的结果对象
     */
    @Override
    public Result pageListJDs(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        log.info("Listing JDs at page {}, page size: {}", pageNum, pageSize);
        // 创建Page分页对象
        Page<JD> page = new Page<>(pageNum, pageSize);
        // 使用Mapper中自定义的分页查询方法，传入分页对象和过滤条件
        baseMapper.selectJDsByCondition(page, filterCondition);
        // 将查询得到的JD对象列表转换为JDDTO对象列表
        List<JDDTO> jdDTOList = page.getRecords().stream().map(jd -> {
            JDDTO dto = new JDDTO();
            BeanUtil.copyProperties(jd, dto);
            dto.setName(getJdName(jd));
            return dto;
        }).collect(Collectors.toList());
        // 将jdDTOList转换为PageResult对象返回
        PageResult<JDDTO> pageResult = new PageResult<>(
                page.getPages(),
                page.getTotal(),
                page.getCurrent(),
                page.getSize(),
                jdDTOList
        );
        if(jdDTOList.isEmpty()) {
            log.info("No JDs found on page {}, page size {}", pageNum, pageSize);
            return Result.success("No JDs found.", pageResult);
        }
        log.info("Found {} JDs on page {}, page size {}.", jdDTOList.size(), pageNum, pageSize);
        return Result.success("JDs found successfully " + "on page " + pageNum + ", page size "+ pageSize + ".", pageResult);
    }

    /**
     * 分页查询当前用户的职位描述（JD）
     * @param pageNum 页码
     * @param pageSize 每页大小
     * @param filterCondition 筛选条件
     * @return Result 包含职位描述列表的结果对象
     */
    @Override
    public Result pageListUserJDs(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        log.info("Listing current user's JDs at page {}, page size: {}", pageNum, pageSize);
        // 将当前用户ID设置到筛选条件中
        filterCondition.setUserId(UserThreadLocal.get());
        return pageListJDs(pageNum, pageSize, filterCondition);
    }

    /**
     * 分页查询系统中所有的职位描述（JD）
     * @param pageNum 页码
     * @param pageSize 每页大小
     * @param filterCondition 筛选条件
     * @return Result 包含职位描述列表的结果对象
     */
    @Override
    public Result pageListAllJDs(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        log.info("Listing all user's JDs at page {}, page size: {}", pageNum, pageSize);
        return pageListJDs(pageNum, pageSize, filterCondition);
    }

    /**
     * 根据ID获取职位描述（JD）在数据库中的全部信息
     * @param id 职位描述ID
     * @return Result 包含职位描述信息的结果对象，类型为JD
     */
    @Override
    public Result getJDById(Long id) {
        // 根据指定的JD id查询对应JD的信息
        // 1. 首先构建该JD id对应的在Redis中的缓存key，并查询Redis尝试获取缓存的JD信息
        String redisKey = JD_KEY + id;
        String jdJSON = stringRedisTemplate.opsForValue().get(redisKey);
        JD jd;
        if (jdJSON != null && !jdJSON.isEmpty()) {
            // 2. 如果Redis中存在该JD的缓存信息，则直接获取缓存的JD对象
            jd = JSONUtil.toBean(jdJSON, JD.class);
            log.info("JD found in Redis cache with key: {}", redisKey);
        }
        else if (jdJSON != null) {
            // 3. 如果Redis中缓存的JD信息为空字符串，说明该JD不存在，命中了空缓存，直接返回JD未找到的结果
            log.info("JD not found in Redis cache with key: {} (NULL cache hit).", redisKey);
            // 刷新空缓存的过期时间
            stringRedisTemplate.expire(redisKey, COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("JD not found.");
        }
        else {
            // 4. 如果Redis中不存在该JD的缓存信息，则查询数据库获取JD信息
            log.info("JD not found in Redis cache with key: {}. Fetching JD from database with ID: {}...", redisKey, id);
            jd = getById(id);
        }
        if (jd == null) {
            // 5. 如果数据库中也不存在该JD信息，则返回JD未找到的结果
            log.info("JD not found in database with ID: {}", id);
            // 为防止缓存穿透，将该JD的空信息缓存到Redis，设置较短的过期时间
            stringRedisTemplate.opsForValue().set(redisKey, "", COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("JD not found.");
        }
        log.info("JD found with ID: {}", id);
        // 6. 将该JD信息缓存到Redis，设置适当的过期时间
        String jdToCache = JSONUtil.toJsonStr(jd);
        stringRedisTemplate.opsForValue().set(redisKey, jdToCache, JD_TTL, JD_TTL_UNIT);
        return Result.success("JD found successfully.", jd);
    }

    /**
     * 根据ID获取职位描述（JD）的全部信息
     * @param id 职位描述ID
     * @return Result 包含职位描述信息的结果对象，类型为JDDTO
     */
    @Override
    public Result getJDDTOById(Long id) {
        // 1. 根据id获取JD信息
        Result jdResult = getJDById(id);
        if (jdResult.getData() == null) {
            log.info("JD not found with ID: {}", id);
            return Result.fail("JD not found.");
        }
        JD jd = (JD) jdResult.getData();
        // 2. 找到该id对应的JD，将JD对象转换为JDDTO对象
        JDDTO jdDTO = new JDDTO();
        BeanUtil.copyProperties(jd, jdDTO);
        jdDTO.setName(getJdName(jd));
        log.info("Successfully converted JD to JDDTO.");
        return Result.success("JD found successfully.", jdDTO);
    }

    /**
     * 根据ID删除职位描述（JD）
     * @param id 职位描述ID
     * @return Result 删除结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result deleteJDById(Long id) {
        log.info("Trying deleting JD with ID: {}", id);
        // 首先查询JD信息，确认JD存在
        JD jd = getById(id);
        if (jd == null) {
            log.error("JD not found with ID: {}", id);
            return Result.fail("JD not found.");
        }
        // 删除数据库中的JD记录
        boolean success = removeById(id);
        if (!success) {
            log.error("Failed to delete JD record from database with ID: {}", id);
            return Result.fail("Failed to delete JD.");
        }
        // 构建该id对应的JD在Redis中的缓存key，并尝试删除Redis中的JD缓存
        try {
            String redisKey = JD_KEY + id;
            if (Boolean.TRUE.equals(stringRedisTemplate.hasKey(redisKey))) {
                log.info("Deleting JD cache from Redis with key: {}", redisKey);
                stringRedisTemplate.delete(redisKey);
                log.info("Deleted JD cache successfully from Redis with key: {}", redisKey);
            }
            else {
                log.info("No JD cache found needs to delete in Redis with key: {}.", redisKey);
            }
        } catch (Exception e) {
            log.error("Failed to delete JD cache from Redis for JD ID: {}: {}", id, e.getMessage());
            throw new RuntimeException("Failed to delete JD cache from Redis.", e);
        }
        // 发送一个消息到rabbitmq，通知向量数据库删除对应的JD嵌入
        try {
            // 构建消息体ResumeAnalysisDTO对象
            ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
            resumeAnalysisDTO.setUserId(jd.getUserId());     // 设置用户ID
            resumeAnalysisDTO.setRequestType(REQUEST_JD_DELETE); // 设置请求类型为JD删除
            resumeAnalysisDTO.setJdID(id);      // 设置JD ID
            log.info("Sending JD delete message to RabbitMQ for JD ID: {}", id);
            rabbitTemplate.convertAndSend(
                    DELETE_EXCHANGE_NAME,
                    JD_DELETE_ROUTING_KEY,
                    resumeAnalysisDTO
            );
        } catch (Exception e) {
            log.error("Failed to send JD delete message to RabbitMQ for JD ID: {}: {}", id, e.getMessage());
            throw new RuntimeException("Failed to send JD delete message to RabbitMQ.", e);
        }

        try {
            // 删除本地磁盘上的JD文件
            String filePath = jd.getFilePath();
            if (filePath.isEmpty()) {
                log.warn("JD file path is empty for JD ID: {}. Skipping file deletion.", id);
            }
            else {
                File file = new File(filePath);
                if (file.exists()) {
                    if (file.delete()) {
                        log.info("JD file deleted successfully at path: {}", filePath);
                    } else {
                        log.error("Failed to delete JD file at path: {}", filePath);
                        throw new FileException("Failed to delete JD file at path: " + filePath);
                    }
                } else {
                    log.warn("JD file not found at path: {}", filePath);
                }
            }
        } catch (FileException e) {
            log.error("Error occurred while deleting JD file from disk: {}", e.getMessage());
            throw new FileException("Error occurred while deleting JD file from disk.", e);
        }
        log.info("JD deleted successfully with ID: {}", id);
        return Result.success("JD deleted successfully.");
    }

    /**
     * 下载职位描述（JD）文件
     * @param id 职位描述ID
     * @return ResponseEntity 包含文件资源的响应实体
     */
    @Override
    public ResponseEntity<FileSystemResource> downloadJD(Long id) {
        // 查询简历信息
        log.info("Downloading JD with ID: {}", id);
        JD jd = getById(id);
        if (jd == null) {
            log.info("JD not found with ID: {}", id);
            return ResponseEntity.notFound().build();
        }
        String filePath = jd.getFilePath();
        File file = new File(filePath);
        if (!file.exists()) {
            log.info("JD file not found at path: {}", filePath);
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
     * 上传JD文件
     * @param file JD文件
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
        log.info("JD file uploading ...");
        String save_path = fileProperties.getJd_save_path();
        // 简历上传后采用本地保存
        // 首先检查简历保存的根目录是否存在
        File dir = new File(save_path);
        if (!dir.exists()) {
            log.info("JD save root dir doesn't exist. Trying to create: {}", save_path);
            if(dir.mkdirs()) {
                log.info("Created directory: {}", save_path);
            } else {
                log.error("Failed to create directory: {}", save_path);
                return Result.fail("Failed to create JD save directory.");
            }
        }
        // 然后检查以用户ID命名的子目录是否存在
        Path path = Path.of(save_path, UserThreadLocal.get().toString());
        dir = new File(path.toString());
        if (!dir.exists()) {
            log.info("User JD save dir doesn't exist. Trying to create: {}", path);
            if (dir.mkdirs()) {
                log.info("Created directory: {}", path);
            } else {
                log.error("Failed to create directory: {}", path);
                return Result.fail("Failed to create user JD save directory.");
            }
        }
        // 构建简历文件的保存路径
        int extension_pos = file_name.lastIndexOf(".");
        String new_file_name = file_name.substring(0, extension_pos) + "_" + UUID.randomUUID() + file_name.substring(extension_pos);    // 为避免文件名冲突，在文件名后（扩展名前）添加UUID
        path = Path.of(path.toString(), new_file_name);
        String jd_path = path.toString();
        JDDTO jdDTO = new JDDTO();

        // 构造JD实体对象
        JD jd = new JD();
        jd.setUserId(UserThreadLocal.get());
        jd.setFilePath(jd_path);
        jd.setCreateTime(LocalDateTime.now());
        jd.setUpdateTime(LocalDateTime.now());
        try {
            // 将新的简历文件的相关信息写入数据库表
            boolean success = save(jd);     // 保存成功后，save方法会将生成的ID回填到jd对象中
            if (!success) {
                log.error("Failed to save JD info to database for user ID: {}", UserThreadLocal.get());
                return Result.fail("JD upload failed: unable to save JD info to database.");
            }
            BeanUtil.copyProperties(jd, jdDTO);
            jdDTO.setName(file_name);
        } catch (Exception e) {
            log.error("Failed to save JD info to database: {}", e.getMessage());
            throw new DbException("Failed to save JD info to database due to an exception.", e);
        }

        try {
            // 保存简历文件到本地磁盘
            file.transferTo(new File(jd_path));
            log.info("JD uploaded successfully: {}", file_name);
            log.info("Saved JD file to disk at path: {}", jd_path);
        } catch (Exception e) {
            log.error("JD upload failed: {}", e.getMessage());
            throw new FileException("JD upload failed due to an exception.", e);
        }

        try {
            // 发送一个消息到rabbitmq，通知向量数据库将新的简历信息嵌入
            // 首先要构造消息体ResumeAnalysisDTO对象
            ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
            resumeAnalysisDTO.setUserId(UserThreadLocal.get());     // 设置用户ID
            resumeAnalysisDTO.setRequestType(REQUEST_JD_UPLOAD); // 设置请求类型为简历上传
            resumeAnalysisDTO.setJdID(jd.getId());      // 设置简历ID
            resumeAnalysisDTO.setJdFilePath(jd_path);   // 设置简历文件路径
            // 手动转换文件路径为wsl可访问路径（因为python程序部署在wsl内）
            String wsl_jdPath = parsePath(resumeAnalysisDTO.getJdFilePath());
            resumeAnalysisDTO.setJdFilePath(wsl_jdPath);    // 设置JD文件路径修改为wsl路径
            resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
            resumeAnalysisDTO.setCreateTime(jd.getCreateTime());    // 设置创建时间
            log.info("Prepared JD upload message for User ID: {}, JD ID: {}.",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getJdID());

            // 发送消息到RabbitMQ的指定交换机和路由键
            log.info("Sending JD upload message to RabbitMQ for JD ID: {}", resumeAnalysisDTO.getJdID());
            rabbitTemplate.convertAndSend(
                    UPLOAD_EXCHANGE_NAME,
                    JD_UPLOAD_ROUTING_KEY,
                    resumeAnalysisDTO
            );
            log.info("JD upload message sent to RabbitMQ successfully for JD ID: {}", resumeAnalysisDTO.getJdID());
        } catch (Exception e) {
            log.error("JD upload failed: {}", e.getMessage());
            throw new RuntimeException("JD upload failed due to an exception.", e);
        }
        return Result.success("JD uploaded successfully.", jdDTO);
    }

    /**
     * 上传JD信息
     * @param jdDTO JD信息对象
     * @return Result 上传结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result upload(JDDTO jdDTO) {
        log.info("JD info uploading ...");
        LocalDateTime now = LocalDateTime.now();
        Long userId = UserThreadLocal.get();
        // 根据传入的JDDTO构造JD实体对象
        JD jd = new JD();
        BeanUtil.copyProperties(jdDTO, jd, "id", "userID", "createTime", "updateTime");
        jd.setUserId(userId);
        jd.setCreateTime(now);
        jd.setUpdateTime(now);
        jd.setFilePath(""); // 由于没有上传文件，文件路径置为空字符串
        jdDTO.setName(getJdName(jd));
        try {
            // 将新的简历文件的相关信息写入数据库表
            boolean success = save(jd);     // 保存成功后，save方法会将生成的ID回填到jd对象中
            if (!success) {
                log.error("Failed to save JD info to database for user ID: {}", UserThreadLocal.get());
                return Result.fail("JD upload failed: unable to save JD info to database.");
            }
        } catch (Exception e) {
            log.error("Failed to save JD info to database: {}", e.getMessage());
            throw new DbException("Failed to save JD info to database due to an exception.", e);
        }

        try {
            // 发送一个消息到rabbitmq，通知向量数据库将新的简历信息嵌入
            // 首先要构造消息体ResumeAnalysisDTO对象
            ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
            BeanUtil.copyProperties(jd, resumeAnalysisDTO);  // 复制jdDTO内的JD信息到消息体resumeAnalysisDTO
            // 手动设置部分字段
            resumeAnalysisDTO.setUserId(userId);     // 设置用户ID
            resumeAnalysisDTO.setRequestType(REQUEST_JD_UPLOAD); // 设置请求类型为简历上传
            resumeAnalysisDTO.setJdID(jd.getId());      // 设置简历ID
            resumeAnalysisDTO.setJdFilePath("");   // 设置简历文件路径为空字符串
            resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
            resumeAnalysisDTO.setCreateTime(jd.getCreateTime());    // 设置创建时间
            log.info("Prepared JD upload message for User ID: {}, JD ID: {}.",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getJdID());

            // 发送消息到RabbitMQ的指定交换机和路由键
            log.info("Sending JD upload message to RabbitMQ for JD ID: {}", resumeAnalysisDTO.getJdID());
            rabbitTemplate.convertAndSend(
                    UPLOAD_EXCHANGE_NAME,
                    JD_UPLOAD_ROUTING_KEY,
                    resumeAnalysisDTO
            );
            log.info("JD upload message sent to RabbitMQ successfully for JD ID: {}", resumeAnalysisDTO.getJdID());
        } catch (Exception e) {
            log.error("JD upload failed: {}", e.getMessage());
            throw new RuntimeException("JD upload failed due to an exception.", e);
        }
        return Result.success("JD uploaded successfully.", jdDTO);
    }
}
