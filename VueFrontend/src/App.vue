<script setup>
import { globalMessage } from './utils/globalMsg'
</script>

<template>
  <v-app>
    <router-view />
    <v-snackbar
      v-model="globalMessage.show"
      :color="globalMessage.color"
      :timeout="globalMessage.timeout"
    >
      {{ globalMessage.text }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="globalMessage.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<style>
/* Global styles can go here or in assets/main.css */
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
}
</style>
