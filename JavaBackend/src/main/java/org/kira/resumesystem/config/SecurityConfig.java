package org.kira.resumesystem.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.io.InputStream;
import java.security.*;

@Slf4j
@Configuration
@EnableConfigurationProperties(value = {JwtProperties.class})
public class SecurityConfig {

    /**
     * 密码编码器，用于对用户密码进行加密存储和验证，采用 “BCrypt 哈希算法 + 加盐” 实现加密
     * @return PasswordEncoder
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * 从 JKS 密钥库中加载公私钥对
     * @param properties JwtProperties 配置属性
     * @param resourceLoader 资源加载器
     * @return KeyPair 包含公钥和私钥
     */
    @Bean
    public KeyPair keyPair(JwtProperties properties,
                           ResourceLoader resourceLoader) {
        try {
            // 1. 加载 keystore 资源
            Resource resource = resourceLoader.getResource(properties.getLocation());
            try (InputStream is = resource.getInputStream()) {

                // 2. 加载 KeyStore
                KeyStore keyStore = KeyStore.getInstance("JKS");
                char[] password = properties.getPassword().toCharArray();
                keyStore.load(is, password);

                // 3. 获取私钥
                Key key = keyStore.getKey(properties.getAlias(), password);
                if (!(key instanceof PrivateKey)) {
                    throw new IllegalStateException("Not a private key");
                }

                // 4. 获取公钥
                PublicKey publicKey =
                        keyStore.getCertificate(properties.getAlias()).getPublicKey();

                // 5. 组装 KeyPair
                return new KeyPair(publicKey, (PrivateKey) key);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Failed to load KeyPair from keystore", e);
        }
    }
}
