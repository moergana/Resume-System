<script setup>
import {onMounted, ref, computed} from 'vue'
import {useRouter} from 'vue-router'
import request from '@/utils/request.js'
import {
  CANDIDATE_NUMBER,
  CANDIDATE_REQUEST_TYPE_MAP,
  RECRUITER_NUMBER, RECRUITER_REQUEST_TYPE_MAP,
  REQUEST_TYPE_MAP,
  STATUS_MAP
} from "@/utils/constants.js";
import {formatDate, formatToISO} from "@/utils/tools.js";

const router = useRouter()
const historyList = ref([])
const loading = ref(false)

// Pagination
const page = ref(1)
const size = ref(10) // default page size
const totalPages = ref(0)
const jumpPage = ref('') // for input

// Filters
const filterRequestTypes = ref([])
const searchId = ref('')
const searchResumeKeyword = ref('')
const searchJdKeyword = ref('')
const filterStatuses = ref([])
const showTimeFilterDialog = ref(false)
const timeFilter = ref({
  active: false,
  start: '',
  end: ''
})
const tempTimeFilter = ref({
  start: '',
  end: ''
})
const timeFilterError = ref(false)

// Options for filters
const requestTypeOptions = computed(() => {
  // 根据用户的登录身份不同，返回不同的请求类型选项表
  // tips: CANDIDATE_REQUEST_TYPE_MAP 和 RECRUITER_REQUEST_TYPE_MAP 是 Map 对象
  // Map 对象是可迭代的，可以直接用 for...of 或 Array.from() 来遍历，但不能用 Object.entries() 遍历
  // Object.entries()只对普通对象有效（比如可枚举属性的 [key, value] 数组形式的二维数组），对于Map对象则无效
  const role = Number(user.value.role)
  if (role === CANDIDATE_NUMBER) {
    return Array.from(CANDIDATE_REQUEST_TYPE_MAP).map(([key, value]) => ({
      title: value,
      value: key
    }))
  }
  else if (role === RECRUITER_NUMBER) {
    return Array.from(RECRUITER_REQUEST_TYPE_MAP).map(([key, value]) => ({
      title: value,
      value: key
    }))
  }
  else {
    // 如果是未知的身份，则返回空数组
    return []
  }
})

const statusOptions = computed(() => {
  // Convert STATUS_MAP object to array of {title, value}
  // STATUS_MAP is likely an object {0: '...', 1: '...'} so Object.entries works
  // {}定义的对象不可迭代，需要用Object.entries转换为包含key-value对象的数组（Object.entries()对普通对象有效）
  return Object.entries(STATUS_MAP).map(([key, value]) => ({
    title: value,
    value: Number(key)
  }))
})

// Time Filter Logic
const openTimeFilterDialog = () => {
    if (timeFilter.value.active) {
        tempTimeFilter.value = { ...timeFilter.value }
    } else {
        tempTimeFilter.value = { start: '', end: '' }
    }
    timeFilterError.value = false
    showTimeFilterDialog.value = true
}

const confirmTimeFilter = () => {
    if (!tempTimeFilter.value.start && !tempTimeFilter.value.end) {
        timeFilter.value = { active: false, start: '', end: '' }
        showTimeFilterDialog.value = false
        fetchHistory() // Refresh
        return
    }
    if (tempTimeFilter.value.start && tempTimeFilter.value.end) {
        if (new Date(tempTimeFilter.value.end) < new Date(tempTimeFilter.value.start)) {
            timeFilterError.value = true
            return
        }
    }
    timeFilter.value = { ...tempTimeFilter.value, active: true }
    showTimeFilterDialog.value = false
    fetchHistory() // Refresh
}

// Delete dialog state
const showDeleteDialog = ref(false)
const recordToDelete = ref(null)
const deleting = ref(false)

const getStatusColor = (status) => {
  switch (status) {
    case 0: return 'grey'
    case 1: return 'blue'
    case 2: return 'green'
    case 3: return 'red'
    default: return 'grey'
  }
}

const feedback_messages = ref([])

const user = ref({
  username: '',
  role: ''
})

onMounted(() => {
  const storedUser = localStorage.getItem('currentUser')
  if (storedUser) {
    // 获取程序内保存的当前登录用户的信息
    user.value = JSON.parse(storedUser)
    // 初始化分析历史记录的表单
    fetchHistory()
  } else {
    // If no user info found, redirect to login
    router.push('/login')
  }
})

const fetchHistory = async () => {
  loading.value = true
  try {
    const filter = {
        id: searchId.value ? parseInt(searchId.value) : null,
        userId: null,   // 不需要前端传递当前用户的id，后端会根据token自动获取
        resumeKeyword: searchResumeKeyword.value || null,
        jdKeyword: searchJdKeyword.value || null,
        requestType: filterRequestTypes.value.length > 0 ? filterRequestTypes.value : null,
        status: filterStatuses.value.length > 0 ? filterStatuses.value : null,
        startCreateTime: timeFilter.value.active ? (timeFilter.value.start ? formatToISO(timeFilter.value.start) : null) : null,
        endCreateTime: timeFilter.value.active ? (timeFilter.value.end ? formatToISO(timeFilter.value.end) : null) : null,
        // Analysis history tracks createTime usually
    }

    // 1. Fetch Page Data
    const res = await request.post('/resumeAnalysis/list/page', filter, {
      params: {
        page: page.value,
        size: size.value
      }
    })

    if (res.code === 200) {
      historyList.value = res.data.records
      totalPages.value = res.data.pages

      feedback_messages.value.push({
        text: `已加载第 ${page.value} 页`,
        timeout: 1500,
        color: 'success'
      })
    } else {
      console.error(res.message)
      feedback_messages.value.push({
        text: '获取历史记录失败! ' + (res.message ? `: ${res.message}` : ''),
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Failed to fetch history:', error)
    feedback_messages.value.push({
      text: '获取历史记录失败! 请检查网络连接。',
      timeout: 4000,
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

const handlePageChange = (newPage) => {
   if (newPage >= 1 && newPage <= totalPages.value) {
       page.value = newPage
       fetchHistory()
   }
}

const handleJumpPage = () => {
    const p = parseInt(jumpPage.value)
    if (!isNaN(p) && p >= 1 && p <= totalPages.value) {
        page.value = p
        fetchHistory()
        jumpPage.value = ''
    } else {
         feedback_messages.value.push({
            text: '请输入有效的页码',
            timeout: 2000,
            color: 'warning'
         })
    }
}

const handleView = (id) => {
  const route = router.resolve({ name: 'analysis-detail', params: { id }})
  window.open(route.href, '_blank')
}

const prepareDelete = (item, index) => {
  recordToDelete.value = { ...item, displayIndex: index + 1 }
  showDeleteDialog.value = true
}

const handleDelete = async () => {
  if (!recordToDelete.value) return

  deleting.value = true
  try {
    const res = await request.delete(`/resumeAnalysis/${recordToDelete.value.id}`)
    if (res.code === 200) {
      feedback_messages.value.push({
        text: '删除成功',
        timeout: 3000,
        color: 'success',
      })
      showDeleteDialog.value = false
      fetchHistory()
    } else {
      feedback_messages.value.push({
        text: res.message || '删除失败',
        timeout: 3000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Delete error:', error)
    feedback_messages.value.push({
      text: '删除请求发生错误',
      timeout: 3000,
      color: 'error',
    })
  } finally {
    deleting.value = false
  }
}

const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="fill-height">
    <v-app-bar color="white" elevation="2">
      <v-btn icon @click="goBack" class="mr-2">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <v-app-bar-title class="font-weight-bold text-black">分析历史记录</v-app-bar-title>
    </v-app-bar>

    <v-main class="bg-grey-lighten-4 fill-height">
      <v-container>
        <v-card class="elevation-1">
          <v-card-title class="pa-4 font-weight-bold">
            历史记录列表
          </v-card-title>

          <!-- Filters Toolbar -->
          <v-card-text class="pb-0">
             <v-row dense>
               <!-- ID Filter -->
               <v-col cols="12" md="2">
                 <v-text-field
                   v-model="searchId"
                   label="ID 搜索"
                   prepend-inner-icon="mdi-identifier"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchHistory()"
                 ></v-text-field>
               </v-col>

               <!-- Request Type Filter -->
               <v-col cols="12" md="2">
                 <v-select
                   v-model="filterRequestTypes"
                   :items="requestTypeOptions"
                   label="类型"
                   multiple
                   chips
                   variant="outlined"
                   density="compact"
                   hide-details
                   @update:model-value="fetchHistory"
                 ></v-select>
               </v-col>

               <!-- Keyword Search -->
               <v-col cols="12" md="2">
                 <v-text-field
                   v-model="searchResumeKeyword"
                   label="简历名称"
                   prepend-inner-icon="mdi-magnify"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchHistory()"
                 ></v-text-field>
               </v-col>
               <v-col cols="12" md="2">
                 <v-text-field
                   v-model="searchJdKeyword"
                   label="JD名称"
                   prepend-inner-icon="mdi-magnify"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchHistory()"
                 ></v-text-field>
               </v-col>

               <!-- Status Filter -->
               <v-col cols="12" md="2">
                 <v-select
                   v-model="filterStatuses"
                   :items="statusOptions"
                   label="状态"
                   multiple
                   chips
                   variant="outlined"
                   density="compact"
                   hide-details
                   @update:model-value="fetchHistory"
                 ></v-select>
               </v-col>

               <!-- Time Filter -->
               <v-col cols="12" md="2" class="d-flex align-center">
                 <v-btn
                     :color="timeFilter.active ? 'primary' : 'default'"
                     :variant="timeFilter.active ? 'flat' : 'outlined'"
                     prepend-icon="mdi-calendar-filter"
                     @click="openTimeFilterDialog"
                     block
                   >
                     时间过滤
                 </v-btn>
               </v-col>
             </v-row>
          </v-card-text>

          <v-table class="mt-2">
            <thead>
              <tr>
                <th class="text-center font-weight-bold">序号</th>
                <th class="text-center font-weight-bold">ID</th>
                <th class="text-center font-weight-bold">类型</th>
                <th class="text-center font-weight-bold">简历名称</th>
                <th class="text-center font-weight-bold">JD名称</th>
                <th class="text-center font-weight-bold">状态</th>
                <th class="text-center font-weight-bold">创建时间</th>
                <th class="text-center font-weight-bold">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="historyList.length === 0 && !loading">
                <td colspan="8" class="text-center pa-4 text-grey">
                   {{ '暂无历史记录' }}
                </td>
              </tr>
              <tr v-for="(item, index) in historyList" :key="index">
                <td class="text-center">{{ index + 1 }}</td>
                <td class="text-center">{{ item.id }}</td>
                <td class="text-center">{{ REQUEST_TYPE_MAP.get(item.requestType) }}</td>
                <td class="text-center">
                  <template v-if="item.resumeName">
                    {{ item.resumeName }}
                  </template>
                  <template v-else>
                    <v-chip
                        :color="'red'"
                        size="small"
                        class="font-weight-bold text-white"
                    >
                      不存在或已被删除
                    </v-chip>
                  </template>
                </td>
                <td class="text-center">
                  <template v-if="item.jdName">
                    {{ item.jdName }}
                  </template>
                  <template v-else>
                    <v-chip
                        :color="'red'"
                        size="small"
                        class="font-weight-bold text-white"
                    >
                      不存在或已被删除
                    </v-chip>
                  </template>
                </td>
                <td class="text-center">
                  <v-chip
                    :color="getStatusColor(item.status)"
                    size="small"
                    class="font-weight-bold text-white"
                  >
                    {{ STATUS_MAP[item.status] }}
                  </v-chip>
                </td>
                <td class="text-center">{{ formatDate(item.createTime) }}</td>
                <td class="text-center">
                  <v-btn icon
                    size="small"
                    color="primary"
                    variant="text"
                    @click="handleView(item.id)"
                    class="mr-2"
                  >
                    <v-icon>mdi-file-document</v-icon>
                    <v-tooltip activator="parent" location="bottom">查看</v-tooltip>
                  </v-btn>
                  <v-btn icon
                    size="small"
                    color="error"
                    variant="text"
                    @click="prepareDelete(item, index)"
                  >
                    <v-icon>mdi-delete</v-icon>
                    <v-tooltip activator="parent" location="bottom">删除</v-tooltip>
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
          <div v-if="loading" class="text-center pa-6">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </div>

          <!-- Pagination Controls -->
          <v-divider></v-divider>
          <v-card-actions class="justify-center pa-4">
             <v-row align="center" justify="center" dense>
                <v-col cols="auto">
                  <v-btn
                    variant="text"
                    icon="mdi-chevron-left"
                    :disabled="page <= 1 || loading"
                    @click="handlePageChange(page - 1)"
                  ></v-btn>
                </v-col>
                <v-col cols="auto">
                   <span class="text-body-2">第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
                </v-col>
                <v-col cols="auto">
                  <v-btn
                    variant="text"
                    icon="mdi-chevron-right"
                    :disabled="page >= totalPages || loading"
                    @click="handlePageChange(page + 1)"
                  ></v-btn>
                </v-col>
                <v-col cols="auto" class="ml-4">
                  <v-text-field
                      v-model="jumpPage"
                      label="跳转至"
                      type="number"
                      variant="outlined"
                      density="compact"
                      hide-details
                      style="width: 80px"
                      @keydown="e => e.key === 'Enter' && handleJumpPage()"
                  ></v-text-field>
                </v-col>
             </v-row>
          </v-card-actions>
        </v-card>

        <!-- Delete Confirmation Dialog -->
        <v-dialog v-model="showDeleteDialog" max-width="400">
          <v-card>
            <v-card-title class="text-h5 pa-4">
              确认删除记录
            </v-card-title>
            <v-card-text class="pa-4">
              确定要删除这条记录（序号：<span class="font-weight-bold">{{ recordToDelete ? recordToDelete.displayIndex : '' }}</span>）吗？
            </v-card-text>
            <v-card-actions class="pa-4 justify-end">
              <v-btn
                color="grey-darken-1"
                variant="text"
                @click="showDeleteDialog = false"
              >
                取消
              </v-btn>
              <v-btn
                color="error"
                variant="flat"
                :loading="deleting"
                @click="handleDelete"
              >
                确认
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Time Filter Dialog -->
        <v-dialog v-model="showTimeFilterDialog" max-width="400">
           <v-card>
             <v-card-title class="text-h6 pa-4">设置时间过滤器</v-card-title>
             <v-card-text class="pa-4">
               <p class="text-caption mb-1">起始时间 (创建时间)</p>
               <v-text-field v-model="tempTimeFilter.start" type="datetime-local" variant="outlined" density="compact"></v-text-field>
               <p class="text-caption mb-1 mt-2">终止时间 (创建时间)</p>
               <v-text-field
                 v-model="tempTimeFilter.end"
                 type="datetime-local"
                 variant="outlined"
                 density="compact"
                 :error="timeFilterError"
                 :error-messages="timeFilterError ? '终止时间不能小于起始时间' : ''"
               ></v-text-field>
             </v-card-text>
             <v-card-actions class="pa-4 justify-end">
               <v-btn color="grey-darken-1" variant="text" @click="showTimeFilterDialog = false">取消</v-btn>
               <v-btn color="primary" variant="flat" @click="confirmTimeFilter">确认</v-btn>
             </v-card-actions>
           </v-card>
        </v-dialog>

        <v-snackbar-queue v-model="feedback_messages"></v-snackbar-queue>
      </v-container>
    </v-main>
  </div>
</template>

<style scoped>
</style>
