<script setup lang="ts">
import { NTag } from 'naive-ui'

const version = '0.1.0-alpha'
</script>

<template>
  <section>
    <h1>Dashboard</h1>
    <NTag type="info">Version {{ version }}</NTag>
  </section>
</template>

<style scoped>
h1 {
  margin: 0 0 12px;
  font-size: 24px;
}
</style>
