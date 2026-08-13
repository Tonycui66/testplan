<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <span class="brand">DevOps Platform</span>
    </header>
    <aside class="app-sidebar">
      <RouterLink to="/dashboard">Dashboard</RouterLink>
    </aside>
    <main class="app-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  grid-template-rows: 56px minmax(0, 1fr);
  min-height: 100vh;
}

.app-header {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}

.brand {
  font-weight: 700;
}

.app-sidebar {
  padding: 16px 12px;
  border-right: 1px solid #e5e7eb;
  background: #f8fafc;
}

.app-sidebar a {
  display: block;
  padding: 8px 10px;
  color: #1f2937;
  text-decoration: none;
}

.app-content {
  padding: 24px;
  background: #f9fafb;
}
</style>
