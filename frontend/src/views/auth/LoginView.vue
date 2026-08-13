<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NForm, NFormItem, NInput } from 'naive-ui'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const email = ref('admin@example.com')
const password = ref('Admin123!')
const loading = ref(false)

async function submit() {
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    await router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <NForm class="login-form" @submit.prevent="submit">
      <h1>登录</h1>
      <NFormItem label="邮箱">
        <NInput v-model:value="email" placeholder="you@example.com" />
      </NFormItem>
      <NFormItem label="密码">
        <NInput v-model:value="password" type="password" placeholder="Password" />
      </NFormItem>
      <NButton type="primary" block :loading="loading" @click="submit">登录</NButton>
    </NForm>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
  background: #f8fafc;
}

.login-form {
  width: 360px;
  padding: 28px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

h1 {
  margin: 0 0 20px;
  font-size: 22px;
}
</style>
