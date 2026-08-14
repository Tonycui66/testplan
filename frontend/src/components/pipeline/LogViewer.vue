<script setup lang="ts">
import { useWebSocket } from '../../composables/useWebSocket'

const props = defineProps<{ runId: string }>()
const { messages } = useWebSocket(`/ws/pipelines/${props.runId}/logs`)
</script>

<template>
  <pre
    class="log-viewer"
  ><code><div v-for="(line, index) in messages" :key="index">{{ line }}</div></code></pre>
</template>

<style scoped>
.log-viewer {
  min-height: 320px;
  overflow: auto;
  padding: 12px;
  border: 1px solid #e5e7eb;
  background: #111827;
  color: #e5e7eb;
  border-radius: 8px;
}
</style>
