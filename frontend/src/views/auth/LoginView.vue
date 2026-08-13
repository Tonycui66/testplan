<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput } from 'naive-ui'
</script>

<template>
  <main class="login-page">
    <NForm class="login-form">
      <h1>登录</h1>
      <NFormItem label="邮箱">
        <NInput placeholder="you@example.com" />
      </NFormItem>
      <NFormItem label="密码">
        <NInput type="password" placeholder="Password" />
      </NFormItem>
      <NButton type="primary" block>登录</NButton>
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
