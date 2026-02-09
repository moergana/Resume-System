package org.kira.resumesystem.service.serviceImpl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.*;
import org.kira.resumesystem.entity.po.JD;
import org.kira.resumesystem.entity.po.Resume;
import org.kira.resumesystem.entity.po.ResumeAnalysis;
import org.kira.resumesystem.entity.vo.ResumeAnalysisVO;
import org.kira.resumesystem.exceptions.DbException;
import org.kira.resumesystem.mapper.ResumeAnalysisMapper;
import org.kira.resumesystem.mapper.ResumeAnalysisVOMapper;
import org.kira.resumesystem.service.IResumeAnalysisService;
import org.kira.resumesystem.utils.FileTool;
import org.kira.resumesystem.utils.RedisCuckooFilterTool;
import org.kira.resumesystem.utils.UserThreadLocal;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.PostConstruct;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

import static org.kira.resumesystem.config.mq.RabbitMqConfig.*;
import static org.kira.resumesystem.utils.Constants.*;
import static org.kira.resumesystem.utils.FileTool.getOriginalFileName;
import static org.kira.resumesystem.utils.RedisConstants.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class ResumeAnalysisServiceImpl extends ServiceImpl<ResumeAnalysisMapper, ResumeAnalysis> implements IResumeAnalysisService {
    private final ResumeServiceImpl resumeService;
    private final JDServiceImpl jdService;
    private final StringRedisTemplate stringRedisTemplate;
    private final RabbitTemplate rabbitTemplate;
    private final ResumeAnalysisVOMapper resumeAnalysisVOMapper;
    private final RedisCuckooFilterTool redisCuckooFilterTool;
    private final RedissonClient redissonClient;

    @PostConstruct
    public void initCuckooFilter() {
        // 初始化Resume Analysis Cuckoo Filter
        log.info("Initializing Resume Analysis Cuckoo Filter...");
        boolean reserved = false;
        try {
            reserved = redisCuckooFilterTool.reserve(RESUME_ANALYSIS_CUCKOO_FILTER_KEY, RESUME_ANALYSIS_CUCKOO_FILTER_CAPACITY);
        } catch (Exception e) {
            // 由于redisCuckooFilterTool.reserve内部判断如果是该key已存在导致异常，则不抛出
            // 所以如果捕获到异常，则需要将该异常继续抛出
            log.error("Failed to initialize Resume Analysis Cuckoo Filter. Error: {}", e.getMessage());
            throw e;
        }
        if (reserved) {
            log.info("Initialized Resume Analysis Cuckoo Filter successfully with key: {}, capacity {}.", RESUME_ANALYSIS_CUCKOO_FILTER_KEY, RESUME_ANALYSIS_CUCKOO_FILTER_CAPACITY);
        } else {
            log.info("Resume Analysis Cuckoo Filter (key: {}) already exists.", RESUME_ANALYSIS_CUCKOO_FILTER_KEY);
            return;
        }
        log.info("Adding existing Resume Analysis IDs into Resume Analysis Cuckoo Filter ...");
        List<String> idList = lambdaQuery()
                .select(ResumeAnalysis::getId)
                .list()
                .stream()
                .map(
                    resumeAnalysis -> String.valueOf(resumeAnalysis.getId())
                ).collect(Collectors.toList());
        redisCuckooFilterTool.batchAdd(RESUME_ANALYSIS_CUCKOO_FILTER_KEY, idList);
        log.info("Added existing Resume Analysis IDs into Resume Analysis Cuckoo Filter successfully.");
    }


    /**
     * 列出当前登录用户的所有简历分析记录
     * 注意：该方法不返回ResumeAnalysis的全部属性，只返回部分需要前端展示的属性
     * 需要查询数据库的属性包括：id, userId, resumeId, jdID, requestType, status, createTime
     * @return 结果对象，包含简历分析记录列表
     */
    @Override
    public Result listResumeAnalysis() {
        // 获取当前用户的所有简历分析记录
        log.info("Listing all resume analysis records of the current login user.");
        // 1. 首先要获取当前登录的用户ID
        Long userId = UserThreadLocal.get();
        // 2. 查询该用户的所有简历分析记录
        List<ResumeAnalysis> analysisList = lambdaQuery()
                .select(
                        ResumeAnalysis::getId,
                        ResumeAnalysis::getUserId,
                        ResumeAnalysis::getResumeId,
                        ResumeAnalysis::getJdID,
                        ResumeAnalysis::getRequestType,
                        ResumeAnalysis::getStatus,
                        ResumeAnalysis::getCreateTime
                )
                .eq(ResumeAnalysis::getUserId, userId)
                .orderByDesc(ResumeAnalysis::getCreateTime)
                .list();
        // 3. 如果没有查询到任何记录，则返回空结果
        if (analysisList.isEmpty()) {
            log.info("No resume analysis records found for User ID {}.", userId);
            return Result.success("No resume analysis records found.", analysisList);
        }
        log.info("Successfully retrieved {} resume analysis records for User ID {}.", analysisList.size(), userId);
        log.info("Trying converting ResumeAnalysis list to ResumeAnalysisVO list...");
        // 4. 将查询得到的ResumeAnalysis对象列表转换为ResumeAnalysisVO对象列表
        List<ResumeAnalysisVO> resumeAnalysisVOList = convertResumeAnalysisListToVOList(analysisList);
        return Result.success("Successfully get all resume analysis records of the current login user.", resumeAnalysisVOList);
    }

    /**
     * 分页查询简历分析记录
     * （查询全部或者某用户的分析记录，根据筛选条件filterCondition中的userId是否为null）
     * @param pageNum 页码（第几页）
     * @param pageSize 页面大小（每页的记录数）
     * @return 结果对象，包含简历分析记录列表
     */
    @Override
    public Result pageListResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        // 获取当前用户的所有简历分析记录，分页返回
        log.info("Listing resume analysis records for User ID {} on page {}, page size {}.", UserThreadLocal.get(), pageNum, pageSize);
        // 1. 首先要获取当前登录的用户ID
        Long userId = UserThreadLocal.get();
        // 2. 查询该用户的所有简历分析记录
        Page<ResumeAnalysisVO> page = new Page<>(pageNum, pageSize);
        resumeAnalysisVOMapper.pageSelectResumeAnalysisVOByCondition(page, filterCondition);
        List<ResumeAnalysisVO> resumeAnalysisVOList = page.getRecords().stream()
                .map(resumeAnalysisVO -> {
                    // 将保存在VO的resumeName和jdName字段中的文件路径转换为原始文件名
                    if (!resumeAnalysisVO.getResumeName().isEmpty()) {
                        String name = getOriginalFileName(resumeAnalysisVO.getResumeName());
                        resumeAnalysisVO.setResumeName(name);
                    }
                    if (resumeAnalysisVO.getJdName().isEmpty()){
                        resumeAnalysisVO.setJdName(resumeAnalysisVO.getTitle());
                    } else {
                        resumeAnalysisVO.setJdName(getOriginalFileName(resumeAnalysisVO.getJdName()));
                    }
                    return resumeAnalysisVO;
                }).collect(Collectors.toList());
        // 3. 将resumeAnalysisVOList封装为PageResult对象返回
        PageResult<ResumeAnalysisVO> pageResult = new PageResult<>(
                page.getPages(),
                page.getTotal(),
                page.getCurrent(),
                page.getSize(),
                resumeAnalysisVOList
        );
        if (resumeAnalysisVOList.isEmpty()) {
            log.info("No resume analysis records found for User ID {} on page {}, page size {}.", userId, pageNum, pageSize);
            return Result.success("No resume analysis records found.", pageResult);
        }
        log.info("Successfully retrieved {} resume analysis records for User ID {} on page {}, page size {}.", resumeAnalysisVOList.size(), userId, pageNum, pageSize);
        return Result.success("Successfully get resume analysis records of the current login user on page " + pageNum + ", page size "+ pageSize + ".", pageResult);
    }

    /**
     * 分页查询当前登录用户的简历分析记录
     * @param pageNum 页码
     * @param pageSize 页面大小
     * @param filterCondition 筛选条件
     * @return 结果对象，包含简历分析记录列表
     */
    @Override
    public Result pageListUserResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        log.info("Listing current user's resume analysis records on page {}, page size {}.", pageNum, pageSize);
        // 将当前登录用户ID设置到filterCondition中
        filterCondition.setUserId(UserThreadLocal.get());
        return pageListResumeAnalysis(pageNum, pageSize, filterCondition);
    }

    /**
     * 分页查询所有用户的简历分析记录
     * @param pageNum 页码
     * @param pageSize 页面大小
     * @param filterCondition 筛选条件
     * @return 结果对象，包含简历分析记录列表
     */
    @Override
    public Result pageListAllResumeAnalysis(Integer pageNum, Integer pageSize, FilterCondition filterCondition) {
        log.info("Listing all users' resume analysis records on page {}, page size {}.", pageNum, pageSize);
        return pageListResumeAnalysis(pageNum, pageSize, filterCondition);
    }

    /**
     * 将ResumeAnalysis对象列表转换为ResumeAnalysisVO对象列表
     * @param analysisList ResumeAnalysis对象列表
     * @return ResumeAnalysisVO对象列表
     */
    @Override
    public List<ResumeAnalysisVO> convertResumeAnalysisListToVOList(List<ResumeAnalysis> analysisList) {
        List<ResumeAnalysisVO> resumeAnalysisVOList = new ArrayList<>();
        List<Long> resumeIds = new ArrayList<>();
        List<Long> jdIds = new ArrayList<>();
        analysisList.forEach(analysis -> {
            resumeIds.add(analysis.getResumeId());
            jdIds.add(analysis.getJdID());
        });
        // 批量查询简历和JD，减少数据库建立连接的次数
        List<Resume> resumes = resumeService.list(
                new LambdaQueryWrapper<Resume>()
                        .select(
                                Resume::getId,
                                Resume::getUserId,
                                Resume::getFilePath
                        )
                        .in(Resume::getId, resumeIds)
        );
        List<JD> jds = jdService.list(
                new LambdaQueryWrapper<JD>()
                        .select(
                                JD::getId,
                                JD::getUserId,
                                JD::getTitle,
                                JD::getFilePath
                        )
                        .in(JD::getId, jdIds)
        );
        // 将简历和JD分别放入Map，方便后续根据ID查找
        Map<Long, Resume> resumeMap = new HashMap<>();
        resumes.forEach(resume -> resumeMap.put(resume.getId(), resume));
        Map<Long, JD> jdMap = new HashMap<>();
        jds.forEach(jd -> jdMap.put(jd.getId(), jd));
        // 将之前查询到的所有ResumeAnalysis转换为ResumeAnalysisVO
        for (ResumeAnalysis analysis : analysisList) {
            ResumeAnalysisVO resumeAnalysisVO = new ResumeAnalysisVO();
            // 将analysis中的属性复制到VO对象中。
            // 需要注意：analysisResult、retrievedResumes和retrievedJds这些字段不复制，列表中不必传递，后续具体查询某个记录的时候再传递
            BeanUtil.copyProperties(analysis, resumeAnalysisVO, "retrievedResumes", "retrievedJds", "analysisResult");
            // 将ResumeAnalysis中的String类型的retrievedResumes和retrievedJds字段转换为List<Map<String, Object>>类型
            /*
            List<Map<String, Object>> retrievedResumes = JSONUtil.toList(analysis.getRetrievedResumes(), Map.class)
                    .stream().map(map -> {
                        // 将list中的Map转为Map<String, Object>
                        Map<String, Object> newMap = new HashMap<>();
                        map.forEach((k, v) -> newMap.put(k.toString(), v));
                        return newMap;
            }).collect(Collectors.toList());
            List<Map<String, Object>> retrievedJds = JSONUtil.toList(analysis.getRetrievedJds(), Map.class)
                    .stream().map(map -> {
                        // 将list中的Map转为Map<String, Object>
                        Map<String, Object> newMap = new HashMap<>();
                        map.forEach((k, v) -> newMap.put(k.toString(), v));
                        return newMap;
                    }).collect(Collectors.toList());
            // 将转换后的结果设置到VO对象中
            resumeAnalysisVO.setRetrievedResumes(retrievedResumes);
            resumeAnalysisVO.setRetrievedJds(retrievedJds);
            */
            // 获取该分析记录中对应的简历和JD
            Resume resume = resumeMap.get(analysis.getResumeId());
            // 获取简历原始文件名，保存到VO中
            if (resume != null) {
                String name = getOriginalFileName(resume.getFilePath());
                resumeAnalysisVO.setResumeName(name);
            }
            BeanUtil.copyProperties(resume, resumeAnalysisVO);  // 将resume中的属性复制到VO对象中

            JD jd = jdMap.get(analysis.getJdID());
            // 获取JD原始文件名，保存到VO中
            if (jd != null) {
                String name = "";
                if (jd.getFilePath().isEmpty()){
                    name = jd.getTitle();
                } else {
                    name = getOriginalFileName(jd.getFilePath());
                }
                resumeAnalysisVO.setJdName(name);
            }
            BeanUtil.copyProperties(jd, resumeAnalysisVO);  // 将jd中的属性复制到VO对象中
            // 最后手动设置一些参数
            resumeAnalysisVO.setId(analysis.getId());
            resumeAnalysisVO.setUserId(analysis.getUserId());
            resumeAnalysisVO.setCreateTime(analysis.getCreateTime());
            resumeAnalysisVOList.add(resumeAnalysisVO);
        }
        log.info("Successfully converted ResumeAnalysis list to ResumeAnalysisVO list.");
        return resumeAnalysisVOList;
    }

    /**
     * 获取指定ID的简历分析记录在数据库中的全部信息
     * 先尝试从Redis缓存中获取简历分析记录信息；如果缓存不存在，则尝试从数据库中获取简历分析记录信息
     * @param id 简历分析记录ID
     * @return 结果对象，包含简历分析记录，类型为ResumeAnalysis
     */
    @Override
    public Result getResumeAnalysisById(Long id) {
        // 获取指定ID的简历分析记录
        // 1. 首先构造简历分析记录id在Redis中的缓存key，然后尝试从Redis中获取缓存的ResumeAnalysis对象
        String redisKey = RESUME_ANALYSIS_KEY + id;
        String resumeAnalysisJSON = stringRedisTemplate.opsForValue().get(redisKey);
        ResumeAnalysis resumeAnalysis;
        if (resumeAnalysisJSON != null && !resumeAnalysisJSON.isEmpty()) {
            // 2. 如果Redis中存在该缓存，则直接获取缓存的ResumeAnalysis对象
            log.info("Found resume analysis record in Redis cache with key {}.", redisKey);
            resumeAnalysis = JSONUtil.toBean(resumeAnalysisJSON, ResumeAnalysis.class);
        }
        else if (resumeAnalysisJSON != null) {
            // 3. 如果Redis中存在该缓存但值为空字符串，则说明该记录不存在，命中了空缓存，直接返回失败结果
            log.info("Resume analysis record not found in Redis cache with key: {} (NULL cache hit).", redisKey);
            // 刷新空缓存的过期时间
            stringRedisTemplate.expire(redisKey, COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("Resume analysis record not found.");
        }
        // 4. 如果Redis中不存在该缓存，则查询数据库获取ResumeAnalysis对象
        // 这可能涉及到缓存的重构，为了避免缓存雪崩和缓存击穿，这里使用加锁的方式，保证只有一个线程去重构缓存
        // 4.1. 尝试获取Redisson的分布式锁
        String lockKey = RESUME_ANALYSIS_LOCK_KEY + id;
        RLock lock = redissonClient.getLock(lockKey);
        try {
            // 尝试获取分布式锁，设置等待时间、锁的持有时间以及锁的释放时间
            boolean isLockAcquired = lock.tryLock(RESUME_ANALYSIS_LOCK_WAIT_TIME, RESUME_ANALYSIS_LOCK_TTL, RESUME_ANALYSIS_LOCK_TTL_UNIT);
            if (!isLockAcquired) {
                // 如果获取失败，则说明有其他线程正在处理该请求，直接返回未找到结果
                log.info("Failed to acquire lock for resume analysis record with lock key {}.", lockKey);
                return Result.fail("Timeout to get resume analysis record! Please try again later.");
            }
            log.info("Lock acquired for resume analysis record with lock key {}. Double checking cache now.", lockKey);
            // 4.2. 再次检查该缓存是否已经存在
            resumeAnalysisJSON = stringRedisTemplate.opsForValue().get(redisKey);
            if (resumeAnalysisJSON != null && !resumeAnalysisJSON.isEmpty()) {
                // 4.2.1. 如果缓存存在，则直接获取缓存的ResumeAnalysis对象
                log.info("Found resume analysis record in Redis cache with key: {} (cache hit after lock acquisition).", redisKey);
                resumeAnalysis = JSONUtil.toBean(resumeAnalysisJSON, ResumeAnalysis.class);
            }
            else if (resumeAnalysisJSON != null) {
                // 4.2.2. 如果缓存存在但值为空字符串，则说明该记录不存在，命中了空缓存，直接返回失败结果
                log.info("Resume analysis record not found in Redis cache with key: {} (NULL cache hit).", redisKey);
                // 刷新空缓存的过期时间
                stringRedisTemplate.expire(redisKey, COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
                return Result.fail("Resume analysis record not found.");
            }
            else {
                // 4.3. 如果缓存不存在，则查询数据库获取ResumeAnalysis对象
                resumeAnalysis = lambdaQuery()
                        .eq(ResumeAnalysis::getId, id)
                        .one();
                if (resumeAnalysis == null) {
                    // 5. 如果数据库中也不存在该记录，则返回失败结果
                    log.info("Resume analysis record not found in database with ID {}.", id);
                    // 为防止缓存穿透，写入空缓存到Redis，并设置较短的过期时间
                    stringRedisTemplate.opsForValue().set(redisKey, "", COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
                    return Result.fail("Resume analysis record not found.");
                }
                log.info("Successfully get resume analysis record with ID {}.", id);
                // 6. 将resumeAnalysis对象缓存到Redis中，并设置适当的过期时间
                String resumeAnalysisToCache = JSONUtil.toJsonStr(resumeAnalysis);
                stringRedisTemplate.opsForValue().set(redisKey, resumeAnalysisToCache, RESUME_ANALYSIS_TTL, RESUME_ANALYSIS_TTL_UNIT);
            }
        }
        catch (Exception e) {
            log.error("Error getting resume analysis record with ID {}: {}", id, e.getMessage());
            return Result.fail("Error getting resume analysis record.");
        }
        finally {
            // 7. 释放分布式锁。只有当前线程持有该锁时，才释放该锁
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
        return Result.success("Resume analysis record found successfully.", resumeAnalysis);
    }

    /**
     * 获取指定ID且属于指定用户的简历分析记录在数据库中的全部信息
     * @param id 简历分析记录ID
     * @param userId 用户ID
     * @return 结果对象，包含简历分析记录，类型为ResumeAnalysis
     */
    @Override
    public Result getResumeAnalysisById_UserId(Long id, Long userId) {
        // 获取当前用户的指定ID的简历分析记录
        // 1. 首先构造简历分析记录id在Redis中的缓存key，然后尝试从Redis中获取缓存的ResumeAnalysis对象
        String redisKey = RESUME_ANALYSIS_KEY + id;
        String resumeAnalysisJSON = stringRedisTemplate.opsForValue().get(redisKey);
        ResumeAnalysis resumeAnalysis;
        if (resumeAnalysisJSON != null && !resumeAnalysisJSON.isEmpty()) {
            // 2. 如果Redis中存在该缓存，判断该缓存的ResumeAnalysis对象的userId是否与传入的userId匹配
            resumeAnalysis = JSONUtil.toBean(resumeAnalysisJSON, ResumeAnalysis.class);
            if (!resumeAnalysis.getUserId().equals(userId)) {
                log.info("Resume analysis record with ID {} does not belong to User ID {}.", id, userId);
                return Result.fail("Resume analysis record not found.");
            }
            log.info("Found resume analysis record in Redis cache with key {}.", redisKey);
        }
        else if (resumeAnalysisJSON != null) {
            // 3. 如果Redis中存在该缓存但值为空字符串，则说明该记录不存在，命中了空缓存，直接返回失败结果
            log.info("Resume analysis record not found in Redis cache with key: {} (NULL cache hit).", redisKey);
            // 刷新空缓存的过期时间
            stringRedisTemplate.expire(redisKey, COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("Resume analysis record not found.");
        }
        else {
            // 4. 如果Redis中不存在该缓存，则查询数据库获取ResumeAnalysis对象
            resumeAnalysis = lambdaQuery()
                    .eq(ResumeAnalysis::getId, id)
                    .eq(ResumeAnalysis::getUserId, userId)
                    .one();
        }
        if (resumeAnalysis == null) {
            // 5. 如果数据库中也不存在该记录，则返回失败结果
            log.info("Resume analysis record not found in database with ID {}, userId {}.", id, userId);
            // 为防止缓存穿透，写入空缓存到Redis，并设置较短的过期时间
            stringRedisTemplate.opsForValue().set(redisKey, "", COMMON_NULL_TTL, COMMON_NULL_TTL_UNIT);
            return Result.fail("Resume analysis record not found.");
        }
        log.info("Successfully get resume analysis record with ID {}, userId {}.", id, userId);
        // 4. 将resumeAnalysis对象缓存到Redis中，并设置适当的过期时间
        String resumeAnalysisToCache = JSONUtil.toJsonStr(resumeAnalysis);
        stringRedisTemplate.opsForValue().set(redisKey, resumeAnalysisToCache, RESUME_ANALYSIS_TTL, RESUME_ANALYSIS_TTL_UNIT);
        return Result.success("Successfully get resume analysis record with ID: " + id + ".", resumeAnalysis);
    }

    /**
     * 获取指定ID的简历分析记录的展示给前端的全部信息
     * @param id 简历分析记录ID
     * @return 结果对象，包含简历分析记录，类型为ResumeAnalysisVO
     */
    @Override
    public Result getResumeAnalysisVOById(Long id) {
        // 1. 根据id获取ResumeAnalysis对象
        // 注意：这里暂且只支持获取当前登录用户的简历分析记录
        Result resumeAnalysisResult = getResumeAnalysisById_UserId(id, UserThreadLocal.get());
        if (resumeAnalysisResult.getData() == null) {
            return Result.fail("Resume analysis record not found.");
        }
        ResumeAnalysis resumeAnalysis = (ResumeAnalysis) resumeAnalysisResult.getData();
        // 2. 将查询得到的ResumeAnalysis对象转换为ResumeAnalysisVO对象
        log.info("Trying converting it to ResumeAnalysisVO...");
        ResumeAnalysisVO resumeAnalysisVO = new ResumeAnalysisVO();
        BeanUtil.copyProperties(resumeAnalysis, resumeAnalysisVO, "retrievedResumes", "retrievedJds");    // 将resumeAnalysis中的属性复制到VO对象中
        // 转换retrievedResumes和retrievedJds字段，由String转为List<Map<String, Object>>
        List<Map<String, Object>> retrievedResumes = JSONUtil.toList(resumeAnalysis.getRetrievedResumes(), Map.class)
                .stream().map(map -> {
                    // 将list中的Map转为Map<String, Object>
                    Map<String, Object> newMap = new HashMap<>();
                    map.forEach((k, v) -> newMap.put(k.toString(), v));
                    return newMap;
                }).collect(Collectors.toList());
        List<Map<String, Object>> retrievedJds = JSONUtil.toList(resumeAnalysis.getRetrievedJds(), Map.class)
                .stream().map(map -> {
                    // 将list中的Map转为Map<String, Object>
                    Map<String, Object> newMap = new HashMap<>();
                    map.forEach((k, v) -> newMap.put(k.toString(), v));
                    return newMap;
                }).collect(Collectors.toList());
        // 将转换后的结果设置到VO对象中
        resumeAnalysisVO.setRetrievedResumes(retrievedResumes);
        resumeAnalysisVO.setRetrievedJds(retrievedJds);
        // 获取该分析记录中对应的简历和JD
        Result resumeResult = resumeService.getResumeDTOById(resumeAnalysis.getResumeId());
        ResumeDTO resumeDTO = (ResumeDTO) resumeResult.getData();
        // 获取简历原始文件名，保存到VO中
        if (resumeDTO != null) {
            resumeAnalysisVO.setResumeName(resumeDTO.getName());
        } else {
            log.info("Resume with ID {} not found.", resumeAnalysis.getResumeId());
        }
        BeanUtil.copyProperties(resumeDTO, resumeAnalysisVO);  // 将resumeDTO中的属性复制到VO对象中
        Result jdResult = jdService.getJDDTOById(resumeAnalysis.getJdID());
        JDDTO jdDTO = (JDDTO) jdResult.getData();
        // 获取JD原始文件名，保存到VO中
        if (jdDTO != null) {
            resumeAnalysisVO.setJdName(jdDTO.getName());
        } else {
            log.info("JD with ID {} not found.", resumeAnalysis.getJdID());
        }
        BeanUtil.copyProperties(jdDTO, resumeAnalysisVO);  // 将jdDTO中的属性复制到VO对象中
        // 最后手动设置一些参数
        resumeAnalysisVO.setId(resumeAnalysis.getId());
        resumeAnalysisVO.setUserId(resumeAnalysis.getUserId());
        resumeAnalysisVO.setCreateTime(resumeAnalysis.getCreateTime());
        log.info("Successfully converted ResumeAnalysis to ResumeAnalysisVO.");
        return Result.success("Successfully get resume analysis record with ID: " + id + ".", resumeAnalysisVO);
    }

    /**
     * 删除当前登录用户的指定ID的简历分析记录
     * @param id 简历分析记录ID
     * @return 结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result deleteResumeAnalysisById(Long id) {
        // 删除当前用户的指定ID的简历分析记录
        // 1. 首先要获取当前登录的用户ID
        Long userId = UserThreadLocal.get();
        // 2. 删除当前用户的指定ID的简历分析记录
        boolean removed = lambdaUpdate()
                .eq(ResumeAnalysis::getUserId, userId)
                .eq(ResumeAnalysis::getId, id)
                .remove();
        if (!removed) {
            log.error("Failed to delete resume analysis record with ID {} for User ID {}.", id, userId);
            return Result.fail("Failed to delete resume analysis record.");
        }
        // 3. 构建该id对应的简历分析记录在Redis中的缓存key，然后尝试删除该缓存
        try {
            String redisKey = RESUME_ANALYSIS_KEY + id;
            if (Boolean.TRUE.equals(stringRedisTemplate.hasKey(redisKey))) {
                log.info("Deleting resume analysis cache from Redis with key: {}", redisKey);
                stringRedisTemplate.delete(redisKey);
                log.info("Deleted resume analysis record cache in Redis with key {}.", redisKey);
            }
        } catch (Exception e) {
            log.error("Failed to delete resume analysis record cache in Redis for ID {}. Error: {}", id, e.getMessage());
            throw new RuntimeException("Failed to delete resume analysis record cache in Redis.", e);
        }
        log.info("Deleted resume analysis record successfully with ID {} for User ID {}.", id, userId);
        return Result.success("Successfully deleted resume analysis record.");
    }

    /**
     * 发送简历与JD差异分析请求消息到RabbitMQ
     * @param resumeId 简历ID
     * @param jdId JD ID
     * @return 结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result generateResumeJdDiffer(Long resumeId, Long jdId) {
        // 该方法需要传递一个简历分析的消息给RabbitMQ，然后由python端进行分析处理
        // 发送的消息体的内容为ResumeAnalysis对象，由Jackson2JsonMessageConverter自动序列化为JSON字符串

        // 1. 根据传入的resumeId和jdId查询对应的简历和JD的内容
        // 获取resumeId对应的Resume对象
        Result resumeResult = resumeService.getResumeById(resumeId);
        if (resumeResult.getData() == null) {
            log.error("Resume with ID {} not found.", resumeId);
            return Result.fail("Resume not found.");
        }
        Resume resume = (Resume) resumeResult.getData();
        // 获取jdId对应的JD对象
        Result jdResult = jdService.getJDById(jdId);
        if (jdResult.getData() == null) {
            log.error("JD with ID {} not found.", jdId);
            return Result.fail("JD not found.");
        }
        JD jd = (JD) jdResult.getData();
        // 2. 构造ResumeAnalysisDTO对象
        ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
        BeanUtil.copyProperties(resume, resumeAnalysisDTO);
        BeanUtil.copyProperties(jd, resumeAnalysisDTO);
        // 手动设置部分字段
        resumeAnalysisDTO.setUserId(UserThreadLocal.get());
        resumeAnalysisDTO.setResumeId(resumeId);    // 由于查询得到的resume对象中只有ID没有resumeId字段，需手动设置
        resumeAnalysisDTO.setJdID(jdId);        // 由于查询得到的jd对象中只有ID没有jdID字段，需手动设置
        resumeAnalysisDTO.setResumeFilePath(resume.getFilePath()); // 同上，由于字段名不同而需手动设置简历文件路径
        resumeAnalysisDTO.setJdFilePath(jd.getFilePath());      // 同上，由于字段名不同而需手动设置JD文件路径
        resumeAnalysisDTO.setRequestType(REQUEST_RESUME_JD_DIFFER); // 设置请求类型为简历JD差异分析
        resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
        resumeAnalysisDTO.setAnalysisResult(""); // 初始为空，等待分析结果返回后更新
        resumeAnalysisDTO.setRetrievedResumes(Collections.emptyList());
        resumeAnalysisDTO.setRetrievedJds(Collections.emptyList());
        resumeAnalysisDTO.setCreateTime(LocalDateTime.now());
        // 生成好resumeAnalysisDTO这个消息体后，调用处理函数进行处理（包括写入数据库，发送消息给MQ）
        HandleAnalyseRequest(resumeAnalysisDTO, ANALYSE_EXCHANGE_NAME, ANALYSE_REQUEST_ROUTING_KEY);
        return Result.success("User " + UserThreadLocal.get() +" sent resume-jd difference analysis request successfully.", resumeAnalysisDTO);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void HandleAnalyseRequest(ResumeAnalysisDTO resumeAnalysisDTO, String ExchangeName, String RoutingKey) {
        // 将resumeAnalysisDTO对象转化为ResumeAnalysis对象，保存初始状态到数据库中
        try {
            log.info("Trying saving initial resume analysis record to database for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}...",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId(), resumeAnalysisDTO.getJdID(), resumeAnalysisDTO.getRequestType());
            ResumeAnalysis resumeAnalysis = new ResumeAnalysis();
            BeanUtil.copyProperties(resumeAnalysisDTO, resumeAnalysis, "retrievedResumes", "retrievedJds");
            resumeAnalysis.setRetrievedResumes(JSONUtil.toJsonStr(resumeAnalysisDTO.getRetrievedResumes()));
            resumeAnalysis.setRetrievedJds(JSONUtil.toJsonStr(resumeAnalysisDTO.getRetrievedJds()));
            save(resumeAnalysis);   // 将resumeAnalysis对象保存到数据库中
            resumeAnalysisDTO.setId(resumeAnalysis.getId()); // 将生成的主键ID设置回DTO对象中
            log.info("Saved initial resume analysis record to database for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId(), resumeAnalysisDTO.getJdID(), resumeAnalysisDTO.getRequestType());
        } catch (Exception e) {
            log.error("Failed to save initial resume analysis record to database for User ID: {}, Resume ID: {}, Request Type: {}, JD ID: {}. Error: {}",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId(), resumeAnalysisDTO.getJdID(), resumeAnalysisDTO.getRequestType(), e.getMessage());
            throw new DbException("Failed to save initial resume analysis record to database.", e);
        }
        try {
            // 手动转换文件路径为wsl可访问路径（因为python程序部署在wsl内）
            String wsl_resumePath = FileTool.parsePath(resumeAnalysisDTO.getResumeFilePath());
            String wsl_jdPath = FileTool.parsePath(resumeAnalysisDTO.getJdFilePath());
            resumeAnalysisDTO.setResumeFilePath(wsl_resumePath);
            resumeAnalysisDTO.setJdFilePath(wsl_jdPath);
            log.info("Prepared MQ request for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId(), resumeAnalysisDTO.getJdID(), resumeAnalysisDTO.getRequestType());
            // 3. 发送消息到RabbitMQ的指定交换机和路由键
            rabbitTemplate.convertAndSend(
                    ExchangeName,
                    RoutingKey,
                    resumeAnalysisDTO
            );
            log.info("Sent request message to RabbitMQ successfully for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}.",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId(), resumeAnalysisDTO.getJdID(), resumeAnalysisDTO.getRequestType());
        } catch (Exception e) {
            log.error("Failed to send request message to RabbitMQ for User ID: {}, Resume ID: {}, JD ID: {}, Request Type: {}, Error: {}",
                    resumeAnalysisDTO.getUserId(), resumeAnalysisDTO.getResumeId(), resumeAnalysisDTO.getJdID(), resumeAnalysisDTO.getRequestType(), e.getMessage());
            throw new RuntimeException("Failed to send request message to RabbitMQ.", e);
        }
    }

    /**
     * 发送简历分析建议请求消息到RabbitMQ
     * @param resumeId 简历ID
     * @param jdId JD ID
     * @return 结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result generateResumeAdvice(Long resumeId, Long jdId) {
        // 该方法需要传递一个简历分析的消息给RabbitMQ，然后由python端进行分析处理
        // 发送的消息体的内容为ResumeAnalysis对象，由Jackson2JsonMessageConverter自动序列化为JSON字符串

        // 1. 根据传入的resumeId和jdId查询对应的简历和JD的内容
        // 获取resumeId对应的Resume对象
        Result resumeResult = resumeService.getResumeById(resumeId);
        if (resumeResult.getData() == null) {
            log.error("Resume with ID {} not found.", resumeId);
            return Result.fail("Resume not found.");
        }
        Resume resume = (Resume) resumeResult.getData();
        // 获取jdId对应的JD对象
        Result jdResult = jdService.getJDById(jdId);
        if (jdResult.getData() == null) {
            log.error("JD with ID {} not found.", jdId);
            return Result.fail("JD not found.");
        }
        JD jd = (JD) jdResult.getData();
        // 2. 构造ResumeAnalysisDTO对象
        ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
        BeanUtil.copyProperties(resume, resumeAnalysisDTO);
        BeanUtil.copyProperties(jd, resumeAnalysisDTO);
        // 手动设置部分字段
        resumeAnalysisDTO.setUserId(UserThreadLocal.get());
        resumeAnalysisDTO.setResumeId(resumeId);    // 由于查询得到的resume对象中只有ID没有resumeId字段，需手动设置
        resumeAnalysisDTO.setJdID(jdId);        // 由于查询得到的jd对象中只有ID没有jdID字段，需手动设置
        resumeAnalysisDTO.setResumeFilePath(resume.getFilePath()); // 同上，由于字段名不同而需手动设置简历文件路径
        resumeAnalysisDTO.setJdFilePath(jd.getFilePath());      // 同上，由于字段名不同而需手动设置JD文件路径
        resumeAnalysisDTO.setRequestType(REQUEST_RESUME_ADVISE); // 设置请求类型为简历分析建议
        resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
        resumeAnalysisDTO.setAnalysisResult(""); // 初始为空，等待分析结果返回后更新
        resumeAnalysisDTO.setRetrievedResumes(Collections.emptyList());
        resumeAnalysisDTO.setRetrievedJds(Collections.emptyList());
        resumeAnalysisDTO.setCreateTime(LocalDateTime.now());
        // 生成好resumeAnalysisDTO这个消息体后，调用处理函数进行处理（包括写入数据库，发送消息给MQ）
        HandleAnalyseRequest(resumeAnalysisDTO, ANALYSE_EXCHANGE_NAME , ANALYSE_REQUEST_ROUTING_KEY);
        return Result.success("User " + UserThreadLocal.get() + " sent resume advice request successfully.", resumeAnalysisDTO);
    }

    /**
     * 发送JD匹配请求消息到RabbitMQ
     * @param resumeId 简历ID
     * @return 结果对象
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result generateJDMatch(Long resumeId) {
        // 构造JD匹配的请求消息，发送给RabbitMQ
        // 1. 首先根据传入的resumeId中查询对应的简历信息
        Result resumeResult = resumeService.getResumeById(resumeId);
        if (resumeResult.getData() == null) {
            log.error("Resume with ID {} not found.", resumeId);
            return Result.fail("Resume not found.");
        }
        Resume resume = (Resume) resumeResult.getData();
        // 2. 构造ResumeAnalysisDTO对象
        ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
        BeanUtil.copyProperties(resume, resumeAnalysisDTO);
        // 手动设置部分字段
        resumeAnalysisDTO.setUserId(UserThreadLocal.get());
        resumeAnalysisDTO.setResumeId(resumeId);    // 由于查询得到的resume对象中只有ID没有resumeId字段，需手动设置
        resumeAnalysisDTO.setResumeFilePath(resume.getFilePath()); // 同上，由于字段名不同而需手动设置简历文件路径
        resumeAnalysisDTO.setRequestType(REQUEST_JD_MATCH); // 设置请求类型为JD匹配
        resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
        resumeAnalysisDTO.setAnalysisResult(""); // 初始为空，等待分析结果返回后更新
        resumeAnalysisDTO.setRetrievedResumes(Collections.emptyList());
        resumeAnalysisDTO.setRetrievedJds(Collections.emptyList());
        resumeAnalysisDTO.setCreateTime(LocalDateTime.now());
        // 生成好resumeAnalysisDTO这个消息体后，调用处理函数进行处理（包括写入数据库，发送消息给MQ）
        HandleAnalyseRequest(resumeAnalysisDTO, MATCH_EXCHANGE_NAME, JD_MATCH_REQUEST_ROUTING_KEY);
        return Result.success("User " + UserThreadLocal.get() + " sent JD match request successfully.", resumeAnalysisDTO);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result generateResumeMatch(Long jdId) {
        // 构造简历匹配的请求消息，发送给RabbitMQ
        // 1. 首先从数据库中查询JD信息
        Result jdResult = jdService.getJDById(jdId);
        if (jdResult.getData() == null) {
            log.error("JD with ID {} not found.", jdId);
            return Result.fail("JD not found.");
        }
        JD jd = (JD) jdResult.getData();
        // 2. 构造ResumeAnalysisDTO对象
        ResumeAnalysisDTO resumeAnalysisDTO = new ResumeAnalysisDTO();
        BeanUtil.copyProperties(jd, resumeAnalysisDTO);
        // 手动设置部分字段
        resumeAnalysisDTO.setUserId(UserThreadLocal.get());
        resumeAnalysisDTO.setJdID(jdId);    // 由于查询得到的JD对象中只有ID没有jdId字段，需手动设置
        resumeAnalysisDTO.setJdFilePath(jd.getFilePath()); // 同上，由于字段名不同而需手动设置简历文件路径
        resumeAnalysisDTO.setRequestType(REQUEST_RESUME_MATCH); // 设置请求类型为简历匹配
        resumeAnalysisDTO.setStatus(RESUME_ANALYSIS_WAITING_STATUS);    // 设置状态为等待分析
        resumeAnalysisDTO.setAnalysisResult(""); // 初始为空，等待分析结果返回后更新
        resumeAnalysisDTO.setRetrievedResumes(Collections.emptyList());
        resumeAnalysisDTO.setRetrievedJds(Collections.emptyList());
        resumeAnalysisDTO.setCreateTime(LocalDateTime.now());
        // 生成好resumeAnalysisDTO这个消息体后，调用处理函数进行处理（包括写入数据库，发送消息给MQ）
        HandleAnalyseRequest(resumeAnalysisDTO, MATCH_EXCHANGE_NAME, RESUME_MATCH_REQUEST_ROUTING_KEY);
        return Result.success("User " + UserThreadLocal.get() + " sent Resume match request successfully.", resumeAnalysisDTO);
    }
}
