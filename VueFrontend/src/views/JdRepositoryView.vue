<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request.js'
import {formatDate, formatToISO} from "@/utils/tools.js";

const router = useRouter()
const jdList = ref([])
const loading = ref(false)
const feedback_messages = ref([])

// Pagination
// Pagination
const page = ref(1)
const size = ref(10)
const totalPages = ref(0)
const jumpPage = ref('')

// Filters
const searchId = ref('')
const searchKeyword = ref('')

// Salary Filter
const showSalaryFilterDialog = ref(false)
const salaryFilter = ref({
    active: false,
    min: '',
    max: '',
    period: '月'
})
const tempSalaryFilter = ref({
    min: '',
    max: '',
    period: '月'
})
const salaryError = ref(false)

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

const openSalaryFilterDialog = () => {
    if (salaryFilter.value.active) {
        tempSalaryFilter.value = { ...salaryFilter.value }
    } else {
        tempSalaryFilter.value = { min: '', max: '', period: '月' }
    }
    salaryError.value = false
    showSalaryFilterDialog.value = true
}

const confirmSalaryFilter = () => {
    if (!tempSalaryFilter.value.min && !tempSalaryFilter.value.max) {
        salaryFilter.value = { active: false, min: '', max: '', period: '月' }
        showSalaryFilterDialog.value = false
        fetchAllJds() // refresh
        return
    }
    if (tempSalaryFilter.value.min && tempSalaryFilter.value.max) {
        if (parseFloat(tempSalaryFilter.value.max) < parseFloat(tempSalaryFilter.value.min)) {
            salaryError.value = true
            return
        }
    }
    salaryError.value = false
    // Ensure period
    if(!tempSalaryFilter.value.period) tempSalaryFilter.value.period = '月'

    // Check if empty again just in case validation logic allows partial
    if (!tempSalaryFilter.value.min && !tempSalaryFilter.value.max) {
        // ...
    }

    salaryFilter.value = { ...tempSalaryFilter.value, active: true }
    showSalaryFilterDialog.value = false
    fetchAllJds() // refresh
}

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
       fetchAllJds() // refresh
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
   fetchAllJds() // refresh
}

// REMOVED filteredJdList computed

onMounted(() => {
  fetchAllJds()
})

const fetchAllJds = async () => {
  loading.value = true
  try {
    const filter = {
        id: searchId.value ? parseInt(searchId.value) : null,
        jdKeyword: searchKeyword.value || null,
        min_salary: salaryFilter.value.active ? parseFloat(salaryFilter.value.min) : null,
        max_salary: salaryFilter.value.active ? parseFloat(salaryFilter.value.max) : null,
        period: salaryFilter.value.active ? salaryFilter.value.period : null,
        startCreateTime: (timeFilter.value.active && timeFilter.value.target === 'createTime') ? (timeFilter.value.start ? formatToISO(timeFilter.value.start) : null) : null,
        endCreateTime: (timeFilter.value.active && timeFilter.value.target === 'createTime') ? (timeFilter.value.end ? formatToISO(timeFilter.value.end) : null) : null,
        startUpdateTime: (timeFilter.value.active && timeFilter.value.target === 'updateTime') ? (timeFilter.value.start ? formatToISO(timeFilter.value.start) : null) : null,
        endUpdateTime: (timeFilter.value.active && timeFilter.value.target === 'updateTime') ? (timeFilter.value.end ? formatToISO(timeFilter.value.end) : null) : null,
    }

    const res = await request.post('/jd/list-all/page', filter, {
      params: { page: page.value, size: size.value }
    })
    if (res.code === 200) {
      jdList.value = res.data.records
      totalPages.value = res.data.pages
      feedback_messages.value.push({
        text: `已加载第 ${page.value} 页`,
        timeout: 1500,
        color: 'success'
      })
    } else {
      feedback_messages.value.push({
        text: '获取职位列表失败! ' + (res.message || ''),
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Failed to fetch JDs:', error)
    feedback_messages.value.push({
      text: '获取职位列表失败! 请检查网络连接。',
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
        fetchAllJds()
    }
}

const handleJumpPage = () => {
    const p = parseInt(jumpPage.value)
    if (!isNaN(p) && p >= 1 && p <= totalPages.value) {
        page.value = p
        fetchAllJds()
        jumpPage.value = ''
    } else {
         feedback_messages.value.push({ text: '请输入有效的页码', timeout: 2000, color: 'warning' })
    }
}

const handleView = (id, jdName) => {
  const route = router.resolve({ name: 'jd-detail', params: { id }, query: { jdName: jdName } })
  window.open(route.href, '_blank')
}
</script>

<template>
  <div class="fill-height bg-grey-lighten-5">
    <v-app-bar color="white" elevation="2">
      <v-app-bar-title class="font-weight-bold text-black">JD 仓库</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container>
        <v-card class="elevation-1">
          <v-card-title class="pa-4 font-weight-bold">
            JD 列表
          </v-card-title>

          <v-card-text class="pb-0">
             <v-row dense>
               <!-- ID and Keyword Search -->
               <v-col cols="12" md="2">
                 <v-text-field
                   v-model="searchId"
                   label="ID 搜索"
                   prepend-inner-icon="mdi-identifier"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchAllJds()"
                 ></v-text-field>
               </v-col>
               <v-col cols="12" md="4">
                 <v-text-field
                   v-model="searchKeyword"
                   label="关键词搜索 (名称/公司/地点)"
                   prepend-inner-icon="mdi-magnify"
                   variant="outlined"
                   density="compact"
                   hide-details
                   @keydown="e => e.key === 'Enter' && fetchAllJds()"
                   @click:append-inner="fetchAllJds"
                 ></v-text-field>
               </v-col>

                <!-- Salary Filter Button -->
                <v-col cols="12" md="4" class="d-flex align-center justify-center">
                    <v-btn
                        :color="salaryFilter.active ? 'primary' : 'default'"
                        :variant="salaryFilter.active ? 'flat' : 'outlined'"
                        prepend-icon="mdi-cash"
                        @click="openSalaryFilterDialog"
                        block
                    >
                        薪资过滤
                    </v-btn>
                </v-col>

               <!-- Time Filter Button -->
               <v-col cols="12" md="2" class="d-flex align-center justify-end">
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
             <!-- Removed inline error -->
          </v-card-text>

          <v-table>
            <thead>
              <tr>
                <th class="text-center font-weight-bold">序号</th>
                <th class="text-center font-weight-bold">ID</th>
                <th class="text-center font-weight-bold">名称</th>
                <th class="text-center font-weight-bold">公司</th>
                <th class="text-center font-weight-bold">工作地点</th>
                <th class="text-center font-weight-bold">薪资</th>
                <th class="text-center font-weight-bold">发布时间</th>
                <th class="text-center font-weight-bold">更新时间</th>
                <th class="text-center font-weight-bold">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="jdList.length === 0 && !loading">
                 <td colspan="9" class="text-center pa-4 text-grey">
                    {{ '暂无JD数据' }}
                 </td>
              </tr>
              <tr v-for="(item, index) in jdList" :key="item.id">
                <td class="text-center">{{ index + 1 }}</td>
                <td class="text-center">{{ item.id }}</td>
                <td class="text-center">{{ item.name }}</td>
                <td class="text-center">{{ item.company }}</td>
                <td class="text-center">{{ item.location }}</td>
                <td class="text-center">{{ item.salary }}</td>
                <td class="text-center">{{ formatDate(item.createTime) }}</td>
                <td class="text-center">{{ formatDate(item.updateTime) }}</td>
                <td class="text-center">
                  <v-btn icon
                    color="primary"
                    variant="text"
                    size="small"
                    @click="handleView(item.id, item.name)"
                  >
                    <v-icon>mdi-file-document</v-icon>
                    <v-tooltip activator="parent" location="bottom">查看</v-tooltip>
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
                 :items="[{title:'发布时间', value:'createTime'}, {title:'更新时间', value:'updateTime'}]"
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
               <v-btn color="grey-darken-1" variant="text" @click="showTimeFilterDialog = false">取消</v-btn>
               <v-btn color="primary" variant="flat" @click="confirmTimeFilter">确认</v-btn>
             </v-card-actions>
           </v-card>
        </v-dialog>

        <!-- Salary Filter Dialog -->
        <v-dialog v-model="showSalaryFilterDialog" max-width="500">
           <v-card>
             <v-card-title class="text-h6 pa-4">设置薪资过滤器</v-card-title>
             <v-card-text class="pa-4">
                <v-row dense>
                    <v-col cols="12" md="4">
                        <v-text-field v-model="tempSalaryFilter.min" label="最低薪资" type="number" variant="outlined" density="compact"></v-text-field>
                    </v-col>
                    <v-col cols="12" md="4">
                        <v-text-field v-model="tempSalaryFilter.max" label="最高薪资" type="number" variant="outlined" density="compact"></v-text-field>
                    </v-col>
                    <v-col cols="12" md="4">
                        <v-select v-model="tempSalaryFilter.period" label="发放周期" :items="['日', '月', '年']" variant="outlined" density="compact"></v-select>
                    </v-col>
                </v-row>
                <p v-if="salaryError" class="text-red text-caption">最高薪资不能低于最低薪资</p>
             </v-card-text>
             <v-card-actions class="pa-4 justify-end">
               <v-btn color="grey-darken-1" variant="text" @click="showSalaryFilterDialog = false">取消</v-btn>
               <v-btn color="primary" variant="flat" @click="confirmSalaryFilter">确认</v-btn>
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
