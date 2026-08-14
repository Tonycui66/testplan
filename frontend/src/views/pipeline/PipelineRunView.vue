<script setup lang="ts">
import { useRoute } from 'vue-router'
import LogViewer from '../../components/pipeline/LogViewer.vue'

const route = useRoute()
const runId = String(route.params.rid)
</script>

<template>
  <section>
    <h1>流水线执行详情</h1>
    <LogViewer :run-id="runId" />
  </section>
</template>
