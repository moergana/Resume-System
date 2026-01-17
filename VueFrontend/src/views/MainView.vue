<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ROLE_MAP, CANDIDATE_NUMBER, RECRUITER_NUMBER } from "@/utils/constants.js"
import request from '@/utils/request.js'
import { formatDate, formatToISO } from "@/utils/tools.js";

const router = useRouter()
const user = ref({
  username: '',
  role: ''
})

// Resume data for Candidate
const resumeList = ref([])
const loading = ref(false)
const showUploadDialog = ref(false)
const uploadFile = ref(null)
const uploading = ref(false)
const snackbar_messages = ref([])

// Resume Pagination
const page = ref(1)
const size = ref(10)
const totalPages = ref(0)
const jumpPage = ref('')

// Resume List Filters
const searchResumeName = ref('')
const showTimeFilterDialog = ref(false)
const timeFilter = ref({
  active: false,
  target: 'createTime', // 'createTime' or 'updateTime'
  start: '',
  end: ''
})
// Temporary state for the dialog
const tempTimeFilter = ref({
  target: 'createTime',
  start: '',
  end: ''
})

const timeFilterError = ref(false)

// Delete dialog state
const showDeleteDialog = ref(false)
const resumeToDelete = ref(null)
const deleting = ref(false)

// Analysis state
const isSelectingResume = ref(false)
const selectedResumeId = ref(null)
const showJdInputDialog = ref(false)
const inputJdId = ref('')
const analyzing = ref(false)

// Added for Full Library Match
const selectionMode = ref('ANALYSIS') // 'ANALYSIS' or 'MATCH'
const showMatchConfirmDialog = ref(false)
const selectedResume = ref(null)

// Global click handler to cancel resume selection if clicking outside
const onGlobalClick = (e) => {
  if (!isSelectingResume.value) return

  // ignore if clicking on resume row (handled by row click)
  if (e.target.closest('.resume-row-select')) return
  // ignore if clicking on snackbar or its children
  if (e.target.closest('.v-snackbar')) return

  // also, we should check if the click target is the "指定分析" button itself?
  // But the startResumeSelection sets isSelectingResume=true.
  // We attach listener with a delay or verify timestamp?
  // No, using watch with setTimeout(0) ensures the current click (which triggered the start) doesn't trigger this listener.

  cancelResumeSelection()
}

// Watch for selection mode changes to add/remove global click listener
watch(isSelectingResume, (val) => {
  if (val) {
     setTimeout(() => {
       window.addEventListener('click', onGlobalClick)
     }, 0)
  } else {
     window.removeEventListener('click', onGlobalClick)
  }
})

onMounted(() => {
  const storedUser = localStorage.getItem('currentUser')
  if (storedUser) {
    user.value = JSON.parse(storedUser)
    if (user.value.role === CANDIDATE_NUMBER) {
      fetchResumes()
    }
    else if (user.value.role === RECRUITER_NUMBER) {
      fetchPublishedJds()
    }
  } else {
    // If no user info found, redirect to login
    router.push('/login')
  }
})

const openTimeFilterDialog = () => {
  // Initialize temp with current active filter or defaults
  if (timeFilter.value.active) {
    tempTimeFilter.value = { ...timeFilter.value }
  } else {
    tempTimeFilter.value = {
      target: 'createTime',
      start: '',
      end: ''
    }
  }
  timeFilterError.value = false
  showTimeFilterDialog.value = true
}

const confirmTimeFilter = () => {
  // If inputs are empty, it means user wants to clear/reset?
  // Requirement: "If user clears inputs... stop time filtering"
  if (!tempTimeFilter.value.start && !tempTimeFilter.value.end) {
    timeFilter.value = {
      active: false,
      target: 'createTime',
      start: '',
      end: ''
    }
    showTimeFilterDialog.value = false
    fetchResumes() // Trigger fetch with new filter (cleared)
    return
  }

  // Validation: end shouldn't be less than start
  if (tempTimeFilter.value.start && tempTimeFilter.value.end) {
    if (new Date(tempTimeFilter.value.end) < new Date(tempTimeFilter.value.start)) {
      timeFilterError.value = true
      return
    }
  }

  timeFilterError.value = false
  timeFilter.value = {
    ...tempTimeFilter.value,
    active: true
  }
  showTimeFilterDialog.value = false
  fetchResumes() // Trigger fetch with new filter
}

// REMOVED filteredResumeList computed property as filtering is now server-side

// --- Recruiter Logic ---

const jdList = ref([])
const jdLoading = ref(false)
const isSelectingJd = ref(false)
const selectedJd = ref(null)
const selectedJdId = ref(null)

// JD Pagination
const jdPage = ref(1)
const jdSize = ref(10)
const jdTotalPages = ref(0)
const jdJumpPage = ref('')

// Analysis (Recruiter)
const showResumeInputDialog = ref(false) // Dialog for entering Resume ID
const inputResumeId = ref('')
const showJdMatchConfirmDialog = ref(false) // For full library match

// Publish JD
const showPublishJdDialog = ref(false)
const publishMode = ref('manual') // 'manual' or 'upload'
const jdForm = ref({
    title: '', company: '', location: '', salary: '',
    description: '', requirements: '', bonus: ''
})
const jdUploadFile = ref(null)
const publishing = ref(false) // renamed from publishLoading to avoid conflict if any
const jdFormValid = ref(false)

const jdRules = {
    required: value => !!value || '此项必填'
}

// Delete JD
const showJdDeleteDialog = ref(false)
const jdToDelete = ref(null)
const jdDeleting = ref(false)

// JD Filters
const searchJdId = ref('')
const searchJdKeyword = ref('')
// Refactored Salary Filter
const showJdSalaryFilterDialog = ref(false)
const jdSalaryFilter = ref({
    active: false,
    min: '',
    max: '',
    period: '月'
})
const tempJdSalaryFilter = ref({
    min: '',
    max: '',
    period: '月'
})
const jdSalaryFilterError = ref(false)

const jdTimeFilter = ref({ active: false, target: 'createTime', start: '', end: '' })
const showJdTimeFilterDialog = ref(false)
const tempJdTimeFilter = ref({ target: 'createTime', start: '', end: '' })
const jdTimeFilterError = ref(false)

// Function to open salary filter dialog
const openJdSalaryFilterDialog = () => {
    if (jdSalaryFilter.value.active) {
        tempJdSalaryFilter.value = { ...jdSalaryFilter.value }
    } else {
        tempJdSalaryFilter.value = { min: '', max: '', period: '月' }
    }
    showJdSalaryFilterDialog.value = true
}

// Function to confirm salary filter
const confirmJdSalaryFilter = () => {
    // Check if cleared
    if (!tempJdSalaryFilter.value.min && !tempJdSalaryFilter.value.max) {
        jdSalaryFilter.value = { active: false, min: '', max: '', period: '月' }
        showJdSalaryFilterDialog.value = false
        fetchPublishedJds()
        return
    }
    // Validation
    if (!tempJdSalaryFilter.value.min || !tempJdSalaryFilter.value.max || !tempJdSalaryFilter.value.period) {
         // Requirement says: "Must fill all or none"
         // If partial, perhaps show error or just ignore.
         // Assuming consistent with requirement: "User must fill all three... or all empty"
         // If mixed, we prevent confirm?
         // Let's assume validation error if mixed.
         // Actually "If user inputs three... button changes color".
         // I'll enforce all required if any is filled.
         if (tempJdSalaryFilter.value.min || tempJdSalaryFilter.value.max) {
             // If any salary entered, must complete all
             if (!tempJdSalaryFilter.value.min || !tempJdSalaryFilter.value.max || !tempJdSalaryFilter.value.period) {
                 // But wait, period has default. So check min/max.
                 // Just check if both min and max are present
                 // Also check Max >= Min
             }
         }
    }
    if (tempJdSalaryFilter.value.min && tempJdSalaryFilter.value.max) {
        if (parseFloat(tempJdSalaryFilter.value.max) < parseFloat(tempJdSalaryFilter.value.min)) {
            jdSalaryFilterError.value = true
            return
        }
    }
    jdSalaryFilterError.value = false

    // If we have values, activate
    // Make sure period is set
    if (!tempJdSalaryFilter.value.period) tempJdSalaryFilter.value.period = '月'

    if (tempJdSalaryFilter.value.min && tempJdSalaryFilter.value.max) {
         jdSalaryFilter.value = { ...tempJdSalaryFilter.value, active: true }
    } else {
         // If empty/partial considered as clear? Requirement says "All must be input... or all empty".
         // Use active=false if not full
         jdSalaryFilter.value = { active: false, min: '', max: '', period: '月' }
    }

    showJdSalaryFilterDialog.value = false
    fetchPublishedJds()
}

// Refactored Post New Job state
const jdFormSalaryInput = ref({
    min: '',
    max: '',
    period: '月'
})
const jdFormSalaryError = ref(false)

// REMOVED filteredJdList computed property

const fetchPublishedJds = async () => {
    jdLoading.value = true
    try {
        // Construct FilterCondition
        const filter = {
             keyword: null, // Not used here? Ah, logic check.
             // Mapping Recruiter JD List Filters:
             // id -> searchJdId
             // jdKeyword -> searchJdKeyword
             // min_salary, max_salary, period -> jdSalaryFilter
             // start/end -> jdTimeFilter
             id: searchJdId.value ? parseInt(searchJdId.value) : null,
             userId: user.value.id || null, // Filter by my own JDs
             jdKeyword: searchJdKeyword.value || null,
             min_salary: jdSalaryFilter.value.active ? parseFloat(jdSalaryFilter.value.min) : null,
             max_salary: jdSalaryFilter.value.active ? parseFloat(jdSalaryFilter.value.max) : null,
             period: jdSalaryFilter.value.active ? jdSalaryFilter.value.period : null,
             startCreateTime: (jdTimeFilter.value.active && jdTimeFilter.value.target === 'createTime') ? formatToISO(jdTimeFilter.value.start) : null,
             endCreateTime: (jdTimeFilter.value.active && jdTimeFilter.value.target === 'createTime') ? formatToISO(jdTimeFilter.value.end) : null,
             startUpdateTime: (jdTimeFilter.value.active && jdTimeFilter.value.target === 'updateTime') ? formatToISO(jdTimeFilter.value.start) : null,
             endUpdateTime: (jdTimeFilter.value.active && jdTimeFilter.value.target === 'updateTime') ? formatToISO(jdTimeFilter.value.end) : null,
        }

        // Fetch Page Data with POST
        const res = await request.post('/jd/list/page', filter, {
          params: { page: jdPage.value, size: jdSize.value }
        })
        if (res && res.code === 200) {
            jdList.value = res.data.records
            jdTotalPages.value = res.data.pages
            // No need to fetch total pages separately

            snackbar_messages.value.push({
                text: `已加载第 ${jdPage.value} 页`,
                timeout: 1500,
                color: 'success'
            })
        } else {
             if (res) console.error(res.message)
             snackbar_messages.value.push({ text: '获取已发布职位列表失败' + (res && res.message ? `: ${res.message}` : ''), color: 'error', timeout: 3000 })
        }
    } catch (error) {
        console.error("Fetch JD error", error)
        snackbar_messages.value.push({ text: '获取已发布职位列表失败', color: 'error', timeout: 3000 })
    } finally {
        jdLoading.value = false
    }
}

// JD Actions
const handleJdView = (id, jdName) => {
    const route = router.resolve({ name: 'jd-detail', params: { id }, query: { jdName: jdName } })
    window.open(route.href, '_blank')
}

const handleJdDownload = async (id) => {
    try {
        const res = await request.get(`/jd/download/${id}`, { responseType: 'blob' })
        // Check for 404 handled by request wrapper?
        // request.js usually returns response data.
        // If 404, it might throw error or return error object.
        // Assuming standard behavior or blob.
        if (res instanceof Blob) {
             const url = window.URL.createObjectURL(res)
             const link = document.createElement('a')
             link.href = url
             link.setAttribute('download', `jd_${id}.pdf`) // simplistic name
             document.body.appendChild(link)
             link.click()
             document.body.removeChild(link)
             window.URL.revokeObjectURL(url)
        } else {
             // Maybe JSON error
             // If backend returns ResponseEntity.notFound().build(), frontend often gets 404 error thrown.
        }
    } catch (error) {
        // Check if 404
        if (error.response && error.response.status === 404) {
             snackbar_messages.value.push({ text: '该职位没有上传过文件', color: 'warning', timeout: 3000 })
        } else {
             snackbar_messages.value.push({ text: '下载失败', color: 'error', timeout: 3000 })
        }
    }
}

const prepareJdDelete = (item) => {
    jdToDelete.value = item
    showJdDeleteDialog.value = true
}

const handleJdDelete = async () => {
  if (!jdToDelete.value) return
  jdDeleting.value = true
  try {
    const res = await request.delete(`/jd/${jdToDelete.value.id}`)
    if (res && res.code === 200) {
      snackbar_messages.value.push({ text: '职位删除成功', color: 'success', timeout: 3000 })
      await fetchPublishedJds() // refresh list
    } else {
      snackbar_messages.value.push({ text: '删除失败: ' + (res.message || '未知错误'), color: 'error', timeout: 3000 })
    }
  } catch (error) {
    console.error('Delete JD error', error)
    snackbar_messages.value.push({ text: '删除请求失败', color: 'error', timeout: 3000 })
  } finally {
    jdDeleting.value = false
    showJdDeleteDialog.value = false
    jdToDelete.value = null
  }
}

// Publish JD
const handlePublishJd = async () => {
    publishing.value = true
    try {
        if (publishMode.value === 'manual') {
            // Construct salary string
            const salaryStr = `${parseFloat(jdFormSalaryInput.value.min).toFixed(2)} - ${parseFloat(jdFormSalaryInput.value.max).toFixed(2)} 元 / ${jdFormSalaryInput.value.period}`

            const payload = {
                ...jdForm.value,
                salary: salaryStr
            }

            const res = await request.post('/jd/upload/info', payload)
            if (res.code === 200) {
                snackbar_messages.value.push({ text: '职位信息发布成功', color: 'success', timeout: 3000 })
                showPublishJdDialog.value = false
                // reset form
                jdForm.value = { title: '', company: '', location: '', salary: '', description: '', requirements: '', bonus: '' }
                jdFormSalaryInput.value = { min: '', max: '', period: '月' }
                fetchPublishedJds()
            } else {
                snackbar_messages.value.push({ text: res.message || '发布失败', color: 'error', timeout: 3000 })
            }
        } else {
            // Upload
            if (!jdUploadFile.value) return
            const file = Array.isArray(jdUploadFile.value) ? jdUploadFile.value[0] : jdUploadFile.value
            const formData = new FormData()
            formData.append('jd', file)
            const res = await request.post('/jd/upload/file', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
            if (res.code === 200) {
                snackbar_messages.value.push({ text: '职位文件上传成功', color: 'success', timeout: 3000 })
                showPublishJdDialog.value = false
                jdUploadFile.value = null
                fetchPublishedJds()
            } else {
                snackbar_messages.value.push({ text: res.message || '上传失败', color: 'error', timeout: 3000 })
            }
        }
    } catch(e) {
        snackbar_messages.value.push({ text: '发布请求出错', color: 'error', timeout: 3000 })
    } finally {
        publishing.value = false
    }
}

// Analysis Selection (Recruiter)
const startJdSelection = (mode = 'ANALYSIS') => {
    if (jdList.value.length === 0) {
        snackbar_messages.value.push({ text: '暂无职位可供分析', color: 'warning', timeout: 3000 })
        return
    }
    selectionMode.value = mode
    isSelectingJd.value = true
    // Add global click listener similar to resume selection
     setTimeout(() => {
       window.addEventListener('click', onGlobalClickJd)
     }, 0)
}

const cancelJdSelection = () => {
    isSelectingJd.value = false
    selectedJdId.value = null
    selectedJd.value = null
    window.removeEventListener('click', onGlobalClickJd)
}

const onGlobalClickJd = (e) => {
  if (!isSelectingJd.value) return
  if (e.target.closest('.jd-row-select')) return
  if (e.target.closest('.v-snackbar')) return
  cancelJdSelection()
}

const selectJd = (item) => {
    if (!isSelectingJd.value) return
    selectedJd.value = item
    selectedJdId.value = item.id
    isSelectingJd.value = false
    window.removeEventListener('click', onGlobalClickJd)

    if (selectionMode.value === 'ANALYSIS') {
        inputResumeId.value = ''
        showResumeInputDialog.value = true
    } else if (selectionMode.value === 'MATCH') {
        showJdMatchConfirmDialog.value = true
    }
}

const openResumeRepository = () => {
    const route = router.resolve({ name: 'resume-repository' })
    window.open(route.href, '_blank')
}

// Perform Analysis (Recruiter)
const confirmRecruiterAnalysis = async () => {
    if (!inputResumeId.value) return
    analyzing.value = true
    try {
        const res = await request.get('/resumeAnalysis/resume_jd_differ', {
            params: {
                resume_id: inputResumeId.value,
                jd_id: selectedJdId.value
            }
        })
        if (res.code === 200) {
            snackbar_messages.value.push({ text: '分析请求已提交', color: 'success', timeout: 3000 })
            showResumeInputDialog.value = false
        } else {
            snackbar_messages.value.push({ text: res.message || '请求失败', color: 'error', timeout: 3000 })
        }
    } catch (e) {
        snackbar_messages.value.push({ text: '请求出错', color: 'error', timeout: 3000 })
    } finally {
        analyzing.value = false
    }
}

const confirmRecruiterMatch = async () => {
    if (!selectedJdId.value) return
    analyzing.value = true
    try {
        const res = await request.get('/resumeAnalysis/resume_match', {
            params: { jd_id: selectedJdId.value }
        })
        if (res.code === 200) {
            snackbar_messages.value.push({ text: '全库匹配请求已提交', color: 'success', timeout: 3000 })
            showJdMatchConfirmDialog.value = false
        } else {
            snackbar_messages.value.push({ text: res.message || '请求失败', color: 'error', timeout: 3000 })
        }
    } catch (e) {
        snackbar_messages.value.push({ text: '请求出错', color: 'error', timeout: 3000 })
    } finally {
        analyzing.value = false
    }
}

// JD Time Filter
const openJdTimeFilterDialog = () => {
   // Implementation similar to Resume Time Filter
   // ...
   showJdTimeFilterDialog.value = true
   if (jdTimeFilter.value.active) {
       tempJdTimeFilter.value = {...jdTimeFilter.value}
   } else {
       tempJdTimeFilter.value = { target: 'createTime', start: '', end: '' }
   }
}
const confirmJdTimeFilter = () => {
    // ...
    if (!tempJdTimeFilter.value.start && !tempJdTimeFilter.value.end) {
        jdTimeFilter.value = { active: false, target: 'createTime', start: '', end: '' }
        showJdTimeFilterDialog.value = false
        fetchPublishedJds() // Trigger fetch
        return
    }
    if (tempJdTimeFilter.value.start && tempJdTimeFilter.value.end) {
        if (new Date(tempJdTimeFilter.value.end) < new Date(tempJdTimeFilter.value.start)) {
             jdTimeFilterError.value = true; return;
        }
    }
    jdTimeFilter.value = {...tempJdTimeFilter.value, active: true }
    showJdTimeFilterDialog.value = false
    fetchPublishedJds() // Trigger fetch
}

/*
 * 获取当前登录的用户上传过的所有简历记录列表
 */
const fetchResumes = async () => {
  loading.value = true
  try {
    const filter = {
        resumeKeyword: searchResumeName.value || null,
        userId: user.value.id || null, // Assuming user.value has id
        startCreateTime: (timeFilter.value.active && timeFilter.value.target === 'createTime') ? formatToISO(timeFilter.value.start) : null,
        endCreateTime: (timeFilter.value.active && timeFilter.value.target === 'createTime') ? formatToISO(timeFilter.value.end) : null,
        startUpdateTime: (timeFilter.value.active && timeFilter.value.target === 'updateTime') ? formatToISO(timeFilter.value.start) : null,
        endUpdateTime: (timeFilter.value.active && timeFilter.value.target === 'updateTime') ? formatToISO(timeFilter.value.end) : null,
    }

    const res = await request.post('/resume/list/page', filter, {
      params: { page: page.value, size: size.value }
    })
    // 如果返回结果为空，说明可能是未登录状态，跳转到登录页面
    if (res === null || res === undefined) {
      if (res === null) {
        console.error("fetchResumes function returns null")
      } else {
        console.error('fetchResumes function returns null or undefined')
      }
      await router.push('/login')
      return
    }
    // 如果返回的结果中状态码为200，说明请求成功，更新简历列表
    if (res.code === 200) {
      resumeList.value = res.data.records
      totalPages.value = res.data.pages
      snackbar_messages.value.push({
        text: `已加载第 ${page.value} 页`,
        timeout: 1500,
        color: 'success'
      })
    } else {
      console.error(res.message)
      snackbar_messages.value.push({
        text: '获取简历列表失败! ' + (res.message ? `: ${res.message}` : ''),
        timeout: 3000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Failed to fetch resumes:', error)
    snackbar_messages.value.push({
      text: '获取简历列表失败! 请检查网络连接。',
      timeout: 3000,
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

// REMOVED fetchTotalPages

/*
 * 开始简历选择模式
 */
const startResumeSelection = (mode = 'ANALYSIS') => {
  if (resumeList.value.length === 0) {
    snackbar_messages.value.push({
      text: '暂无简历可供分析，请先上传简历',
      timeout: 3000,
      color: 'warning',
    })
    return
  }
  selectionMode.value = mode
  isSelectingResume.value = true
}

/*
 * 取消简历选择模式
 */
const cancelResumeSelection = () => {
  isSelectingResume.value = false
  selectedResumeId.value = null
  selectedResume.value = null
}

/*
 * 选择简历
 */
const selectResume = (item) => {
  if (!isSelectingResume.value) return

  selectedResumeId.value = item.id
  selectedResume.value = item
  isSelectingResume.value = false // Exit selection mode

  if (selectionMode.value === 'ANALYSIS') {
      inputJdId.value = '' // reset input
      showJdInputDialog.value = true
  } else if (selectionMode.value === 'MATCH') {
      showMatchConfirmDialog.value = true
  }
}

/*
 * 跳转JD仓库
 */
const openJdRepository = () => {
  const route = router.resolve({ name: 'jd-repository' })
  window.open(route.href, '_blank')
}

/*
 * 确认开始分析
 */
const confirmAnalysis = async () => {
  if (!inputJdId.value) return

  analyzing.value = true
  try {
    const res = await request.get('/resumeAnalysis/resume_advice', {
      params: {
        resume_id: selectedResumeId.value,
        jd_id: inputJdId.value
      }
    })

    if (res.code === 200) {
      snackbar_messages.value.push({
        text: '分析请求已提交',
        timeout: 3000,
        color: 'success',
      })
      showJdInputDialog.value = false
    } else {
      snackbar_messages.value.push({
        text: '分析请求失败! ' + (res.message || ''),
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Analysis error:', error)
    snackbar_messages.value.push({
      text: '分析请求发生错误',
      timeout: 4000,
      color: 'error',
    })
  } finally {
    analyzing.value = false
  }
}

/*
 * 确认开始全库匹配
 */
const confirmMatch = async () => {
  if (!selectedResumeId.value) return

  analyzing.value = true
  try {
    const res = await request.get('/resumeAnalysis/jd_match', {
      params: {
        resume_id: selectedResumeId.value
      }
    })

    if (res.code === 200) {
      snackbar_messages.value.push({
        text: '全库匹配请求已提交',
        timeout: 3000,
        color: 'success',
      })
      showMatchConfirmDialog.value = false
    } else {
      snackbar_messages.value.push({
        text: '全库匹配请求失败! ' + (res.message || ''),
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Match error:', error)
    snackbar_messages.value.push({
      text: '全库匹配请求发生错误',
      timeout: 4000,
      color: 'error',
    })
  } finally {
    analyzing.value = false
  }
}

/*
 * 简历下载功能
 */
const handleDownload = async (id) => {
  try {
    const res = await request.post(`/resume/download/${id}`, {}, {
      responseType: 'blob'
    })

    // Check if it is a Blob
    if (res instanceof Blob) {
      if (res.type === 'application/json') {
          // If server returned JSON error as blob
          const text = await res.text()
          const json = JSON.parse(text)
          snackbar_messages.value.push({
            text: json.message || '下载失败',
            timeout: 3000,
            color: 'error',
          })
          return
      }

      const url = window.URL.createObjectURL(res)
      const link = document.createElement('a')
      link.href = url
      // Assuming PDF for now as per upload restriction, though backend might send other types
      // The name should ideally come from headers, but simplistic approach:
      link.setAttribute('download', `resume_${id}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      snackbar_messages.value.push({
        text: '下载已开始',
        timeout: 3000,
        color: 'success',
      })
    } else {
      // Unexpected response
      console.error('Unexpected download response', res)
    }

  } catch (error) {
    console.error('Download error:', error)
    snackbar_messages.value.push({
      text: '下载请求发生错误',
      timeout: 3000,
      color: 'error',
    })
  }
}

/*
 * 准备删除简历
 */
const prepareDelete = (item) => {
  resumeToDelete.value = item
  showDeleteDialog.value = true
}

/*
 * 确认删除简历
 */
const handleDelete = async () => {
  if (!resumeToDelete.value) return

  deleting.value = true
  try {
    const res = await request.delete(`/resume/${resumeToDelete.value.id}`)
    if (res.code === 200) {
      snackbar_messages.value.push({
        text: '删除成功',
        timeout: 3000,
        color: 'success',
      })
      showDeleteDialog.value = false
      fetchResumes()
    } else {
      snackbar_messages.value.push({
        text: res.message || '删除失败',
        timeout: 3000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Delete error', error)
    snackbar_messages.value.push({
      text: '删除请求发生错误',
      timeout: 3000,
      color: 'error',
    })
  } finally {
    deleting.value = false
  }
}

/*
 * 简历文件上传功能
 */
const handleUpload = async () => {
  if (!uploadFile.value) return

  // Verify file type just in case, though accept attribute handles selection
  // Vuetify file input value might be array or single object depending on version/props
  // normalizing to single file
  const file = Array.isArray(uploadFile.value) ? uploadFile.value[0] : uploadFile.value

  if (!file) return

  const formData = new FormData()
  formData.append('resume', file)

  uploading.value = true
  try {
    const res = await request.post('/resume/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (res.code === 200) {
      // Success
      snackbar_messages.value.push({
        text: '简历上传成功',
        timeout: 3000,
        color: 'success',
      })
      showUploadDialog.value = false
      uploadFile.value = null // clear input
      fetchResumes() // refresh list
    } else {
      // alert(res.message || '上传失败')
      snackbar_messages.value.push({
        text: res.message || '上传失败',
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Upload error:', error)
    // alert('上传发生错误')
    snackbar_messages.value.push({
      text: '上传发生错误',
      timeout: 4000,
      color: 'error',
    })
  } finally {
    uploading.value = false
  }
}

/*
 * 用户退出登录功能
 * 当用户退出后，会清除cookie中的token和localStorage中的用户信息，并重定向到登录页面
 */
const handleLogout = () => {
  // Clear token from cookie
  document.cookie = 'token=; Max-Age=0; path=/'
  // Clear local storage
  localStorage.removeItem('currentUser')
  // Redirect to login
  router.push('/login')
}

const openChatBot = () => {
  window.open('http://localhost:7860/?analysis_id=', '_blank')
}
</script>

<template>
  <div class="fill-height">
    <v-app-bar color="white" elevation="2">
      <v-app-bar-title class="font-weight-bold text-black text-h5 ml-4">简历职位分析系统</v-app-bar-title>
      <v-spacer></v-spacer>

      <div class="mr-4">
        <v-menu min-width="200px" rounded>
          <template v-slot:activator="{ props }">
            <v-btn
              icon
              v-bind="props"
            >
              <v-avatar color="primary" size="40">
                <span class="text-h6 text-white">{{ user.username ? user.username.charAt(0).toUpperCase() : '' }}</span>
              </v-avatar>
            </v-btn>
          </template>
          <v-card>
            <v-card-text>
              <div class="mx-auto text-center">
                <v-avatar color="primary" class="mb-3">
                  <span class="text-white text-h5">
                    {{ user.username ? user.username.charAt(0).toUpperCase() : '' }}
                  </span>
                </v-avatar>
                <h3 class="mt-2 text-h6">
                  {{ user.username }}
                </h3>
                <p class="text-caption mt-1 text-medium-emphasis">
                  身份：{{ ROLE_MAP.get(user.role) }}
                </p>
                <v-divider class="my-3"></v-divider>
                <v-btn
                  color="error"
                  variant="flat"
                  block
                  rounded
                  @click="handleLogout"
                >
                  退出登录
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-menu>
      </div>
    </v-app-bar>

    <v-main class="bg-grey-lighten-4 fill-height">
      <v-container>
        <!-- Display for Job Seeker (Candidate) -->
        <template v-if="user.role === CANDIDATE_NUMBER">

          <!-- Analysis Component -->
          <v-card class="mb-6 elevation-1">
            <v-card-title class="text-h5 font-weight-bold pa-4">
              简历分析
            </v-card-title>
            <v-card-text class="pa-4">
              <div class="d-flex gap-4">
                <v-btn
                  :color="(isSelectingResume && selectionMode === 'ANALYSIS') ? 'light-blue-lighten-4' : 'primary'"
                  :variant="(isSelectingResume && selectionMode === 'ANALYSIS') ? 'tonal' : 'elevated'"
                  size="large"
                  prepend-icon="mdi-text-box-search-outline"
                  class="mr-4"
                  @click="startResumeSelection('ANALYSIS')"
                >
                  指定分析
                </v-btn>
                <v-btn
                  :color="(isSelectingResume && selectionMode === 'MATCH') ? 'light-blue-lighten-4' : 'secondary'"
                  :variant="(isSelectingResume && selectionMode === 'MATCH') ? 'tonal' : 'elevated'"
                  size="large"
                  prepend-icon="mdi-database-search-outline"
                  @click="startResumeSelection('MATCH')"
                >
                  全库匹配
                </v-btn>
                <v-btn
                  color="info"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-history"
                  class="ml-auto"
                  @click="$router.push('/analysis-history')"
                >
                  历史记录
                </v-btn>
              </div>
            </v-card-text>
          </v-card>

          <!-- Resume Selection Snackbar -->
          <v-snackbar
            v-model="isSelectingResume"
            color="info"
            :timeout="-1"
            multi-line
            top
            class="font-weight-bold"
          >
            {{ selectionMode === 'MATCH' ? '请选择用于匹配的简历' : '请选择你想要分析的简历' }}
            <template v-slot:actions>
              <v-btn
                color="white"
                variant="text"
                class="font-weight-bold"
                @click="cancelResumeSelection"
              >
                取消
              </v-btn>
            </template>
          </v-snackbar>

          <!-- Resume List Table -->
          <v-card class="elevation-1">
            <v-card-title class="text-h6 pa-4 font-weight-bold d-flex align-center">
              <span>您上传过的简历</span>
              <v-spacer></v-spacer>
              <!-- Filters -->
              <div class="d-flex align-center" style="gap: 12px; width: 50%;">
                 <v-text-field
                   v-model="searchResumeName"
                   density="compact"
                   variant="outlined"
                   label="搜索简历名称"
                   prepend-inner-icon="mdi-magnify"
                   hide-details
                   single-line
                   class="flex-grow-1"
                   @keydown="e => e.key === 'Enter' && fetchResumes()"
                   @click:append-inner="fetchResumes"
                 ></v-text-field>
                 <v-btn
                   :color="timeFilter.active ? 'primary' : 'default'"
                   :variant="timeFilter.active ? 'flat' : 'outlined'"
                   prepend-icon="mdi-calendar-filter"
                   @click="openTimeFilterDialog"
                 >
                   时间过滤
                 </v-btn>
              </div>
            </v-card-title>
            <v-table>
              <thead>
                <tr>
                  <th class="text-center font-weight-bold">序号</th>
                  <th class="text-center font-weight-bold">ID</th>
                  <th class="text-center font-weight-bold">简历名称</th>
                  <th class="text-center font-weight-bold">创建时间</th>
                  <th class="text-center font-weight-bold">更新时间</th>
                  <th class="text-center font-weight-bold" style="width: 120px;">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="resumeList.length === 0">
                   <td colspan="6" class="text-center pa-4 text-grey">
                     {{ '暂无简历数据' }}
                   </td>
                </tr>
                <tr
                  v-for="(item, index) in resumeList"
                  :key="item.id"
                  :class="{'resume-row-select': isSelectingResume}"
                  @click="selectResume(item)"
                >
                  <td class="text-center">{{ index + 1 }}</td>
                  <td class="text-center">{{ item.id }}</td>
                  <td class="text-center">{{ item.name }}</td>
                  <td class="text-center">{{ formatDate(item.createTime) }}</td>
                  <td class="text-center">{{ formatDate(item.updateTime) }}</td>
                  <td class="text-center">
                    <v-btn
                      icon
                      color="primary"
                      size="small"
                      variant="text"
                      class="mr-2"
                      @click="handleDownload(item.id)"
                    >
                      <v-icon>mdi-download</v-icon>
                      <v-tooltip activator="parent" location="bottom">下载</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      color="error"
                      size="small"
                      variant="text"
                      @click="prepareDelete(item)"
                    >
                      <v-icon>mdi-delete</v-icon>
                      <v-tooltip activator="parent" location="bottom">删除</v-tooltip>
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
            <div v-if="loading" class="text-center pa-4">
               <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>

            <!-- Resume Pagination Controls -->
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
                  :items="[{title: '创建时间', value: 'createTime'}, {title: '更新时间', value: 'updateTime'}]"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                ></v-select>

                <p class="text-caption mb-1">起始时间</p>
                <v-text-field
                    v-model="tempTimeFilter.start"
                    type="datetime-local"
                    variant="outlined"
                    density="compact"
                ></v-text-field>

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
                <v-btn
                    color="grey-darken-1"
                    variant="text"
                    @click="showTimeFilterDialog = false"
                >
                  取消
                </v-btn>
                <v-btn
                    color="primary"
                    variant="flat"
                    @click="confirmTimeFilter"
                >
                  确认
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <!-- Upload Floating Button -->
          <v-btn
              color="primary"
              icon="mdi-plus"
              size="large"
              position="fixed"
              location="bottom right"
              class="ma-6"
              elevation="4"
              @click="showUploadDialog = true"
              style="bottom: 96px; right: 24px; z-index: 100;"
              v-tooltip="'添加简历'"
          ></v-btn>

          <!-- Chat Bot Floating Button -->
          <v-btn
            color="blue"
            icon="mdi-robot-happy"
            size="large"
            position="fixed"
            location="bottom right"
            class="ma-6"
            elevation="4"
            @click="openChatBot"
            style="bottom: 24px; right: 24px; z-index: 100;"
            v-tooltip="'分析小助手'"
          >
          </v-btn>

          <!-- Upload Dialog -->
          <v-dialog v-model="showUploadDialog" max-width="500">
             <v-card>
               <v-card-title class="text-h5 pa-4">
                 要添加新的简历吗？
               </v-card-title>
               <v-card-text class="pa-4">
                 <p class="text-red mb-4 font-weight-bold">目前仅支持上传PDF文件！</p>
                 <v-file-input
                    v-model="uploadFile"
                    accept="application/pdf"
                    label="选择文件"
                    variant="outlined"
                    prepend-icon="mdi-file-pdf-box"
                    show-size
                 ></v-file-input>
               </v-card-text>
               <v-card-actions class="pa-4 justify-end">
                 <v-btn
                   color="grey-darken-1"
                   variant="text"
                   @click="showUploadDialog = false"
                 >
                   取消
                 </v-btn>
                 <v-btn
                   color="primary"
                   variant="flat"
                   :loading="uploading"
                   @click="handleUpload"
                 >
                   确认
                 </v-btn>
               </v-card-actions>
             </v-card>
          </v-dialog>

          <!-- Delete Confirmation Dialog -->
          <v-dialog v-model="showDeleteDialog" max-width="400">
             <v-card>
               <v-card-title class="text-h5 pa-4">
                 确认删除简历
               </v-card-title>
                <v-card-text class="pa-4">
                 确定要删除简历 <span class="font-weight-bold">{{ resumeToDelete ? resumeToDelete.name : '' }}</span> 吗？
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
                   删除
                 </v-btn>
               </v-card-actions>
             </v-card>
          </v-dialog>

          <!-- JD Input Dialog for Analysis -->
          <v-dialog v-model="showJdInputDialog" max-width="400">
            <v-card>
              <v-card-title class="text-h5 pa-4">
                请输入职位信息
              </v-card-title>
              <v-card-text class="pa-4">
                <v-text-field
                  v-model="inputJdId"
                  label="JD ID"
                  placeholder="请输入JD ID"
                  prepend-icon="mdi-identifier"
                ></v-text-field>
                <div class="mt-2 text-right">
                  <a
                    href="#"
                    class="text-primary text-decoration-underline"
                    @click.prevent="openJdRepository"
                  >
                    不知道ID？逛逛JD仓库！
                  </a>
                </div>
              </v-card-text>
              <v-card-actions class="pa-4 justify-end">
                <v-btn
                  color="grey-darken-1"
                  variant="text"
                  @click="showJdInputDialog = false"
                >
                  取消
                </v-btn>
                <v-btn
                  color="primary"
                  variant="flat"
                  :loading="analyzing"
                  :disabled="!inputJdId"
                  @click="confirmAnalysis"
                >
                  开始分析
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <!-- Match Confirmation Dialog -->
          <v-dialog v-model="showMatchConfirmDialog" max-width="400">
            <v-card>
              <v-card-title class="text-h5 pa-4">
                即将开始全库匹配
              </v-card-title>
              <v-card-text class="pa-4">
                确定要使用简历 <span class="font-weight-bold">{{ selectedResume ? selectedResume.name : '' }}</span> 开始全库匹配吗？
                <div class="mt-2 text-red">
                  全库匹配将会根据您提供的简历推荐合适的JD
                </div>
              </v-card-text>
              <v-card-actions class="pa-4 justify-end">
                <v-btn
                  color="grey-darken-1"
                  variant="text"
                  @click="showMatchConfirmDialog = false"
                >
                  取消
                </v-btn>
                <v-btn
                  color="primary"
                  variant="flat"
                  :loading="analyzing"
                  @click="confirmMatch"
                >
                  确认
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <v-snackbar-queue v-model="snackbar_messages"></v-snackbar-queue>
        </template>

        <!-- Display for Recruiter -->
        <template v-else-if="user.role === RECRUITER_NUMBER">
          <!-- Analysis Component -->
          <v-card class="mb-6 elevation-1">
            <v-card-title class="text-h5 font-weight-bold pa-4">
              职位分析
            </v-card-title>
            <v-card-text class="pa-4">
              <div class="d-flex gap-4">
                <v-btn
                  :color="(isSelectingJd && selectionMode === 'ANALYSIS') ? 'light-blue-lighten-4' : 'primary'"
                  :variant="(isSelectingJd && selectionMode === 'ANALYSIS') ? 'tonal' : 'elevated'"
                  size="large"
                  prepend-icon="mdi-text-box-search-outline"
                  class="mr-4"
                  @click="startJdSelection('ANALYSIS')"
                >
                  指定分析
                </v-btn>
                <v-btn
                  :color="(isSelectingJd && selectionMode === 'MATCH') ? 'light-blue-lighten-4' : 'secondary'"
                  :variant="(isSelectingJd && selectionMode === 'MATCH') ? 'tonal' : 'elevated'"
                  size="large"
                  prepend-icon="mdi-database-search-outline"
                  @click="startJdSelection('MATCH')"
                >
                  全库匹配
                </v-btn>
                <v-btn
                  color="info"
                  size="large"
                  variant="elevated"
                  prepend-icon="mdi-history"
                  class="ml-auto"
                  @click="$router.push('/analysis-history')"
                >
                  历史记录
                </v-btn>
              </div>
            </v-card-text>
          </v-card>

          <!-- JD Selection Snackbar -->
          <v-snackbar
            v-model="isSelectingJd"
            color="info"
            :timeout="-1"
            multi-line
            top
            class="font-weight-bold"
          >
            {{ selectionMode === 'MATCH' ? '请选择用于匹配的JD' : '请选择你想要分析的JD' }}
            <template v-slot:actions>
              <v-btn
                color="white"
                variant="text"
                class="font-weight-bold"
                @click="cancelJdSelection"
              >
                取消
              </v-btn>
            </template>
          </v-snackbar>

          <!-- JD List Table (Published Positions) -->
          <v-card class="elevation-1">
            <v-card-title class="text-h6 pa-4 font-weight-bold">
              您发布过的职位
            </v-card-title>
            <v-card-text class="pb-0">
               <v-row dense>
                 <!-- ID and Keyword Search -->
                 <v-col cols="12" md="2">
                   <v-text-field
                     v-model="searchJdId"
                     label="ID 搜索"
                     prepend-inner-icon="mdi-identifier"
                     variant="outlined"
                     density="compact"
                     hide-details
                     @keydown="e => e.key === 'Enter' && fetchPublishedJds()"
                   ></v-text-field>
                 </v-col>
                 <v-col cols="12" md="4">
                   <v-text-field
                     v-model="searchJdKeyword"
                     label="关键词搜索"
                     prepend-inner-icon="mdi-magnify"
                     variant="outlined"
                     density="compact"
                     hide-details
                     @keydown="e => e.key === 'Enter' && fetchPublishedJds()"
                     @click:append-inner="fetchPublishedJds"
                   ></v-text-field>
                 </v-col>

                  <!-- Salary Filter Button -->
                  <v-col cols="12" md="4" class="d-flex align-center justify-center">
                       <v-btn
                           :color="jdSalaryFilter.active ? 'primary' : 'default'"
                           :variant="jdSalaryFilter.active ? 'flat' : 'outlined'"
                           prepend-icon="mdi-cash"
                           @click="openJdSalaryFilterDialog"
                           block
                       >
                         薪资过滤
                       </v-btn>
                  </v-col>

                 <!-- Time Filter Button -->
                 <v-col cols="12" md="2" class="d-flex align-center justify-end">
                   <v-btn
                       :color="jdTimeFilter.active ? 'primary' : 'default'"
                       :variant="jdTimeFilter.active ? 'flat' : 'outlined'"
                       prepend-icon="mdi-calendar-filter"
                       @click="openJdTimeFilterDialog"
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
                <tr v-if="jdList.length === 0 && !jdLoading">
                   <td colspan="9" class="text-center pa-4 text-grey">
                      {{ '暂无职位数据' }}
                   </td>
                </tr>
                <tr
                  v-for="(item, index) in jdList"
                  :key="item.id"
                  :class="{'jd-row-select': isSelectingJd}"
                  @click="selectJd(item)"
                >
                  <td class="text-center">{{ index + 1 }}</td>
                  <td class="text-center">{{ item.id }}</td>
                  <td class="text-center">{{ item.name }}</td>
                  <td class="text-center">{{ item.company }}</td>
                  <td class="text-center">{{ item.location }}</td>
                  <td class="text-center">{{ item.salary }}</td>
                  <td class="text-center">{{ formatDate(item.createTime) }}</td>
                  <td class="text-center">{{ formatDate(item.updateTime) }}</td>
                  <td class="text-center" style="display: flex; justify-content: space-around;">
                    <v-btn icon color="primary" size="small" variant="text" @click.stop="handleJdView(item.id, item.name)">
                      <v-icon>mdi-file-document</v-icon>
                      <v-tooltip activator="parent" location="bottom">查看</v-tooltip>
                    </v-btn>
                    <v-btn icon color="primary" size="small" variant="text" @click.stop="handleJdDownload(item.id)">
                      <v-icon>mdi-download</v-icon>
                      <v-tooltip activator="parent" location="bottom">下载</v-tooltip>
                    </v-btn>
                    <v-btn icon color="error" size="small" variant="text" @click.stop="prepareJdDelete(item)">
                      <v-icon>mdi-delete</v-icon>
                      <v-tooltip activator="parent" location="bottom">删除</v-tooltip>
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
            <div v-if="jdLoading" class="text-center pa-6">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>

            <!-- JD Pagination Controls -->
            <v-divider></v-divider>
            <v-card-actions class="justify-center pa-4">
              <v-row align="center" justify="center" dense>
                  <v-col cols="auto">
                    <v-btn variant="text" icon="mdi-chevron-left" :disabled="jdPage <= 1 || jdLoading" @click="handleJdPageChange(jdPage - 1)"></v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <span class="text-body-2">第 {{ jdPage }} 页 / 共 {{ jdTotalPages }} 页</span>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn variant="text" icon="mdi-chevron-right" :disabled="jdPage >= jdTotalPages || jdLoading" @click="handleJdPageChange(jdPage + 1)"></v-btn>
                  </v-col>
                  <v-col cols="auto" class="ml-4">
                    <v-text-field v-model="jdJumpPage" label="跳转至" type="number" variant="outlined" density="compact" hide-details style="width: 80px" @keydown="e => e.key === 'Enter' && handleJdJumpPage()"></v-text-field>
                  </v-col>
              </v-row>
            </v-card-actions>
          </v-card>

          <!-- Publish JD Floating Button -->
          <v-btn
              color="primary"
              icon="mdi-plus"
              size="large"
              position="fixed"
              location="bottom right"
              class="ma-6"
              elevation="4"
              @click="showPublishJdDialog = true"
              style="bottom: 96px; right: 24px; z-index: 100;"
              v-tooltip="'发布职位'"
          ></v-btn>

          <!-- Chat Bot Floating Button -->
          <v-btn
            color="blue"
            icon="mdi-robot-happy"
            size="large"
            position="fixed"
            location="bottom right"
            class="ma-6"
            elevation="4"
            @click="openChatBot"
            style="bottom: 24px; right: 24px; z-index: 100;"
            v-tooltip="'分析小助手'"
          >
          </v-btn>

          <!-- Publish JD Dialog -->
          <v-dialog v-model="showPublishJdDialog" max-width="800">
             <v-card>
               <v-card-title class="text-h5 pa-4">要发布新的职位吗？</v-card-title>
               <v-card-text class="pa-4">
                 <v-tabs v-model="publishMode" class="mb-4">
                    <v-tab value="manual">手动输入</v-tab>
                    <v-tab value="upload">上传文件</v-tab>
                 </v-tabs>

                 <v-window v-model="publishMode">
                    <v-window-item value="manual">
                       <v-form v-model="jdFormValid">
                          <v-row dense>
                             <v-col cols="12" md="6">
                                <v-text-field v-model="jdForm.title" label="职位标题" :rules="[jdRules.required]" variant="outlined"></v-text-field>
                             </v-col>
                             <v-col cols="12" md="6">
                                <v-text-field
                                  v-model="jdForm.company"
                                  label="公司名称"
                                  :rules="[jdRules.required]"
                                  variant="outlined"
                                ></v-text-field>
                             </v-col>
                             <v-col cols="12" md="6">
                                <v-text-field v-model="jdForm.location" label="工作地点" :rules="[jdRules.required]" variant="outlined"></v-text-field>
                             </v-col>

                             <!-- New Salary Inputs -->
                             <v-col cols="12" md="12" class="py-2">
                                <span class="text-subtitle-2 text-grey-darken-1">薪资范围设置</span>
                             </v-col>
                             <v-col cols="12" md="4">
                                <v-text-field
                                    v-model="jdFormSalaryInput.min"
                                    label="最低薪资"
                                    type="number"
                                    :rules="[jdRules.required]"
                                    variant="outlined"
                                    density="compact"
                                ></v-text-field>
                             </v-col>
                             <v-col cols="12" md="4">
                                <v-text-field
                                    v-model="jdFormSalaryInput.max"
                                    label="最高薪资"
                                    type="number"
                                    :rules="[jdRules.required]"
                                    variant="outlined"
                                    density="compact"
                                ></v-text-field>
                             </v-col>
                             <v-col cols="12" md="4">
                                <v-select
                                    v-model="jdFormSalaryInput.period"
                                    label="发放周期"
                                    :items="['日', '月', '年']"
                                    variant="outlined"
                                    density="compact"
                                ></v-select>
                             </v-col>

                             <v-col cols="12">
                                <v-textarea v-model="jdForm.description" label="职位描述" :rules="[jdRules.required]" variant="outlined"></v-textarea>
                             </v-col>
                             <v-col cols="12">
                                <v-textarea v-model="jdForm.requirements" label="岗位要求" variant="outlined"></v-textarea>
                             </v-col>
                             <v-col cols="12">
                                <v-textarea v-model="jdForm.bonus" label="福利待遇" variant="outlined"></v-textarea>
                             </v-col>
                          </v-row>
                       </v-form>
                    </v-window-item>
                    <v-window-item value="upload">
                       <v-file-input
                          v-model="jdUploadFile"
                          accept="application/pdf"
                          label="选择JD PDF文件"
                          variant="outlined"
                          show-size
                       ></v-file-input>
                    </v-window-item>
                 </v-window>
               </v-card-text>
               <v-card-actions class="pa-4 justify-end">
                 <v-btn color="grey-darken-1" variant="text" @click="showPublishJdDialog = false">取消</v-btn>
                 <v-btn
                   color="primary"
                   variant="flat"
                   :loading="publishing"
                   :disabled="publishMode === 'manual' && !jdFormValid"
                   @click="handlePublishJd"
                 >
                   确认
                 </v-btn>
               </v-card-actions>
             </v-card>
          </v-dialog>

          <!-- Input Resume ID Dialog -->
          <v-dialog v-model="showResumeInputDialog" max-width="400">
            <v-card>
               <v-card-title class="text-h5 pa-4">请输入简历信息</v-card-title>
               <v-card-text class="pa-4">
                  <v-text-field
                     v-model="inputResumeId"
                     label="简历 ID"
                     placeholder="请输入简历 ID"
                     variant="outlined"
                  ></v-text-field>
                  <div class="mt-2 text-right">
                    <a href="#" class="text-primary text-decoration-underline" @click.prevent="openResumeRepository">查询简历仓库</a>
                  </div>
               </v-card-text>
               <v-card-actions class="pa-4 justify-end">
                  <v-btn color="grey-darken-1" variant="text" @click="showResumeInputDialog = false">取消</v-btn>
                  <v-btn color="primary" variant="flat" :loading="analyzing" :disabled="!inputResumeId" @click="confirmRecruiterAnalysis">确认</v-btn>
               </v-card-actions>
            </v-card>
          </v-dialog>

          <!-- Full Match Confirm Dialog -->
          <v-dialog v-model="showJdMatchConfirmDialog" max-width="400">
             <v-card>
                <v-card-title class="text-h6 pa-4">即将开始全库匹配</v-card-title>
                <v-card-text class="pa-4">
                   确定要使用JD <span class="font-weight-bold">{{ selectedJd ? selectedJd.name : '' }}</span> 开始全库匹配吗？
                   <div class="mt-2 text-red font-weight-bold">全库匹配将会根据您提供的职位描述推荐合适的简历</div>
                </v-card-text>
                <v-card-actions class="pa-4 justify-end">
                  <v-btn color="grey-darken-1" variant="text" @click="showJdMatchConfirmDialog = false">取消</v-btn>
                  <v-btn color="primary" variant="flat" :loading="analyzing" @click="confirmRecruiterMatch">确认</v-btn>
                </v-card-actions>
             </v-card>
          </v-dialog>

          <!-- JD Delete Dialog -->
          <v-dialog v-model="showJdDeleteDialog" max-width="400">
             <v-card>
               <v-card-title class="text-h5 pa-4">确认删除职位</v-card-title>
                <v-card-text class="pa-4">
                 确定要删除职位 <span class="font-weight-bold">{{ jdToDelete ? jdToDelete.name : '' }}</span> 吗？
               </v-card-text>
               <v-card-actions class="pa-4 justify-end">
                 <v-btn color="grey-darken-1" variant="text" @click="showJdDeleteDialog = false">取消</v-btn>
                 <v-btn color="error" variant="flat" :loading="jdDeleting" @click="handleJdDelete">删除</v-btn>
               </v-card-actions>
             </v-card>
          </v-dialog>

          <!-- JD Time Filter Dialog -->
          <v-dialog v-model="showJdTimeFilterDialog" max-width="400">
             <v-card>
               <v-card-title class="text-h6 pa-4">设置时间过滤器</v-card-title>
               <v-card-text class="pa-4">
                  <v-select
                    v-model="tempJdTimeFilter.target"
                    label="过滤目标栏目"
                    :items="[{title:'发布时间', value:'createTime'}, {title:'更新时间', value:'updateTime'}]"
                    variant="outlined"
                    density="compact"
                    class="mb-4"
                  ></v-select>
                  <p class="text-caption mb-1">起始时间</p>
                  <v-text-field v-model="tempJdTimeFilter.start" type="datetime-local" variant="outlined" density="compact"></v-text-field>
                  <p class="text-caption mb-1 mt-2">终止时间</p>
                  <v-text-field v-model="tempJdTimeFilter.end" type="datetime-local" variant="outlined" density="compact" :error="jdTimeFilterError" :error-messages="jdTimeFilterError ? '终止时间不能小于起始时间' : ''"></v-text-field>
               </v-card-text>
               <v-card-actions class="pa-4 justify-end">
                  <v-btn color="grey-darken-1" variant="text" @click="showJdTimeFilterDialog = false">取消</v-btn>
                  <v-btn color="primary" variant="flat" @click="confirmJdTimeFilter">确认</v-btn>
               </v-card-actions>
             </v-card>
          </v-dialog>

          <!-- JD Salary Filter Dialog -->
          <v-dialog v-model="showJdSalaryFilterDialog" max-width="500">
             <v-card>
               <v-card-title class="text-h6 pa-4">设置薪资过滤器</v-card-title>
               <v-card-text class="pa-4">
                  <v-row dense>
                      <v-col cols="12" md="4">
                        <v-text-field v-model="tempJdSalaryFilter.min" label="最低薪资" type="number" variant="outlined" density="compact"></v-text-field>
                      </v-col>
                      <v-col cols="12" md="4">
                        <v-text-field v-model="tempJdSalaryFilter.max" label="最高薪资" type="number" variant="outlined" density="compact"></v-text-field>
                      </v-col>
                      <v-col cols="12" md="4">
                        <v-select v-model="tempJdSalaryFilter.period" label="发放周期" :items="['日', '月', '年']" variant="outlined" density="compact"></v-select>
                      </v-col>
                  </v-row>
                  <p v-if="jdSalaryFilterError" class="text-red text-caption">最高薪资不能低于最低薪资</p>
               </v-card-text>
               <v-card-actions class="pa-4 justify-end">
                  <v-btn color="grey-darken-1" variant="text" @click="showJdSalaryFilterDialog = false">取消</v-btn>
                  <v-btn color="primary" variant="flat" @click="confirmJdSalaryFilter">确认</v-btn>
               </v-card-actions>
             </v-card>
          </v-dialog>

          <v-snackbar-queue v-model="snackbar_messages"></v-snackbar-queue>
        </template>

        <!-- Default Welcome for others (e.g. Recruiter or generic) -->
        <template v-else>
           <h1 class="text-h4 mt-6 mb-4 text-black font-weight-bold">欢迎使用</h1>
          <v-card class="mb-6 elevation-1">
            <v-icon class="ml-4">mdi-alert</v-icon>
             <p>暂无内容！施工中...</p>
          </v-card>
        </template>

      </v-container>
    </v-main>
  </div>
</template>

<style scoped>
/* Vuetify handles styles */
.resume-row-select, .jd-row-select {
  cursor: pointer;
}
.resume-row-select:hover, .jd-row-select:hover {
  background-color: #E1F5FE !important; /* light-blue-lighten-5 or similar */
}
</style>
