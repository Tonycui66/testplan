<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NButton, NDataTable, NInput } from 'naive-ui'
import { listProjects, type Project } from '../../api/projects'

const projects = ref<Project[]>([])
const loading = ref(false)
const search = ref('')

async function load() {
  loading.value = true
  try {
    const data = await listProjects(search.value)
    projects.value = data.items
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="toolbar">
      <h1>项目</h1>
      <NInput v-model:value="search" placeholder="搜索项目" @keyup.enter="load" />
      <NButton type="primary" @click="load">查询</NButton>
    </div>
    <NDataTable
      :columns="[
        { title: '名称', key: 'name' },
        { title: 'Key', key: 'key' },
        {
          title: '状态',
          key: 'is_archived',
          render: (row) => (row.is_archived ? 'Archived' : 'Active')
        }
      ]"
      :data="projects"
      :loading="loading"
    />
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

h1 {
  margin: 0;
  font-size: 24px;
}
</style>
