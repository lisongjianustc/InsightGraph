<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { watch, onMounted } from 'vue'
import { useTheme } from './composables/useTheme'

const route = useRoute()
const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})

watch(() => route.path, (path) => {
  if (path === '/spotlight') {
    document.body.style.backgroundColor = 'transparent'
  } else {
    // For non-spotlight pages, background color is managed by main.css CSS variables now.
    document.body.style.backgroundColor = ''
  }
}, { immediate: true })
</script>

<template>
  <el-config-provider>
    <RouterView />
  </el-config-provider>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  /* background-color: #f5f7fa; managed by script now */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
</style>
