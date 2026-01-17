<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import request from '@/utils/request.js'
import { formatDate } from "@/utils/tools.js";

const route = useRoute()
const jdId = route.params.id
const jdData = ref(null)
const loading = ref(false)
const feedback_messages = ref([])

onMounted(() => {
  if (jdId) {
    fetchJdDetail()
  } else {
    feedback_messages.value.push({
      text: '无效的JD ID',
      color: 'error'
    })
  }
})

const fetchJdDetail = async () => {
  loading.value = true
  try {
    const res = await request.get(`/jd/${jdId}`)
    if (res.code === 200) {
      jdData.value = res.data
    } else {
      feedback_messages.value.push({
        text: '获取JD详情失败! ' + (res.message || ''),
        timeout: 4000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error('Failed to fetch JD detail:', error)
    feedback_messages.value.push({
        text: '获取详情请求发生错误',
        timeout: 4000,
        color: 'error',
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fill-height bg-grey-lighten-5">
    <v-app-bar color="white" elevation="2">
       <v-app-bar-title class="font-weight-bold text-black">JD 详情</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <v-container>
        <div v-if="loading" class="text-center pa-10">
           <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
           <div class="mt-4 text-grey">加载中...</div>
        </div>

        <v-card v-else-if="jdData" class="pa-4">
          <v-card-title class="text-h5 font-weight-bold mb-4">
            基本信息
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field label="ID" :model-value="jdData.id" variant="outlined" readonly></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field label="用户ID" :model-value="jdData.userId" variant="outlined" readonly></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                 <v-text-field label="名称" :model-value="jdData.name" variant="outlined" readonly></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                 <v-text-field label="公司" :model-value="jdData.company" variant="outlined" readonly></v-text-field>
              </v-col>
               <v-col cols="12" md="6">
                <v-text-field label="创建时间" :model-value="formatDate(jdData.createTime)" variant="outlined" readonly></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field label="更新时间" :model-value="formatDate(jdData.updateTime)" variant="outlined" readonly></v-text-field>
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider class="my-4"></v-divider>

          <v-card-title class="text-h5 font-weight-bold mb-4">
            职位详情
          </v-card-title>
          <v-card-text>
             <v-row>
               <v-col cols="12">
                 <v-text-field label="岗位标题" :model-value="jdData.title" variant="outlined" readonly></v-text-field>
               </v-col>
               <v-col cols="12" md="6">
                  <v-text-field label="工作地点" :model-value="jdData.location" variant="outlined" readonly></v-text-field>
               </v-col>
               <v-col cols="12" md="6">
                  <v-text-field label="薪资待遇" :model-value="jdData.salary" variant="outlined" readonly></v-text-field>
               </v-col>
               <v-col cols="12">
                  <v-textarea label="岗位福利" :model-value="jdData.bonus" variant="outlined" readonly auto-grow></v-textarea>
               </v-col>
               <v-col cols="12">
                  <v-textarea label="职位描述" :model-value="jdData.description" variant="outlined" readonly auto-grow></v-textarea>
               </v-col>
               <v-col cols="12">
                  <v-textarea label="任职要求" :model-value="jdData.requirements" variant="outlined" readonly auto-grow></v-textarea>
               </v-col>
             </v-row>
          </v-card-text>
        </v-card>

        <v-alert v-else class="mt-4" type="warning" variant="tonal">
          未找到相关JD数据
        </v-alert>

        <v-snackbar-queue v-model="feedback_messages"></v-snackbar-queue>
      </v-container>
    </v-main>
  </div>
</template>

<style scoped>
</style>

