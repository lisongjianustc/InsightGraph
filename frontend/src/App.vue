<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { watch } from 'vue'

const route = useRoute()

watch(() => route.path, (path) => {
  if (path === '/spotlight') {
    document.body.style.backgroundColor = 'transparent'
  } else {
    document.body.style.backgroundColor = '#f5f7fa'
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
