package org.kira.resumesystem.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;

import java.io.InputStream;
import java.security.*;

@Slf4j
@Configuration
@EnableConfigurationProperties(value = {JwtProperties.class})
public class SecurityConfig {

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
