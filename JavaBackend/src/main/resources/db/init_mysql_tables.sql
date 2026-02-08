-- ----------------------------
-- Table structure for tb_user
-- ----------------------------
DROP TABLE IF EXISTS `tb_user`;
CREATE TABLE `tb_user`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，用户ID',
    username varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL UNIQUE COMMENT '用户名',
    password varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT '' COMMENT '密码，加密存储',
    role int NOT NULL DEFAULT 0 COMMENT '用户角色，0-求职者，1-招聘者',
    email varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT '' COMMENT '用户邮箱',
    create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    UNIQUE INDEX idx_username (username) USING BTREE COMMENT '用户名的唯一索引',
    INDEX idx_create_time (create_time) USING BTREE COMMENT '创建时间的普通索引',
    INDEX idx_update_time (update_time) USING BTREE COMMENT '更新时间的普通索引'
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
    INDEX idx_user_resume (user_id) USING BTREE COMMENT '用户ID的普通索引',
    INDEX idx_create_update_time (create_time, update_time) USING BTREE COMMENT '创建时间和更新时间的联合索引',
    INDEX idx_update_time (update_time) USING BTREE COMMENT '更新时间的普通索引'
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
    requirements text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位要求',
    bonus text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '职位福利',
    file_path varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'JD文件路径(可选，如果有上传JD文件)',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_user_jd (user_id) USING BTREE COMMENT '用户ID的普通索引',
    INDEX idx_create_update_time (create_time, update_time) USING BTREE COMMENT '创建时间和更新时间的联合索引',
    INDEX idx_update_time (update_time) USING BTREE COMMENT '更新时间的普通索引'
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
    request_type varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '请求类型，如匹配度分析、优势劣势分析等',
    status int NOT NULL DEFAULT 0 COMMENT '分析状态，0-未开始，1-进行中，2-已完成，3-失败',
    analysis_result text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '简历分析结果，存储为JSON格式',
    retrieved_resumes text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '检索到的相关简历信息，存储为JSON格式',
    retrieved_jds text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '检索到的相关职位信息，存储为JSON格式',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_user_id (user_id) USING BTREE COMMENT '用户ID的普通索引',
    INDEX idx_resume_id (resume_id) USING BTREE COMMENT '简历ID的普通索引',
    INDEX idx_jd_id (jd_id) USING BTREE COMMENT '职位ID的普通索引',
    INDEX idx_create_time (create_time) USING BTREE COMMENT '创建时间的普通索引'
);



-- ----------------------------
-- Table structure for tb_analysis_summary
-- ----------------------------
DROP TABLE IF EXISTS `tb_analysis_summary`;
CREATE TABLE `tb_analysis_summary`  (
    id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键，简历分析ID',
    analysis_id bigint(20) UNSIGNED NOT NULL COMMENT '简历分析ID，关联tb_resume_analysis表',
    user_id bigint(20) UNSIGNED NOT NULL COMMENT '简历分析所属的用户ID，关联tb_user表',
    resume_id bigint(20) UNSIGNED NOT NULL COMMENT '被分析的简历ID，关联tb_resume表',
    jd_id bigint(20) UNSIGNED NOT NULL COMMENT '关联的职位ID，关联tb_jd表',
    resume_summary_text text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '该分析记录中涉及的简历的总结文本',
    jd_summary_text text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '该分析记录中涉及的JD的总结文本',
    create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id) USING BTREE,
    INDEX idx_analysis_id (analysis_id) USING BTREE COMMENT '简历分析ID的普通索引',
    INDEX idx_user_id (user_id) USING BTREE COMMENT '用户ID的普通索引',
    INDEX idx_resume_id (resume_id) USING BTREE COMMENT '简历ID的普通索引',
    INDEX idx_jd_id (jd_id) USING BTREE COMMENT '职位ID的普通索引',
    INDEX idx_create_time (create_time) USING BTREE COMMENT '创建时间的普通索引'
);