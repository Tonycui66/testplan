<script setup lang="ts">
import { computed } from 'vue'
import { useWebSocket } from '../../composables/useWebSocket'

const props = defineProps<{ runId: string; pipelineId: string }>()
const { messages, connected, error } = useWebSocket(
  `/ws/pipelines/${props.pipelineId}/runs/${props.runId}/logs`
)

const parsed = computed(() => {
  return messages.value.map((line) => {
    try {
      return JSON.parse(line) as { stream: string; content: string; timestamp: string }
    } catch {
      return { stream: 'stdout', content: line, timestamp: '' }
    }
  })
})
</script>

<template>
  <div class="log-viewer" :data-state="error || (!connected ? 'empty' : 'ok')">
    <div v-if="!connected && !error" class="state">正在连接日志...</div>
    <div v-else-if="error" class="state error">{{ error }}</div>
    <pre v-else-if="parsed.length"><code><div
      v-for="(line, index) in parsed"
      :key="index"
      :class="line.stream"
    >{{ line.content }}</div></code></pre>
    <div v-else class="state">暂无日志</div>
  </div>
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
.stdout {
  color: #e5e7eb;
}
.stderr {
  color: #f87171;
}
.state {
  padding: 20px;
  color: #9ca3af;
}
.error {
  color: #f87171;
}
</style>
