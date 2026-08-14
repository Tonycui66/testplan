<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NInput, NForm, NFormItem } from 'naive-ui'
import { createPipeline, getPipeline, updatePipeline } from '../../api/pipelines'

const route = useRoute()
const projectId = String(route.params.id)
const pipelineId = String(route.params.pid)
const name = ref('')
const description = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await getPipeline(projectId, pipelineId)
    const detail = data.data
    name.value = detail.name
    description.value = detail.description ?? ''
  } finally {
    loading.value = false
  }
}

async function save() {
  loading.value = true
  try {
    if (pipelineId === 'new') {
      await createPipeline(projectId, {
        name: name.value,
        description: description.value,
        stages: []
      })
    } else {
      await updatePipeline(projectId, pipelineId, {
        name: name.value,
        description: description.value
      })
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (pipelineId !== 'new') load()
})
</script>

<template>
  <NForm>
    <h1>流水线编辑</h1>
    <NFormItem label="名称">
      <NInput v-model:value="name" />
    </NFormItem>
    <NFormItem label="描述">
      <NInput v-model:value="description" />
    </NFormItem>
    <NButton type="primary" :loading="loading" @click="save">保存</NButton>
  </NForm>
</template>
