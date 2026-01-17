package org.kira.resumesystem.service.serviceImpl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.entity.po.User;
import org.kira.resumesystem.mapper.UserMapper;
import org.kira.resumesystem.service.IUserService;
import org.kira.resumesystem.utils.JwtTool;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import static org.kira.resumesystem.utils.RedisConstants.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements IUserService {
    private final StringRedisTemplate stringRedisTemplate;
    private final JwtTool jwtTool;

    /**
     * 用户登录功能
     * @param userDTO 用户传入的登录信息
     * @return 登录结果
     */
    @Override
    public Result login(UserDTO userDTO) {
        String username = userDTO.getUsername();
        String password = userDTO.getPassword();
        Integer role = userDTO.getRole();
        log.info("用户尝试登录，用户名：{}", username);
        // 首先查询Redis，看是否有该用户登录的缓存信息
        String redisKey = USER_LOGIN_KEY + username;
        String redisCdKey = USER_LOGIN_HASH_CD + username;
        // 首先检查用户是否频繁尝试登录
        // 检查redisCdKey，防止用户短时间内多次尝试登录
        Boolean hasCdKey = stringRedisTemplate.hasKey(redisCdKey);
        if (hasCdKey != null && hasCdKey) {
            log.info("用户 {} 登录失败，操作过于频繁!", username);
            return Result.fail("操作过于频繁，请稍后再试");
        }
        // 然后再检查Redis中是否有该用户的登录缓存
        Map<Object, Object> userLoginMap = stringRedisTemplate.opsForHash().entries(redisKey);
        if (!userLoginMap.isEmpty()) {
            String cachePassword = userLoginMap.get(USER_LOGIN_HASH_PASSWORD).toString();
            if(cachePassword.isEmpty()) {
                // 缓存中存的是空值，说明用户名不存在。顺便刷新空缓存的过期时间，防止缓存穿透
                stringRedisTemplate.expire(redisKey, USER_LOGIN_TTL, USER_LOGIN_TTL_UNIT);
                log.info("用户 {} 登录失败，用户名不存在!", username);
                return Result.fail("用户名或密码或身份错误");
            }
            // Redis中有缓存，验证密码是否匹配
            if (cachePassword.equals(password)) {
                // 密码匹配。再判断用户的角色是否匹配
                Integer cachedRole = Integer.parseInt(userLoginMap.get(USER_LOGIN_HASH_ROLE).toString());
                if (!role.equals(cachedRole)){
                    // 角色不匹配，登录失败。设置登录冷却时间，防止用户频繁尝试错误角色
                    stringRedisTemplate.opsForValue().set(redisCdKey, "", USER_LOGIN_CD_TTL, USER_LOGIN_CD_TTL_UNIT);
                    log.info("用户 {} 登录失败，用户角色不匹配!", username);
                    return Result.fail("用户名或密码或身份错误");
                }
                // 登录成功，生成新的jwt token返回给前端保存
                Long userId = Long.valueOf(userLoginMap.get(USER_LOGIN_HASH_ID).toString());
                User user = new User().setId(userId).setUsername(username).setRole(cachedRole);
                String newToken = jwtTool.createToken(user);
                UserDTO responseDTO = new UserDTO()
                        .setUsername(username)
                        .setToken(newToken)
                        .setRole(role);
                log.info("用户 {} 登录成功!", username);
                return Result.success("登录成功", responseDTO);
            } else {
                // 密码不匹配，登录失败。设置登录冷却时间，防止用户频繁尝试错误密码
                stringRedisTemplate.opsForValue().set(redisCdKey, "", USER_LOGIN_CD_TTL, USER_LOGIN_CD_TTL_UNIT);
                log.info("用户 {} 登录失败，密码错误!", username);
                return Result.fail("用户名或密码或身份错误");
            }
        }
        // 缓存失效，查询数据库验证用户名是否匹配密码
        User user = lambdaQuery()
                .eq(User::getUsername, userDTO.getUsername())
                .one();
        // 用户名不存在或者密码错误或者角色不匹配，则登录失败
        // 用户名不存在的情况
        if (user == null) {
            // 为防止缓存穿透，不存在的用户也缓存一个空值，设置较短的过期时间
            stringRedisTemplate.opsForHash().put(redisKey, USER_LOGIN_HASH_PASSWORD, "");
            stringRedisTemplate.expire(redisKey, USER_LOGIN_TTL, USER_LOGIN_TTL_UNIT);
            log.info("用户 {} 登录失败，用户名错误!", username);
            return Result.fail("用户名或密码或身份错误");
        }
        // 密码错误的情况
        else if (!password.equals(user.getPassword())) {
            // 密码错误的情况设置一个很短的冷却时间，防止用户频繁尝试错误密码
            stringRedisTemplate.opsForValue().set(redisCdKey, "", USER_LOGIN_CD_TTL, USER_LOGIN_CD_TTL_UNIT);
            log.info("用户 {} 登录失败，密码错误!", username);
            return Result.fail("用户名或密码或身份错误");
        }
        // 角色不匹配的情况
        else if (!role.equals(user.getRole())) {
            // 角色错误的情况设置一个很短的冷却时间，防止用户频繁尝试错误角色
            stringRedisTemplate.opsForValue().set(redisCdKey, "", USER_LOGIN_CD_TTL, USER_LOGIN_CD_TTL_UNIT);
            log.info("用户 {} 登录失败，身份错误!", username);
            return Result.fail("用户名或密码或身份错误");
        }
        // 登录成功，将用户信息缓存到Redis
        // 用户信息缓存时间较短，是因为通常登录成功后的用户带有正确的jwt，不需要再访问Redis验证登录状态
        // 不过为了防止特殊情况下jwt出现快速失效的情况，仍然在Redis中短时间缓存用户登录信息以备用户频繁登录请求
        Long userId = user.getId();
        Map<String, Object> userMap = new HashMap<>();
        userMap.put(USER_LOGIN_HASH_ID, userId.toString());
        userMap.put(USER_LOGIN_HASH_PASSWORD, user.getPassword());
        userMap.put(USER_LOGIN_HASH_ROLE, user.getRole().toString());
        stringRedisTemplate.opsForHash().putAll(redisKey, userMap);
        stringRedisTemplate.expire(redisKey, USER_LOGIN_TTL, USER_LOGIN_TTL_UNIT);
        // 生成新的jwt token，返回给前端保存
        String newToken = jwtTool.createToken(user);
        UserDTO responseDTO = new UserDTO()
                .setUsername(username)
                .setRole(role)
                .setToken(newToken);
        log.info("用户 {} 登录成功!", username);
        return Result.success("登录成功", responseDTO);
    }

    /**
     * 用户注册功能
     * @param userDTO 用户传入的注册信息
     * @return 注册结果
     */
    @Override
    public Result register(UserDTO userDTO) {
        // 先检查用户名是否已存在
        // 首先需要检查Redis缓存中是否存在该用户名，如果存在，则说明该用户名处于冷却时间，暂时禁止注册
        String cd_key = USER_REGISTER_CD_KEY + userDTO.getUsername();
        Boolean hasKey = stringRedisTemplate.hasKey(cd_key);
        if (hasKey != null && hasKey) {
            return Result.fail("操作过于频繁，请稍后再试");
        }
        // 查询数据库，检查用户名是否已存在
        Integer count = lambdaQuery().eq(User::getUsername, userDTO.getUsername()).count();
        if (count != null && count > 0) {
            // 用户名已存在。为防止用户频繁尝试注册重复用户名，设置一个短暂的冷却时间
            stringRedisTemplate.opsForValue().set(cd_key, "", USER_REGISTER_CD_TTL, USER_REGISTER_CD_TTL_UNIT);
            log.info("用户注册失败，用户名已存在：{}", userDTO.getUsername());
            return Result.fail("用户名已存在");
        }
        // 创建新用户，保存到数据库
        User newUser = new User()
                .setUsername(userDTO.getUsername())
                .setPassword(userDTO.getPassword())
                .setRole(userDTO.getRole())
                .setCreateTime(LocalDateTime.now())
                .setUpdateTime(LocalDateTime.now());
        boolean saved = save(newUser);
        // 数据库插入新用户信息失败
        if (!saved) {
            log.info("用户注册失败，数据库插入新用户信息失败，用户名：{}", userDTO.getUsername());
            return Result.fail("注册失败，请稍后重试");
        }
        // 将用户信息存入Redis
        String redisKey = USER_LOGIN_KEY + newUser.getUsername();
        Map<String, Object> userMap = new HashMap<>();
        userMap.put(USER_LOGIN_HASH_ID, newUser.getId().toString());
        userMap.put(USER_LOGIN_HASH_PASSWORD, newUser.getPassword());
        userMap.put(USER_LOGIN_HASH_ROLE, newUser.getRole().toString());
        stringRedisTemplate.opsForHash().putAll(redisKey, userMap);
        stringRedisTemplate.expire(redisKey, USER_LOGIN_TTL, USER_LOGIN_TTL_UNIT);
        // 生成登录的jwt token，返回给前端保存
        String token = jwtTool.createToken(newUser);
        UserDTO responseDTO = new UserDTO()
                .setUsername(userDTO.getUsername())
                .setToken(token)
                .setRole(userDTO.getRole());
        log.info("新用户注册成功，用户名：{}", userDTO.getUsername());
        return Result.success("注册成功", responseDTO);
    }
}
