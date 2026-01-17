<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { CANDIDATE_NUMBER, RECRUITER_NUMBER } from '../utils/constants'

const CANDIDATE = CANDIDATE_NUMBER
const RECRUITER = RECRUITER_NUMBER

const router = useRouter()
const form = ref({
  username: '',
  password: '',
  role: 0,
})
const valid = ref(false)
const loading = ref(false)

// Registration state
const isLogin = ref(true)
const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  role: 0,
})
const registerValid = ref(false)
const registerLoading = ref(false)

const rules = {
  required: value => !!value || '此项必填',
  matchPassword: value => value === registerForm.value.password || '密码不一致'
}

const showPassword = ref(false)

const messages = ref([])   // Snackbar messages queue，用于显示登录相关的信息（成功、失败等）

const handleLogin = async () => {
  /*
  messages.value.push({
    text: '尝试登录中...',
    timeout: 1500,
    color: 'blue-grey',
  })
  */
  if (!form.value.username || !form.value.password) return

  loading.value = true
  try {
    const res = await request.post('/user/login', form.value)

    if (res.code === 200) {
      // Login success
      messages.value.push({
        text: '登录成功，正在跳转...',
        timeout: 3000,
        color: 'success',
      })
      const { token, username, role } = res.data
      // Save token to cookie with 7 days expiration
      // (if we don't set max-age, the cookie will be a session cookie and expire when the browser is closed)
      document.cookie = `token=${token}; path=/; max-age=604800`
      document.cookie = `role=${role}; path=/; max-age=604800`

      // Save user info for Main page display
      localStorage.setItem('currentUser', JSON.stringify({ username, role }))

      router.push('/')
    } else {
      // Login failed
      messages.value.push({
        text: res.message || '登录失败',
        timeout: 3000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error(error)
    messages.value.push({
      text: '网络请求失败或服务器异常',
      timeout: 3000,
      color: 'error',
    })
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (registerForm.value.password !== registerForm.value.confirmPassword) return

  messages.value.push({
    text: '正在注册...',
    timeout: 1000,
    color: 'blue-grey',
  })

  registerLoading.value = true
  try {
    const payload = {
      username: registerForm.value.username,
      password: registerForm.value.password,
      role: registerForm.value.role
    }
    const res = await request.post('/user/register', payload)

    if (res.code === 200) {
      messages.value.push({
        text: '注册成功！请使用新账号登录',
        timeout: 3000,
        color: 'success',
      })
      isLogin.value = true
      // Optional: clear register form
      registerForm.value = { username: '', password: '', confirmPassword: '', role: 0 }
    } else {
      messages.value.push({
        text: res.message || '注册失败',
        timeout: 3000,
        color: 'error',
      })
    }
  } catch (error) {
    console.error(error)
    messages.value.push({
      text: '网络请求失败或服务器异常',
      timeout: 3000,
      color: 'error',
    })
  } finally {
    registerLoading.value = false
  }
}
</script>

<template>
  <v-main>
    <v-container fluid class="fill-height login-wrapper">
      <v-row justify="center" align="center">
        <v-col cols="12" sm="8" md="6" lg="4">
          <v-card class="elevation-4 pa-6">
            <!-- Login Form -->
            <v-card-title class="text-center text-h4 font-weight-bold mb-6 text-black">
              简历职位分析系统
            </v-card-title>
            <v-card-text>
              <v-form v-if="isLogin" v-model="valid" @submit.prevent="handleLogin">
                <v-text-field
                  v-model="form.username"
                  label="用户名"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  :rules="[rules.required]"
                  required
                  class="mb-2"
                ></v-text-field>

                <v-text-field
                  v-model="form.password"
                  label="密码"
                  prepend-inner-icon="mdi-lock"
                  variant="outlined"
                  :type="showPassword ? 'text' : 'password'"
                  clearable
                  :append-inner-icon ="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append-inner="showPassword = !showPassword"
                  :rules="[rules.required]"
                  required
                  class="mb-2"
                ></v-text-field>

                <div class="mb-4">
                  <label class="d-block text-subtitle-1 font-weight-bold text-center">身份</label>
                  <v-radio-group class="d-flex justify-center" v-model="form.role" inline color="primary">
                    <v-radio label="求职者" v-bind:value="CANDIDATE"></v-radio>
                    <v-radio label="招聘者" v-bind:value="RECRUITER"></v-radio>
                  </v-radio-group>
                </div>

                <v-btn
                  block
                  color="primary"
                  size="large"
                  type="submit"
                  :loading="loading"
                  :disabled="!valid"
                >
                  登录
                </v-btn>

                <div class="text-center mt-4">
                  <span class="text-blue cursor-pointer" @click="isLogin = false; showPassword = false">注册新账号</span>
                </div>
              </v-form>

              <!-- Registration Form -->
              <v-form v-if="!isLogin" v-model="registerValid" @submit.prevent="handleRegister">
                <v-text-field
                  v-model="registerForm.username"
                  label="用户名"
                  prepend-inner-icon="mdi-account"
                  variant="outlined"
                  :rules="[rules.required]"
                  required
                  class="mb-2"
                ></v-text-field>

                <v-text-field
                  v-model="registerForm.password"
                  label="密码"
                  prepend-inner-icon="mdi-lock"
                  variant="outlined"
                  :type="showPassword ? 'text' : 'password'"
                  clearable
                  :append-inner-icon ="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append-inner="showPassword = !showPassword"
                  :rules="[rules.required]"
                  required
                  class="mb-2"
                ></v-text-field>

                <v-text-field
                  v-model="registerForm.confirmPassword"
                  label="确认密码"
                  prepend-inner-icon="mdi-lock"
                  variant="outlined"
                  type="text"
                  clearable
                  :rules="[rules.required, rules.matchPassword]"
                  required
                  class="mb-2"
                ></v-text-field>

                <div class="mb-4">
                  <label class="d-block text-subtitle-1 mb-1 font-weight-bold text-center">身份</label>
                  <v-radio-group class="d-flex justify-center" v-model="registerForm.role" inline color="primary">
                    <v-radio label="求职者" v-bind:value="CANDIDATE"></v-radio>
                    <v-radio label="招聘者" v-bind:value="RECRUITER"></v-radio>
                  </v-radio-group>
                </div>

                <v-btn
                  block
                  color="primary"
                  size="large"
                  type="submit"
                  :loading="registerLoading"
                  :disabled="!registerValid"
                >
                  注册
                </v-btn>

                <div class="text-center mt-4">
                  <span class="text-blue cursor-pointer" @click="isLogin = true; showPassword = false">登录账号</span>
                </div>
              </v-form>
            </v-card-text>
          </v-card>
          <!-- Snackbar Queue for messages，可以按产生的先后顺序将messages数组中消息展示出来 -->
          <v-snackbar-queue v-model="messages"></v-snackbar-queue>
        </v-col>
      </v-row>
    </v-container>
  </v-main>
</template>

<style scoped>
.login-wrapper {
  background-color: #f0f2f5;
  min-height: 100vh;
}
.text-black {
  color: #000000 !important;
}
.cursor-pointer {
  cursor: pointer;
}
</style>
