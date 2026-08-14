<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NInput, NForm, NFormItem } from 'naive-ui'
import { createPipeline } from '../../api/pipelines'

const route = useRoute()
const projectId = String(route.params.id)
const name = ref('')
const description = ref('')
const loading = ref(false)

async function save() {
  loading.value = true
  try {
    await createPipeline(projectId, {
      name: name.value,
      description: description.value,
      stages: [
        {
          name: 'Build',
          order: 0,
          condition: 'always',
          jobs: [
            { name: 'echo', image: 'alpine:3.18', script: 'echo hello', order: 0, variables: {} }
          ]
        }
      ]
    })
    name.value = ''
    description.value = ''
  } finally {
    loading.value = false
  }
}
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
