-- ----------------------------
-- Table structure for tb_user
-- ----------------------------
DROP TABLE IF EXISTS `tb_user`;
CREATE TABLE `tb_user`  (
    `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，用户ID',
    `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名',
    `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT '' COMMENT '密码，加密存储',
    `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`) USING BTREE
);



-- ----------------------------
-- Table structure for tb_resume
-- ----------------------------
DROP TABLE IF EXISTS `tb_resume`;
CREATE TABLE `tb_resume`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，简历ID',
    user_id bigint(20) UNSIGNED NOT NULL COMMENT '简历所属的用户ID，关联tb_user表',
    file_path varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '简历文件路径',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_user_resume (user_id) USING BTREE
);



-- ----------------------------
-- Table structure for tb_jd
-- ----------------------------
DROP TABLE IF EXISTS `tb_jd`;
CREATE TABLE `tb_jd`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，JD ID',
    user_id bigint(20) UNSIGNED NOT NULL COMMENT '发布JD的用户ID，关联tb_user表',
    title varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位标题',
    company varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '公司名称',
    location varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '工作地点',
    salary varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '薪资范围',
    description text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位描述',
    request text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位要求',
    bonus text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '职位福利',
    file_path varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'JD文件路径(可选，如果有上传JD文件)',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_user_jd (user_id) USING BTREE
);



-- ----------------------------
-- Table structure for tb_resume_analysis
-- ----------------------------
DROP TABLE IF EXISTS `tb_resume_analysis`;
CREATE TABLE `tb_resume_analysis`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，简历分析ID',
    user_id bigint(20) UNSIGNED NOT NULL COMMENT '简历分析所属的用户ID，关联tb_user表',
    resume_id bigint(20) UNSIGNED NOT NULL COMMENT '被分析的简历ID，关联tb_resume表',
    jd_id bigint(20) UNSIGNED NOT NULL COMMENT '关联的职位ID，关联tb_jd表',
    analysis_result text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '简历分析结果，存储为JSON格式',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_user_resume_analysis (user_id) USING BTREE,
    INDEX idx_resume_analysis (resume_id) USING BTREE,
    INDEX idx_jd_analysis (jd_id) USING BTREE
);