import axios from 'axios'
import router from '../router'
import { showGlobalMessage } from './globalMsg'

const service = axios.create({
  baseURL: 'http://localhost:8080',
  timeout: 10000
})

service.interceptors.request.use(
  config => {
    // Helper to get cookie value
    const getCookie = (name) => {
      const value = `; ${document.cookie}`
      const parts = value.split(`; ${name}=`)
      if (parts.length === 2) return parts.pop().split(';').shift()
    }

    const token = getCookie('token')
    const role = getCookie('role')

    if (token) {
      config.headers['Authorization'] = token
    }
    if (role) {
      config.headers['Role'] = role
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  response => {
    // Check for token refresh
    const newToken = response.headers['authorization'] || response.headers['Authorization']
    if (newToken) {
      document.cookie = `token=${newToken}; path=/; max-age=604800`
    }

    // Check for message
    const msg = response.headers['message'] || response.headers['Message']
    if (msg) {
      try {
        showGlobalMessage(decodeURIComponent(msg))
      } catch (e) {
        showGlobalMessage(msg)
      }
    }

    return response.data
  },
  error => {
    if (error.response) {
      if (error.response.status === 401) {
        // Clear cookie and redirect
        // document.cookie = "token=; path=/; max-age=0" // Optional: clear token
        router.push('/login')
      }

      const msg = error.response.headers['message'] || error.response.headers['Message']
      if (msg) {
        try {
          showGlobalMessage(decodeURIComponent(msg), 'error')
        } catch (e) {
          showGlobalMessage(msg, 'error')
        }
      }
    }
    return Promise.reject(error)
  }
)

export default service

