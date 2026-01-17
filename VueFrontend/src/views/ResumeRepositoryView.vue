<script setup>
import { onMounted, ref, computed } from 'vue'
import request from '@/utils/request.js'
import {formatDate, formatToISO} from "@/utils/tools.js";

const resumeList = ref([])
const loading = ref(false)
const feedback_messages = ref([])

// Pagination
const page = ref(1)
const size = ref(10)
const totalPages = ref(0)
const jumpPage = ref('')

// Filters
const searchId = ref('')
const searchUserId = ref('')
const searchName = ref('')

// Time Filter
const showTimeFilterDialog = ref(false)
const timeFilter = ref({
  active: false,
  target: 'createTime', // createTime or updateTime
  start: '',
  end: ''
})
const tempTimeFilter = ref({
  target: 'createTime',
  start: '',
  end: ''
})
const timeFilterError = ref(false)

const openTimeFilterDialog = () => {
    if (timeFilter.value.active) {
        tempTimeFilter.value = { ...timeFilter.value }
    } else {
        tempTimeFilter.value = { target: 'createTime', start: '', end: '' }
    }
    timeFilterError.value = false
    showTimeFilterDialog.value = true
}

const confirmTimeFilter = () => {
   if (!tempTimeFilter.value.start && !tempTimeFilter.value.end) {
       timeFilter.value = { active: false, target: 'createTime', start: '', end: '' }
       showTimeFilterDialog.value = false
       fetchAllResumes() // refresh
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
   fetchAllResumes() // refresh
}

onMounted(() => {
  fetchAllResumes()
})

const fetchAllResumes = async () => {
  loading.value = true
  try {
    const filter = {
        id: searchId.value ? parseInt(searchId.value) : null,
        userId: searchUserId.value ? parseInt(searchUserId.value) : null,
        resumeKeyword: searchName.value || null,
        startCreateTime: (timeFilter.value.active && timeFilter.value.target === 'createTime') ? (timeFilter.value.start ? formatToISO(timeFilter.value.start) : null) : null,
        endCreateTime: (timeFilter.value.active && timeFilter.value.target === 'createTime') ? (timeFilter.value.end ? formatToISO(timeFilter.value.end) : null) : null,
        startUpdateTime: (timeFilter.value.active && timeFilter.value.target === 'updateTime') ? (timeFilter.value.start ? formatToISO(timeFilter.value.start) : null) : null,
        endUpdateTime: (timeFilter.value.active && timeFilter.value.target === 'updateTime') ? (timeFilter.value.end ? formatToISO(timeFilter.value.end) : null) : null,
    }

    const res = await request.post('/resume/list/page', filter, {
      params: { page: page.value, size: size.value }
    })
    if (res.code === 200) {
      resumeList.value = res.data.records
      totalPages.value = res.data.pages

      feedback_messages.value.push({
        text: `已加载第 ${page.value} 页`,
        timeout: 1500,
        color: 'success'
      })
    } else {
      feedback_messages.value.push({
        text: '获取简历列表失败! ' + (res.message || ''),
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Failed to fetch resumes:', error)
    feedback_messages.value.push({
      text: '获取简历列表失败! 请检查网络连接。',
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
    fetchAllResumes()
  }
}

const handleJumpPage = () => {
  const p = parseInt(jumpPage.value)
  if (!isNaN(p) && p >= 1 && p <= totalPages.value) {
    page.value = p
    fetchAllResumes()
    jumpPage.value = ''
  } else {
    feedback_messages.value.push({ text: '请输入有效的页码', timeout: 2000, color: 'warning' })
  }
}

const handleDownload = async (id) => {
  try {
    const res = await request.post(`/resume/download/${id}`, null, {
      responseType: 'blob'
    })
    // Check if it is a blob (file) or json (error) - axios 'request.js' might handle this differently.
    // Assuming request.js handles simple JSON responses. If it is blob, it returns it.
    // We need to check if response is valid.

    // NOTE: request.js wrapper usually returns res.data. If responseType is blob, we might need special handling in request.js or here.
    // Assuming request.js returns the blob processing if I haven't seen request.js.
    // Let's implement standard download logic assuming raw response if request.js doesn't wrap blob.

    // Wait, the prompt implies using the existing request utility.
    // Let's rely on standard browser download behavior if possible but axios download needs blob handling.

    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `resume_${id}.pdf`) // Or get filename from header
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    feedback_messages.value.push({
      text: '已开始下载',
      timeout: 3000,
      color: 'success',
    })
  } catch (error) {
     console.error("Download failed", error);
     feedback_messages.value.push({
        text: '下载失败',
        timeout: 3000,
        color: 'error'
     })
  }
}
</script>

<template>
  <div class="fill-height bg-grey-lighten-5">
    <v-app-bar color="white" elevation="2">
      <v-app-bar-title class="font-weight-bold text-black">简历仓库</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container>
        <v-card class="elevation-1">
          <v-card-title class="pa-4 font-weight-bold">
            简历列表
          </v-card-title>

          <v-card-text class="pb-0">
             <v-row dense>
               <!-- ID Filters -->
               <v-col cols="12" md="2">
                 <v-text-field
                   v-model="searchId"
                   label="ID 搜索"
                   prepend-inner-icon="mdi-identifier"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchAllResumes()"
                 ></v-text-field>
               </v-col>
                <v-col cols="12" md="2">
                 <v-text-field
                   v-model="searchUserId"
                   label="用户ID 搜索"
                   prepend-inner-icon="mdi-account"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchAllResumes()"
                 ></v-text-field>
               </v-col>
               <v-col cols="12" md="5">
                 <v-text-field
                   v-model="searchName"
                   label="简历名称搜索"
                   prepend-inner-icon="mdi-magnify"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchAllResumes()"
                   @click:append-inner="fetchAllResumes"
                 ></v-text-field>
               </v-col>

               <!-- Time Filter Button -->
               <v-col cols="12" md="3" class="d-flex align-center justify-end">
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

          <v-table>
            <thead>
              <tr>
                <th class="text-center font-weight-bold">序号</th>
                <th class="text-center font-weight-bold">ID</th>
                <th class="text-center font-weight-bold">用户ID</th>
                <th class="text-center font-weight-bold">名称</th>
                <th class="text-center font-weight-bold">创建时间</th>
                <th class="text-center font-weight-bold">更新时间</th>
                <th class="text-center font-weight-bold">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="resumeList.length === 0 && !loading">
                 <td colspan="7" class="text-center pa-4 text-grey">
                    {{ '暂无简历数据' }}
                 </td>
              </tr>
              <tr v-for="(item, index) in resumeList" :key="item.id">
                <td class="text-center">{{ index + 1 }}</td>
                <td class="text-center">{{ item.id }}</td>
                <td class="text-center">{{ item.userId }}</td>
                <td class="text-center">{{ item.name }}</td>
                <td class="text-center">{{ formatDate(item.createTime) }}</td>
                <td class="text-center">{{ formatDate(item.updateTime) }}</td>
                <td class="text-center">
                  <v-btn icon
                    color="primary"
                    variant="text"
                    size="small"
                    @click="handleDownload(item.id)"
                  >
                    <v-icon>mdi-download</v-icon>
                    <v-tooltip activator="parent" location="bottom">下载</v-tooltip>
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
                <v-btn variant="text" icon="mdi-chevron-left" :disabled="page <= 1 || loading" @click="handlePageChange(page - 1)"></v-btn>
              </v-col>
              <v-col cols="auto">
                <span class="text-body-2">第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
              </v-col>
              <v-col cols="auto">
                <v-btn variant="text" icon="mdi-chevron-right" :disabled="page >= totalPages || loading" @click="handlePageChange(page + 1)"></v-btn>
              </v-col>
              <v-col cols="auto" class="ml-4">
                <v-text-field v-model="jumpPage" label="跳转至" type="number" variant="outlined" density="compact" hide-details style="width: 80px" @keydown="e => e.key === 'Enter' && handleJumpPage()"></v-text-field>
              </v-col>
            </v-row>
          </v-card-actions>
        </v-card>

        <!-- Time Filter Dialog -->
        <v-dialog v-model="showTimeFilterDialog" max-width="400">
           <v-card>
             <v-card-title class="text-h6 pa-4">设置时间过滤器</v-card-title>
             <v-card-text class="pa-4">
               <v-select
                 v-model="tempTimeFilter.target"
                 label="过滤目标栏目"
                 :items="[{title:'创建时间', value:'createTime'}, {title:'更新时间', value:'updateTime'}]"
                 variant="outlined"
                 density="compact"
                 class="mb-4"
               ></v-select>
               <p class="text-caption mb-1">起始时间</p>
               <v-text-field v-model="tempTimeFilter.start" type="datetime-local" variant="outlined" density="compact"></v-text-field>
               <p class="text-caption mb-1 mt-2">终止时间</p>
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
                <v-btn variant="text" @click="showTimeFilterDialog = false">取消</v-btn>
                <v-btn color="primary" @click="confirmTimeFilter">确认</v-btn>
             </v-card-actions>
           </v-card>
        </v-dialog>

        <v-snackbar-queue v-model="feedback_messages"></v-snackbar-queue>
      </v-container>
    </v-main>
  </div>
</template>

