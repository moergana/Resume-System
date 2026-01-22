package org.kira.resumesystem.service.serviceImpl;

import cn.hutool.core.util.RandomUtil;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kira.resumesystem.entity.dto.Result;
import org.kira.resumesystem.entity.dto.UserDTO;
import org.kira.resumesystem.entity.po.User;
import org.kira.resumesystem.mapper.UserMapper;
import org.kira.resumesystem.service.IUserService;
import org.kira.resumesystem.utils.JwtTool;
import org.kira.resumesystem.utils.UserThreadLocal;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static org.kira.resumesystem.utils.Constants.CANDIDATE_ROLE;
import static org.kira.resumesystem.utils.Constants.RECRUITER_ROLE;
import static org.kira.resumesystem.utils.RedisConstants.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements IUserService {
    private final StringRedisTemplate stringRedisTemplate;
    private final JwtTool jwtTool;
    private final PasswordEncoder passwordEncoder;

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
            if (passwordEncoder.matches(password, cachePassword)) {
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
                String email = userLoginMap.get(USER_LOGIN_HASH_EMAIL).toString();
                User user = new User().setId(userId).setUsername(username).setRole(cachedRole);
                String newToken = jwtTool.createToken(user);
                UserDTO responseDTO = new UserDTO()
                        .setId(userId)
                        .setUsername(username)
                        .setToken(newToken)
                        .setRole(role)
                        .setEmail(email);
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
        else if (!passwordEncoder.matches(password, user.getPassword())) {
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
        userMap.put(USER_LOGIN_HASH_EMAIL, user.getEmail());
        stringRedisTemplate.opsForHash().putAll(redisKey, userMap);
        stringRedisTemplate.expire(redisKey, USER_LOGIN_TTL, USER_LOGIN_TTL_UNIT);
        // 生成新的jwt token，返回给前端保存
        String newToken = jwtTool.createToken(user);
        UserDTO responseDTO = new UserDTO()
                .setId(userId)
                .setUsername(username)
                .setRole(role)
                .setToken(newToken)
                .setEmail(user.getEmail());
        log.info("用户 {} 登录成功!", username);
        return Result.success("登录成功", responseDTO);
    }
    /**
     * 发送注册的邮箱验证码功能
     * @param userDTO 用户传入的邮箱信息
     * @return 发送结果
     */
    @Override
    public Result sendRegisterEmailCode(UserDTO userDTO) {
        // 1. 判断邮箱是否为空
        if (userDTO.getEmail() == null || userDTO.getEmail().isEmpty()) {
            log.info("发送注册的邮箱验证码失败，邮箱为空");
            return Result.fail("邮箱不能为空");
        }
        // 2. 生成验证码并发送邮件（此处省略具体实现）
        String email = userDTO.getEmail();
        // 生成一个6位数字验证码
        String verificationCode = RandomUtil.randomNumbers(6);  // 这里本应该调用实际的验证码生成和发送逻辑
        // 3. 将验证码保存到Redis中，有效期为10分钟
        String redisKey = EMAIL_REGISTER_CODE_KEY + email;
        stringRedisTemplate.opsForValue().set(redisKey, verificationCode, EMAIL_CODE_TTL, EMAIL_CODE_TTL_UNIT);
        log.info("发送注册邮箱验证码成功，邮箱：{}，验证码：{}", email, verificationCode);
        return Result.success("验证码发送成功", null);
    }

    /**
     * 用户注册功能
     * @param userDTO 用户传入的注册信息
     * @return 注册结果
     */
    @Override
    public Result register(UserDTO userDTO) {
        // 先检查userDTO中的所需字段是否都存在
        if (userDTO.getUsername() == null || userDTO.getUsername().isEmpty()) {
            log.info("用户注册失败，用户名为空");
            return Result.fail("用户名不能为空");
        }
        if (userDTO.getPassword() == null || userDTO.getPassword().isEmpty()) {
            log.info("用户注册失败，密码为空");
            return Result.fail("密码不能为空");
        }
        if (userDTO.getRole() == null) {
            log.info("用户注册失败，角色为空");
            return Result.fail("角色不能为空");
        }
        if (!userDTO.getRole().equals(CANDIDATE_ROLE) && !userDTO.getRole().equals(RECRUITER_ROLE)) {
            log.info("用户注册失败，角色不合法");
            return Result.fail("角色不合法");
        }
        // 首先需要检查Redis缓存中是否存在该用户名，如果存在，则说明该用户名处于冷却时间，暂时禁止注册
        String cd_key = USER_REGISTER_CD_KEY + userDTO.getUsername();
        Boolean hasKey = stringRedisTemplate.hasKey(cd_key);
        if (hasKey != null && hasKey) {
            return Result.fail("操作过于频繁，请稍后再试");
        }
        // 查询数据库，检查用户名是否已存在
        Long count = lambdaQuery().eq(User::getUsername, userDTO.getUsername()).count();
        if (count != null && count > 0) {
            // 用户名已存在。为防止用户频繁尝试注册重复用户名，设置一个短暂的冷却时间
            stringRedisTemplate.opsForValue().set(cd_key, "", USER_REGISTER_CD_TTL, USER_REGISTER_CD_TTL_UNIT);
            log.info("用户注册失败，用户名已存在：{}", userDTO.getUsername());
            return Result.fail("用户名已存在");
        }
        // 创建新用户，保存到数据库
        // 密码需要加密后再保存
        String encodedPassword = passwordEncoder.encode(userDTO.getPassword());
        userDTO.setPassword(encodedPassword);
        // 构造User对象
        User newUser = new User()
                .setUsername(userDTO.getUsername())
                .setPassword(userDTO.getPassword())
                .setRole(userDTO.getRole())
                .setEmail(userDTO.getEmail())
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
        userMap.put(USER_LOGIN_HASH_EMAIL, newUser.getEmail());
        stringRedisTemplate.opsForHash().putAll(redisKey, userMap);
        stringRedisTemplate.expire(redisKey, USER_LOGIN_TTL, USER_LOGIN_TTL_UNIT);
        // 生成登录的jwt token，返回给前端保存
        String token = jwtTool.createToken(newUser);
        UserDTO responseDTO = new UserDTO()
                .setId(newUser.getId())
                .setUsername(userDTO.getUsername())
                .setToken(token)
                .setRole(userDTO.getRole())
                .setEmail(userDTO.getEmail());
        log.info("新用户注册成功，用户名：{}", userDTO.getUsername());
        return Result.success("注册成功", responseDTO);
    }

    /**
     * 发送重置密码的邮箱验证码功能
     * @param userDTO 用户传入的邮箱信息
     * @return 发送结果
     */
    @Override
    public Result sendResetPasswordEmailCode(UserDTO userDTO) {
        // 1. 判断邮箱是否为空
        if (userDTO.getEmail() == null || userDTO.getEmail().isEmpty()) {
            log.info("发送重置密码的邮箱验证码失败，邮箱为空");
            return Result.fail("邮箱不能为空");
        }
        // 2. 生成验证码并发送邮件（此处省略具体实现）
        String email = userDTO.getEmail();
        // 生成一个6位数字验证码
        String verificationCode = RandomUtil.randomNumbers(6);  // 这里本应该调用实际的验证码生成和发送逻辑
        // 3. 将验证码保存到Redis中，有效期为10分钟
        String redisKey = EMAIL_RESET_PASSWORD_CODE_KEY + email;
        stringRedisTemplate.opsForValue().set(redisKey, verificationCode, EMAIL_CODE_TTL, EMAIL_CODE_TTL_UNIT);
        log.info("发送邮箱验证码成功，邮箱：{}，验证码：{}", email, verificationCode);
        return Result.success("验证码发送成功", null);
    }

    /**
     * 重置密码功能。该方法调用前需要确保已经通过邮箱验证用户身份合法
     * @param userDTO 用户传入的重置密码信息
     * @return 重置结果
     */
    @Override
    @Transactional
    public Result resetPassword(UserDTO userDTO) {
        try {
            // 1. 判断邮箱和邮箱验证码是否不为空
            if (userDTO.getEmail() == null || userDTO.getEmail().isEmpty()) {
                log.info("重置密码失败，邮箱为空");
                return Result.fail("邮箱不能为空");
            }
            if (userDTO.getEmailCode() == null || userDTO.getEmailCode().isEmpty()) {
                log.info("重置密码失败，邮箱验证码为空");
                return Result.fail("邮箱验证码不能为空");
            }
            // 2. 从Redis中获取该邮箱对应的验证码，进行验证
            String redisKey = EMAIL_RESET_PASSWORD_CODE_KEY + userDTO.getEmail();
            String cachedCode = stringRedisTemplate.opsForValue().get(redisKey);
            if (cachedCode == null) {
                log.info("重置密码失败，邮箱验证码已过期，邮箱：{}", userDTO.getEmail());
                return Result.fail("邮箱验证码已过期");
            }
            if (!cachedCode.equals(userDTO.getEmailCode())) {
                log.info("重置密码失败，邮箱验证码错误，邮箱：{}", userDTO.getEmail());
                return Result.fail("邮箱验证码错误");
            }
            // 3. 根据邮箱查询用户
            User user = lambdaQuery()
                    .eq(User::getEmail, userDTO.getEmail())
                    .one();
            if (user == null) {
                log.info("重置密码失败，邮箱未注册，邮箱：{}", userDTO.getEmail());
                return Result.fail("邮箱未注册");
            }
            // 4. 更新用户密码。密码需要加密后再保存
            String encodedPassword = passwordEncoder.encode(userDTO.getPassword());
            user.setPassword(encodedPassword);
            boolean updated = updateById(user);
            if (!updated) {
                log.info("重置密码失败，数据库更新用户密码失败，邮箱：{}", userDTO.getEmail());
                return Result.fail("重置密码失败，请稍后重试");
            }
            // 5. 删除该用户在Redis中的登录缓存，避免失效的旧密码影响登录。用户重新登录后会缓存有效的新密码
            redisKey = USER_LOGIN_KEY + user.getUsername();
            stringRedisTemplate.delete(redisKey);
            log.info("用户密码重置成功，邮箱：{}", userDTO.getEmail());
            return Result.success("密码重置成功，请使用新密码登录");
        } catch (Exception e) {
            log.info("重置密码失败，发生异常：{}", e.getMessage());
            throw new RuntimeException(e);
        }
    }

    /**
     * 发送修改邮箱验证码功能
     * @param userDTO 用户传入的邮箱信息
     * @return 发送结果
     */
    @Override
    public Result sendModifyEmailCode(UserDTO userDTO) {
        // 1. 判断新邮箱是否为空
        if (userDTO.getEmail() == null || userDTO.getEmail().isEmpty()) {
            log.info("发送修改邮箱验证码失败，新邮箱为空");
            return Result.fail("新邮箱不能为空");
        }
        // 2. 生成验证码并发送邮件（此处省略具体实现）
        String email = userDTO.getEmail();
        // 生成一个6位数字验证码
        String verificationCode = RandomUtil.randomNumbers(6); // 这里应该调用实际的验证码生成和发送逻辑
        // 3. 将验证码保存到Redis中，有效期为10分钟
        String redisKey = EMAIL_MODIFY_EMAIL_CODE_KEY + email;
        stringRedisTemplate.opsForValue().set(redisKey, verificationCode, EMAIL_CODE_TTL, EMAIL_CODE_TTL_UNIT);
        log.info("发送修改邮箱验证码成功，新邮箱：{}，验证码：{}", email, verificationCode);
        return Result.success("验证码发送成功", null);
    }

    /**
     * 修改邮箱功能
     * @param userDTO 用户传入的修改邮箱信息
     * @return 修改结果
     */
    @Override
    public Result modifyEmail(UserDTO userDTO) {
        // 1. 判断新邮箱和邮箱验证码是否不为空
        if (userDTO.getEmail() == null || userDTO.getEmail().isEmpty()) {
            log.info("修改邮箱失败，新邮箱为空");
            return Result.fail("新邮箱不能为空");
        }
        if (userDTO.getEmailCode() == null || userDTO.getEmailCode().isEmpty()) {
            log.info("修改邮箱失败，邮箱验证码为空");
            return Result.fail("邮箱验证码不能为空");
        }
        // 2. 从Redis中获取该新邮箱对应的验证码，进行验证
        String redisKey = EMAIL_MODIFY_EMAIL_CODE_KEY + userDTO.getEmail();
        String cachedCode = stringRedisTemplate.opsForValue().get(redisKey);
        if (cachedCode == null) {
            log.info("修改邮箱失败，邮箱验证码已过期");
            return Result.fail("邮箱验证码已过期");
        }
        if (!cachedCode.equals(userDTO.getEmailCode())) {
            log.info("修改邮箱失败，邮箱验证码错误");
            return Result.fail("邮箱验证码错误");
        }
        // 3. 更新用户的邮箱信息
        Long userId = UserThreadLocal.get();
        boolean updated = lambdaUpdate()
                .eq(User::getId, userId)
                .set(User::getEmail, userDTO.getEmail())
                .update();
        if (!updated) {
            log.info("修改邮箱失败，数据库更新用户邮箱失败，用户ID：{}", userId);
            return Result.fail("修改邮箱失败，请稍后重试");
        }
        log.info("用户邮箱修改成功，用户ID：{}", userId);
        return Result.success("邮箱修改成功");
    }
}
