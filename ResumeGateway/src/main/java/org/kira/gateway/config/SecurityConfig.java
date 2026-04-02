package org.kira.gateway.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import java.io.InputStream;
import java.security.*;

/**
 * 安全配置：从 JKS 密钥库加载公私钥对，用于 JWT 签名验证
 */
@Slf4j
@Configuration
public class SecurityConfig {

    /**
     * 从 JKS 密钥库中加载公私钥对
     * 与 ResumeSystem 共用同一个密钥库文件，确保 JWT 签发和验证使用同一密钥
     */
    @Bean
    public KeyPair keyPair(JwtProperties properties, ResourceLoader resourceLoader) {
        try {
            Resource resource = resourceLoader.getResource(properties.getLocation());
            try (InputStream is = resource.getInputStream()) {
                KeyStore keyStore = KeyStore.getInstance("JKS");
                char[] password = properties.getPassword().toCharArray();
                keyStore.load(is, password);

                Key key = keyStore.getKey(properties.getAlias(), password);
                if (!(key instanceof PrivateKey)) {
                    throw new IllegalStateException("Not a private key");
                }
                PublicKey publicKey = keyStore.getCertificate(properties.getAlias()).getPublicKey();
                return new KeyPair(publicKey, (PrivateKey) key);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Failed to load KeyPair from keystore", e);
        }
    }
}
