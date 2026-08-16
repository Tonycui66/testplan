<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { NButton, NDataTable } from 'naive-ui'
import { listArtifactRepositories } from '../../api/phase3'

const route = useRoute()
const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await listArtifactRepositories(String(route.params.id))
    rows.value = data.data ?? []
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <section>
    <h1>制品仓库</h1>
    <NButton @click="load">刷新</NButton>
    <NDataTable
      :columns="[
        { title: '名称', key: 'name' },
        { title: '类型', key: 'type' }
      ]"
      :data="rows"
      :loading="loading"
    />
  </section>
</template>
