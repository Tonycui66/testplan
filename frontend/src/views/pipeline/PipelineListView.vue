<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NDataTable } from 'naive-ui'
import { listPipelines, type Pipeline } from '../../api/pipelines'

const route = useRoute()
const projectId = String(route.params.id)
const pipelines = ref<Pipeline[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await listPipelines(projectId)
    pipelines.value = data.data ?? []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="toolbar">
      <h1>流水线</h1>
      <NButton type="primary" @click="load">刷新</NButton>
    </div>
    <NDataTable
      :columns="[
        { title: '名称', key: 'name' },
        { title: '启用', key: 'is_enabled', render: (row) => (row.is_enabled ? '是' : '否') },
        { title: '执行次数', key: 'run_counter' }
      ]"
      :data="pipelines"
      :loading="loading"
    />
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
h1 {
  margin: 0;
}
</style>
