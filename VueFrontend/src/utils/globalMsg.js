import { ref } from 'vue'

export const globalMessage = ref({
  show: false,
  text: '',
  color: 'info',
  timeout: 3000
})

export function showGlobalMessage(text, color = 'info', timeout = 3000) {
  globalMessage.value = {
    show: true,
    text,
    color,
    timeout
  }
}

