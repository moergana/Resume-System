-- ----------------------------
-- Table structure for tb_resume
-- ----------------------------
DROP TABLE IF EXISTS `tb_resume`;
CREATE TABLE `tb_resume`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，简历ID',
    resume_id varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '标识简历且是向量数据库中的ID',
    file_path varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '简历文件路径',
		raw_text varchar(8192) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '简历原始文本',
		summary varchar(4096) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '简历总结',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_create_update_time (create_time, update_time) USING BTREE COMMENT '创建时间和更新时间的联合索引',
    INDEX idx_update_time (update_time) USING BTREE COMMENT '更新时间的普通索引'
);



-- ----------------------------
-- Table structure for tb_jd
-- ----------------------------
DROP TABLE IF EXISTS `tb_jd`;
CREATE TABLE `tb_jd`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，JD ID',
    jd_id varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '标识JD且是向量数据库中的ID',
    file_path varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'JD文件路径(可选，如果有上传JD文件)',
    raw_text varchar(8192) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'JD原始文本',
		summary varchar(4096) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'JD总结',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_create_update_time (create_time, update_time) USING BTREE COMMENT '创建时间和更新时间的联合索引',
    INDEX idx_update_time (update_time) USING BTREE COMMENT '更新时间的普通索引'
);