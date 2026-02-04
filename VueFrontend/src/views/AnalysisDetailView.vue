<script setup>
import { ref, onMounted, computed } from 'vue'
import VueMarkdown from 'vue-markdown-render'
import { useRoute } from 'vue-router'
import request from '@/utils/request.js'
import {
  ANALYSIS_RESULT_PANEL_VALUE,
  BASIC_INFO_PANEL_VALUE, BONUS_PANEL_VALUE, DESCRIPTION_PANEL_VALUE, DIFFERENCES_PANEL_VALUE, REQUIREMENTS_PANEL_VALUE,
  RESUME_JD_INFO_PANEL_VALUE, RETRIEVED_JDS_PANEL_VALUE, RETRIEVED_RESUMES_PANEL_VALUE,
  STATUS_MAP, SUGGESTIONS_PANEL_VALUE, TIPS_PANEL_VALUE
} from "@/utils/constants.js"
import { formatDate } from "@/utils/tools.js"

const route = useRoute()
const analysisId = route.params.id
const analysisData = ref(null)
const loading = ref(false)
const feedback_messages = ref([])
const main_panels = ref([
  BASIC_INFO_PANEL_VALUE,
  RESUME_JD_INFO_PANEL_VALUE,
  ANALYSIS_RESULT_PANEL_VALUE,
  RETRIEVED_RESUMES_PANEL_VALUE,
  RETRIEVED_JDS_PANEL_VALUE
]) // Open all panels by default
const resume_jd_info_panels = ref([
  BONUS_PANEL_VALUE,
  DESCRIPTION_PANEL_VALUE,
  REQUIREMENTS_PANEL_VALUE
])
const analysis_result_panels = ref([
  DIFFERENCES_PANEL_VALUE,
  SUGGESTIONS_PANEL_VALUE,
  TIPS_PANEL_VALUE
])
const retrieved_resumes_panels = ref([])
const retrieved_jds_panels = ref([])

onMounted(() => {
  if (analysisId) {
    fetchAnalysisDetail()
  } else {
    feedback_messages.value.push({
      text: '无效的分析记录ID',
      color: 'error'
    })
  }
})

const parsedAnalysisResult = computed(() => {
  if (!analysisData.value?.analysisResult) return null
  try {
    const result = typeof analysisData.value.analysisResult === 'string'
      ? JSON.parse(analysisData.value.analysisResult)
      : analysisData.value.analysisResult

    // Ensure match_score is valid
    if (result.match_score !== undefined) {
      let score = parseInt(result.match_score)
      if (isNaN(score)) score = 0
      if (score < 0) score = 0
      if (score > 100) score = 100
      result.match_score = score
    }
    return result
  } catch (e) {
    console.error('Failed to parse analysisResult:', e)
    return null
  }
})

const parsedRetrievedResumes = computed(() => {
  if (!analysisData.value?.retrievedResumes) return []
  try {
    const data = typeof analysisData.value.retrievedResumes === 'string'
      ? JSON.parse(analysisData.value.retrievedResumes)
      : analysisData.value.retrievedResumes
    return Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Failed to parse retrievedResumes:', e)
    return []
  }
})

const parsedRetrievedJds = computed(() => {
  if (!analysisData.value?.retrievedJds) return []
  try {
    const data = typeof analysisData.value.retrievedJds === 'string'
      ? JSON.parse(analysisData.value.retrievedJds)
      : analysisData.value.retrievedJds
    return Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Failed to parse retrievedJds:', e)
    return []
  }
})

const getScoreColor = (score) => {
  if (score === undefined || score === null) return 'grey'
  if (score >= 0 && score <= 25) return 'red'
  if (score <= 50) return 'amber' // yellow is often too bright on white
  if (score <= 75) return 'blue'
  return 'green'
}

const fetchAnalysisDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/resumeAnalysis/${analysisId}`)
    if (res.code === 200) {
      analysisData.value = res.data
    } else {
      feedback_messages.value.push({
        text: '获取详情失败! ' + (res.message || ''),
        timeout: 3000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Failed to fetch analysis detail:', error)
    feedback_messages.value.push({
        text: '获取详情请求发生错误',
        timeout: 3000,
        color: 'error',
    })
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 0: return 'grey'
    case 1: return 'blue'
    case 2: return 'green'
    case 3: return 'red'
    default: return 'grey'
  }
}

// Check request type for showing section
const showAnalysisResult = computed(() => {
  if (!analysisData.value) return false
  const t = analysisData.value.requestType
  return t === 'resume_jd_differ' || t === 'resume_advise'
})

const showRetrievedResumes = computed(() => {
  if (!analysisData.value) return false
  return analysisData.value.requestType === 'resume_match'
})

const showRetrievedJds = computed(() => {
  if (!analysisData.value) return false
  return analysisData.value.requestType === 'jd_match'
})

const isEmpty = (val) => {
  return val === null || val === undefined || val === ''
}

const openChatBot = () => {
  if (analysisData.value && analysisData.value.id) {
    window.open(`http://localhost:7860/?analysis_id=${analysisData.value.id}`, '_blank')
  }
}

</script>

<template>
  <div class="fill-height bg-grey-lighten-5">
    <v-app-bar color="white" elevation="2">
       <v-app-bar-title class="font-weight-bold text-black">分析记录详情</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container>
        <div v-if="loading" class="text-center pa-10">
           <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
           <div class="mt-4 text-grey">加载中...</div>
        </div>

        <v-expansion-panels v-else-if="analysisData" v-model="main_panels" multiple>
          <!-- 1. 基本信息 -->
          <v-expansion-panel :value="BASIC_INFO_PANEL_VALUE">
            <v-expansion-panel-title class="text-h6 font-weight-bold">
              基本信息
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field label="分析ID" :model-value="analysisData.id" variant="outlined" readonly density="compact"></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field label="用户ID" :model-value="analysisData.userId" variant="outlined" readonly density="compact"></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                   <v-text-field label="请求类型" :model-value="analysisData.requestType" variant="outlined" readonly density="compact"></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                   <div class="d-flex align-center">
                     <span class="text-medium-emphasis mr-2">状态:</span>
                     <v-chip :color="getStatusColor(analysisData.status)" class="text-white font-weight-bold" label>
                        {{ STATUS_MAP[analysisData.status] || '未知' }}
                     </v-chip>
                   </div>
                </v-col>
                 <v-col cols="12" md="6">
                  <v-text-field label="创建时间" :model-value="formatDate(analysisData.createTime)" variant="outlined" readonly density="compact"></v-text-field>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 2. 简历与JD信息 -->
          <v-expansion-panel :value="RESUME_JD_INFO_PANEL_VALUE">
            <v-expansion-panel-title class="text-h6 font-weight-bold">
              简历与JD信息
            </v-expansion-panel-title>
            <v-expansion-panel-text>
               <v-row>
                 <v-col cols="12" md="6">
                   <v-text-field label="简历名称" :model-value="analysisData.resumeName || '无'" variant="outlined" readonly density="compact"></v-text-field>
                 </v-col>
                 <v-col cols="12" md="6">
                   <v-text-field label="JD名称" :model-value="analysisData.jdName || '无'" variant="outlined" readonly density="compact"></v-text-field>
                 </v-col>
                 <v-col cols="12">
                   <v-text-field label="岗位标题" :model-value="analysisData.title || '无'" variant="outlined" readonly density="compact"></v-text-field>
                 </v-col>
                 <v-col cols="12" md="6">
                   <v-text-field label="公司名称" :model-value="analysisData.company || '无'" variant="outlined" readonly density="compact"></v-text-field>
                 </v-col>
                 <v-col cols="12" md="6">
                    <v-text-field label="工作地点" :model-value="analysisData.location || '无'" variant="outlined" readonly density="compact"></v-text-field>
                 </v-col>
                 <v-col cols="12" md="6">
                    <v-text-field label="薪资待遇" :model-value="analysisData.salary || '无'" variant="outlined" readonly density="compact"></v-text-field>
                 </v-col>
               </v-row>

               <v-expansion-panels v-model="resume_jd_info_panels" multiple variant="accordion" class="mt-4">
                 <v-expansion-panel :value="BONUS_PANEL_VALUE">
                   <v-expansion-panel-title class="font-weight-bold">
                      岗位福利 (Bonus)
                   </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div v-if="isEmpty(analysisData.bonus)" class="text-center text-grey my-4">无内容</div>
                      <div v-else class="text-pre-wrap">
                        <VueMarkdown :source="analysisData.bonus" />
                      </div>
                    </v-expansion-panel-text>
                 </v-expansion-panel>
                 <v-expansion-panel :value="DESCRIPTION_PANEL_VALUE">
                   <v-expansion-panel-title class="font-weight-bold">
                      职位描述 (Description)
                   </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div v-if="isEmpty(analysisData.description)" class="text-center text-grey my-4">无内容</div>
                      <div v-else class="text-pre-wrap">
                        <VueMarkdown :source="analysisData.description" />
                      </div>
                    </v-expansion-panel-text>
                 </v-expansion-panel>
                 <v-expansion-panel :value="REQUIREMENTS_PANEL_VALUE">
                   <v-expansion-panel-title class="font-weight-bold">
                     任职要求 (Requirements)
                   </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div v-if="isEmpty(analysisData.requirements)" class="text-center text-grey my-4">无内容</div>
                      <div v-else class="text-pre-wrap">
                        <VueMarkdown :source="analysisData.requirements" />
                      </div>
                    </v-expansion-panel-text>
                 </v-expansion-panel>
               </v-expansion-panels>

            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 3. 分析结果 (仅 Type = resume_jd_differ | resume_advise) -->
          <v-expansion-panel v-if="showAnalysisResult" :value="ANALYSIS_RESULT_PANEL_VALUE">
            <v-expansion-panel-title class="text-h6 font-weight-bold">
              分析结果
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div v-if="!parsedAnalysisResult" class="text-center text-grey my-4">无分析结果</div>
              <div v-else>
                 <div class="d-flex justify-center align-center flex-column my-6">
                    <v-progress-circular
                      :model-value="parsedAnalysisResult.match_score"
                      :color="getScoreColor(parsedAnalysisResult.match_score)"
                      :size="120"
                      :width="15"
                    >
                      <span class="text-h5 font-weight-bold" :class="`text-${getScoreColor(parsedAnalysisResult.match_score)}`">
                        {{ parsedAnalysisResult.match_score }}
                        <span class="text-body-1 text-grey">/100</span>
                      </span>
                    </v-progress-circular>
                    <div class="mt-2 text-subtitle-1 font-weight-medium text-grey-darken-2">匹配度</div>
                 </div>

                 <v-expansion-panels v-model="analysis_result_panels" multiple variant="accordion">
                   <v-expansion-panel :value="DIFFERENCES_PANEL_VALUE">
                     <v-expansion-panel-title class="font-weight-bold">
                       差异分析 (Differences)
                     </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div v-if="isEmpty(parsedAnalysisResult.differences)" class="text-center text-grey my-4">无内容</div>
                        <div v-else class="text-pre-wrap">
                          <VueMarkdown :source="parsedAnalysisResult.differences" />
                        </div>
                      </v-expansion-panel-text>
                   </v-expansion-panel>
                   <v-expansion-panel :value="SUGGESTIONS_PANEL_VALUE">
                     <v-expansion-panel-title class="font-weight-bold">
                       改进建议 (Improvement Suggestions)
                     </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div v-if="isEmpty(parsedAnalysisResult.improvement_suggestions)" class="text-center text-grey my-4">无内容</div>
                        <div v-else class="text-pre-wrap">
                          <VueMarkdown :source="parsedAnalysisResult.improvement_suggestions" />
                        </div>
                      </v-expansion-panel-text>
                   </v-expansion-panel>
                   <v-expansion-panel :value="TIPS_PANEL_VALUE">
                     <v-expansion-panel-title class="font-weight-bold">
                       求职小贴士 (Job Hunting Tips)
                     </v-expansion-panel-title>
                      <v-expansion-panel-text>
                         <div v-if="isEmpty(parsedAnalysisResult.job_hunting_tips)" class="text-center text-grey my-4">无内容</div>
                         <div v-else class="text-pre-wrap">
                           <VueMarkdown :source="parsedAnalysisResult.job_hunting_tips" />
                         </div>
                      </v-expansion-panel-text>
                   </v-expansion-panel>
                 </v-expansion-panels>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- 4. 匹配简历列表 (仅 Type = resume_match) -->
          <v-expansion-panel
              v-model="retrieved_resumes_panels"
              v-if="showRetrievedResumes"
              :value="RETRIEVED_RESUMES_PANEL_VALUE"
          >
             <v-expansion-panel-title class="text-h6 font-weight-bold">
               匹配简历列表
             </v-expansion-panel-title>
             <v-expansion-panel-text>
               <div v-if="!parsedRetrievedResumes || parsedRetrievedResumes.length === 0" class="text-center text-grey my-4">
                 未找到匹配的简历
               </div>
               <v-expansion-panels v-else variant="popout" class="mt-2">
                 <v-expansion-panel
                   v-for="(item, index) in parsedRetrievedResumes"
                   :key="index"
                 >
                   <v-expansion-panel-title>
                     <div class="d-flex w-100 align-center justify-space-between mr-4">
                        <div class="font-weight-bold">第 {{ item.rank }} 名 (ID: {{ item.resume_id }})</div>
                        <v-chip color="primary" variant="outlined" size="small">
                          相似度: {{ item.similarity_score }}
                        </v-chip>
                     </div>
                   </v-expansion-panel-title>
                   <v-expansion-panel-text>
                      <div v-if="isEmpty(item.content)" class="text-center text-grey">无内容</div>
                      <div v-else class="text-pre-wrap body-2">
                        <VueMarkdown :source="item.content" />
                      </div>
                   </v-expansion-panel-text>
                 </v-expansion-panel>
               </v-expansion-panels>
             </v-expansion-panel-text>
          </v-expansion-panel>

           <!-- 5. 匹配JD列表 (仅 Type = jd_match) -->
          <v-expansion-panel
              v-model="retrieved_jds_panels"
              v-if="showRetrievedJds"
              :value="RETRIEVED_JDS_PANEL_VALUE"
          >
             <v-expansion-panel-title class="text-h6 font-weight-bold">
               匹配JD列表
             </v-expansion-panel-title>
             <v-expansion-panel-text>
               <div v-if="!parsedRetrievedJds || parsedRetrievedJds.length === 0" class="text-center text-grey my-4">
                 未找到匹配的JD
               </div>
               <v-expansion-panels v-else variant="popout" class="mt-2">
                 <v-expansion-panel
                   v-for="(item, index) in parsedRetrievedJds"
                   :key="index"
                 >
                   <v-expansion-panel-title>
                     <div class="d-flex w-100 align-center justify-space-between mr-4">
                        <div class="font-weight-bold">第 {{ item.rank }} 名 (JD ID: {{ item.JD_id }})</div>
                        <v-chip color="primary" variant="outlined" size="small">
                          相似度: {{ item.similarity_score }}
                        </v-chip>
                     </div>
                   </v-expansion-panel-title>
                   <v-expansion-panel-text>
                      <div v-if="isEmpty(item.content)" class="text-center text-grey">无内容</div>
                      <div v-else class="text-pre-wrap body-2">
                        <VueMarkdown :source="item.content" />
                      </div>
                   </v-expansion-panel-text>
                 </v-expansion-panel>
               </v-expansion-panels>
             </v-expansion-panel-text>
          </v-expansion-panel>

        </v-expansion-panels>

        <v-alert v-else class="mt-4" type="warning" variant="tonal">
          未找到相关分析记录数据
        </v-alert>

        <div class="mt-2 text-center" v-if="showAnalysisResult">
          <v-icon color="primary" size="40">mdi-robot-happy-outline</v-icon>
          <a href="#"
             class="text-primary text-decoration-underline ml-2 font-weight-bold"
             @click.prevent="openChatBot"
             v-tooltip="'小助手已自动读取分析记录哦！'"
          >
            与分析小助手聊一聊
          </a>
        </div>

        <v-snackbar-queue v-model="feedback_messages"></v-snackbar-queue>
      </v-container>
    </v-main>
  </div>
</template>

<style scoped>
.text-pre-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}
.font-monospace :deep(textarea) {
  font-family: monospace;
}
</style>

