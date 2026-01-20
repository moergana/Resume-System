<script setup>
import { ref, computed } from 'vue'
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

// Reset Password state
const isResetPassword = ref(false)
const resetForm = ref({
  emailLocal: '',
  emailDomain: '@qq.com',
  emailCode: '',
  password: '',
  confirmPassword: ''
})
const resetValid = ref(false)
const resetLoading = ref(false)

// Registration state
const isLogin = ref(true)
const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
  role: 0,
  emailLocal: '',
  emailDomain: '@qq.com',
  emailCode: ''
})
const registerValid = ref(false)
const registerLoading = ref(false)
const registerEmailCountdown = ref(0)

const emailDomains = ['@qq.com', '@163.com', '@gmail.com', '@outlook.com', '@yahoo.com']

const rules = {
  required: value => !!value || '此项必填',
  matchPassword: value => value === registerForm.value.password || '密码不一致',
  matchResetPassword: value => value === resetForm.value.password || '密码不一致'
}

const formTitle = computed(() => {
    if (isResetPassword.value) return '重置密码'
    if (isLogin.value) return '登录'
    return '注册'
})

const showPassword = ref(false)
const showResetPassword = ref(false) // Added for reset password toggle
const showResetConfirmPassword = ref(false) // Added for reset password toggle

const messages = ref([])   // Snackbar messages queue

const resetPasswordCountdown = ref(0)
let timer = null

const startCountdown = (countdown) => {
  countdown.value = 60
    if (timer) clearInterval(timer)
    timer = setInterval(() => {
      countdown.value--
        if (countdown.value <= 0) {
            clearInterval(timer)
        }
    }, 1000)
}

const sendEmailCode = async (emailLocal, emailDomain, type) => {
  if (type === 'reset' && resetPasswordCountdown.value > 0) return
  if (type === 'register' && registerEmailCountdown.value > 0) return
  if (!emailLocal) {
    messages.value.push({ text: '请输入邮箱前缀', color: 'warning' })
    return
  }
  const email = `${emailLocal}${emailDomain}`

  // Start countdown immediately or after success? Usually immediately to prevent spam.
  // Requirement says "Click -> button grey, show time".
  // But if request fails, maybe we shouldn't cooldown?
  // Let's start it for now to prevent spamming requests.
  if (type === 'reset') startCountdown(resetPasswordCountdown)
  else if (type === 'register') startCountdown(registerEmailCountdown)

  try {
    // Changed endpoint to /user/resetPassword/emailCode
    let url = '/user/resetPassword/emailCode'
    if (type === 'reset') {
      url = '/user/resetPassword/emailCode'
    } else if (type === 'register') {
      url = '/user/register/emailCode'
    }
    const res = await request.post(url, { email })
    if (res.code === 200) {
      messages.value.push({ text: res.message || '验证码已发送', color: 'success' })
    } else {
      messages.value.push({ text: res.message || '发送失败', color: 'error' })
      // Reset countdown if failed
      if (type === 'reset') resetPasswordCountdown.value = 0
      else if (type === 'register') registerEmailCountdown.value = 0
      clearInterval(timer)
    }
  } catch (error) {
    messages.value.push({ text: '发送请求失败', color: 'error' })
    if (type === 'reset') resetPasswordCountdown.value = 0
    else if (type === 'register') registerEmailCountdown.value = 0
    clearInterval(timer)
  }
}

const handleResetPassword = async () => {
    if (resetForm.value.password !== resetForm.value.confirmPassword) return

    resetLoading.value = true
    try {
        const payload = {
            password: resetForm.value.password,
            email: `${resetForm.value.emailLocal}${resetForm.value.emailDomain}`,
            emailCode: resetForm.value.emailCode
        }
        // Changed endpoint to /user/resetPassword
        const res = await request.post('/user/resetPassword', payload)
        if (res.code === 200) {
             messages.value.push({ text: res.message || '密码重置成功，请登录', color: 'success', timeout: 3000 })
             isResetPassword.value = false
             isLogin.value = true
             resetForm.value = {
                emailLocal: '',
                emailDomain: '@qq.com',
                emailCode: '',
                password: '',
                confirmPassword: ''
             }
        } else {
             messages.value.push({ text: res.message || '重置失败', color: 'error' })
        }
    } catch (error) {
        messages.value.push({ text: '请求失败', color: 'error' })
    } finally {
        resetLoading.value = false
    }
}

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
      const { token, username, role, email } = res.data
      // Save token to cookie with 7 days expiration
      // (if we don't set max-age, the cookie will be a session cookie and expire when the browser is closed)
      document.cookie = `token=${token}; path=/; max-age=604800`
      document.cookie = `role=${role}; path=/; max-age=604800`

      // Save user info for Main page display
      localStorage.setItem('currentUser', JSON.stringify({ username, role, email }))

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
      role: registerForm.value.role,
      email: `${registerForm.value.emailLocal}${registerForm.value.emailDomain}`
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
      registerForm.value = { username: '', password: '', confirmPassword: '', role: 0, emailLocal: '', emailDomain: '@qq.com' }
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
            <div class="text-center text-h4 font-weight-bold mb-6 text-black">
              简历职位分析系统
            </div>
            <v-card-title class="text-center text-h5 font-weight-bold mb-6">
              {{ formTitle }}
            </v-card-title>
            <v-card-text>
              <v-form v-if="isLogin && !isResetPassword" v-model="valid" @submit.prevent="handleLogin">
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

                <div class="d-flex justify-end mb-4">
                  <span
                      class="text-blue text-decoration-underline cursor-pointer"
                      @click="isResetPassword = true; isLogin = false"
                  >
                    忘记密码
                  </span>
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
                  <span class="text-blue cursor-pointer" @click="isLogin = false; isResetPassword = false; showPassword = false">注册新账号</span>
                </div>
              </v-form>

              <!-- Reset Password Form -->
              <v-form v-if="isResetPassword" v-model="resetValid" @submit.prevent="handleResetPassword">
                <v-row dense>
                    <v-col cols="7">
                        <v-text-field
                            v-model="resetForm.emailLocal"
                            label="邮箱"
                            variant="outlined"
                            density="compact"
                            :rules="[rules.required]"
                        ></v-text-field>
                    </v-col>
                    <v-col cols="5">
                        <v-select
                            v-model="resetForm.emailDomain"
                            :items="emailDomains"
                            variant="outlined"
                            density="compact"
                            hide-details
                            bg-color="grey-lighten-4"
                        ></v-select>
                    </v-col>
                </v-row>

                <v-row dense class="align-center">
                    <v-col cols="7">
                        <v-text-field
                            v-model="resetForm.emailCode"
                            label="邮箱验证码"
                            variant="outlined"
                            density="compact"
                            hide-details="auto"
                            single-line
                            :rules="[rules.required]"
                        ></v-text-field>
                    </v-col>
                    <v-col cols="5">
                        <v-btn
                            color="info"
                            variant="elevated"
                            block
                            :disabled="resetPasswordCountdown > 0"
                            @click="sendEmailCode(resetForm.emailLocal, resetForm.emailDomain, 'reset')"
                        >
                          {{ resetPasswordCountdown > 0 ? `${resetPasswordCountdown}s` : '发送验证码' }}
                        </v-btn>
                    </v-col>
                </v-row>

                <v-row>
                  <v-text-field
                      v-model="resetForm.password"
                      label="新密码"
                      prepend-inner-icon="mdi-lock"
                      variant="outlined"
                      :type="showResetPassword ? 'text' : 'password'"
                      clearable
                      :append-inner-icon ="showResetPassword ? 'mdi-eye' : 'mdi-eye-off'"
                      @click:append-inner="showResetPassword = !showResetPassword"
                      :rules="[rules.required]"
                      class="mb-2"
                  ></v-text-field>
                </v-row>

                <v-row>
                   <v-text-field
                      v-model="resetForm.confirmPassword"
                      label="确认密码"
                      prepend-inner-icon="mdi-lock"
                      variant="outlined"
                      :type="showResetConfirmPassword ? 'text' : 'password'"
                      clearable
                      :append-inner-icon ="showResetConfirmPassword ? 'mdi-eye' : 'mdi-eye-off'"
                      @click:append-inner="showResetConfirmPassword = !showResetConfirmPassword"
                      :rules="[rules.required, rules.matchResetPassword]"
                      class="mb-2"
                  ></v-text-field>
                </v-row>

                <v-btn
                    block
                    color="primary"
                    size="large"
                    type="submit"
                    :loading="resetLoading"
                    :disabled="!resetValid"
                >
                    确认
                </v-btn>

                <div class="text-center mt-4">
                    <span class="text-blue cursor-pointer" @click="isResetPassword = false; isLogin = true">返回登录</span>
                </div>
              </v-form>

              <!-- Registration Form -->
              <v-form v-if="!isLogin && !isResetPassword" v-model="registerValid" @submit.prevent="handleRegister">
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
                  type="password"
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

                <div class="mb-2">
                  <v-row dense>
                      <v-col cols="7">
                          <v-text-field
                              v-model="registerForm.emailLocal"
                              label="邮箱"
                              variant="outlined"
                              density="compact"
                              :rules="[rules.required]"
                          ></v-text-field>
                      </v-col>
                      <v-col cols="5">
                          <v-select
                              v-model="registerForm.emailDomain"
                              :items="emailDomains"
                              variant="outlined"
                              density="compact"
                              hide-details
                              bg-color="grey-lighten-4"
                          ></v-select>
                      </v-col>
                  </v-row>

                  <v-row dense class="align-center">
                    <v-col cols="7">
                      <v-text-field
                          v-model="registerForm.emailCode"
                          label="邮箱验证码"
                          variant="outlined"
                          density="compact"
                          hide-details="auto"
                          single-line
                          :rules="[rules.required]"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="5">
                      <v-btn
                          color="info"
                          variant="elevated"
                          block
                          :disabled="registerEmailCountdown > 0"
                          @click="sendEmailCode(registerForm.emailLocal, registerForm.emailDomain, 'register')"
                      >
                        {{ registerEmailCountdown > 0 ? `${registerEmailCountdown}s` : '发送验证码' }}
                      </v-btn>
                    </v-col>
                  </v-row>
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
