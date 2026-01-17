// 用户角色在数据库中对应的数值
export const CANDIDATE_NUMBER = 0
export const RECRUITER_NUMBER = 1

// 用户角色映射表，从数值映射到中文名称
// 需要注意：Map对象是可迭代的，且键值对保持原始类型
export const ROLE_MAP = new Map([
    [CANDIDATE_NUMBER, '求职者'],
    [RECRUITER_NUMBER, '招聘者']
])

// 分析请求处理状态映射表
// 需要注意：{}定义的对象是普通对象，且不可迭代，并且键会被自动转换为字符串
export const STATUS_MAP = {
    0: '待分析',
    1: '分析中',
    2: '分析完成',
    3: '分析失败'
}

// 不同的分析请求类型标识值
export const REQUEST_RESUME_UPLOAD = "resume_upload"
export const REQUEST_JD_UPLOAD = "jd_upload"
export const REQUEST_RESUME_JD_DIFFER = "resume_jd_differ"
export const REQUEST_RESUME_ADVISE = "resume_advise"
export const REQUEST_JD_MATCH = "jd_match"
export const REQUEST_RESUME_MATCH = "resume_match"
export const REQUEST_RESUME_DELETE = "resume_delete"
export const REQUEST_JD_DELETE = "jd_delete"

// 分析请求类型映射表，从标识值映射到中文名称
export const REQUEST_TYPE_MAP = new Map([
    [REQUEST_RESUME_UPLOAD, '简历上传'],
    [REQUEST_JD_UPLOAD, '职位发布'],
    [REQUEST_RESUME_JD_DIFFER, '指定职位与简历的分析'],
    [REQUEST_RESUME_ADVISE, '指定简历与职位的分析'],
    [REQUEST_JD_MATCH, '全库匹配合适的职位'],
    [REQUEST_RESUME_MATCH, '全库匹配合适的简历'],
    [REQUEST_RESUME_DELETE, '删除简历'],
    [REQUEST_JD_DELETE, '删除职位']
])

// 求职者的分析请求类型映射表
export const CANDIDATE_REQUEST_TYPE_MAP = new Map([
    [REQUEST_RESUME_UPLOAD, '简历上传'],
    [REQUEST_RESUME_ADVISE, '指定简历与职位的分析'],
    [REQUEST_JD_MATCH, '全库匹配合适的职位'],
    [REQUEST_RESUME_DELETE, '删除简历']
])

// 招聘者的分析请求类型映射表
export const RECRUITER_REQUEST_TYPE_MAP = new Map([
    [REQUEST_JD_UPLOAD, '职位发布'],
    [REQUEST_RESUME_JD_DIFFER, '指定职位与简历的分析'],
    [REQUEST_RESUME_MATCH, '全库匹配合适的简历'],
    [REQUEST_JD_DELETE, '删除职位']
])


// 分析结果展示页有许多面板，以下是不同信息面板的标识值
export const BASIC_INFO_PANEL_VALUE = "basic-info"
export const RESUME_JD_INFO_PANEL_VALUE = "resume-jd-info"
export const ANALYSIS_RESULT_PANEL_VALUE = "analysis-result"
export const RETRIEVED_RESUMES_PANEL_VALUE = "retrieved-resumes"
export const RETRIEVED_JDS_PANEL_VALUE = "retrieved-jds"

// RESUME_JD_INFO_PANEL_VALUE面板内部的子面板标识值
export const BONUS_PANEL_VALUE = "bonus"
export const DESCRIPTION_PANEL_VALUE = "description"
export const REQUIREMENTS_PANEL_VALUE = "requirements"

// ANALYSIS_RESULT_PANEL_VALUE面板内部的子面板标识值
export const DIFFERENCES_PANEL_VALUE = "differences"
export const SUGGESTIONS_PANEL_VALUE = "suggestions"
export const TIPS_PANEL_VALUE = "tips"