import { onMounted, onUnmounted, ref } from 'vue'

export function useWebSocket(path: string) {
  const messages = ref<string[]>([])
  let socket: globalThis.WebSocket | null = null

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    socket = new globalThis.WebSocket(`${protocol}//${window.location.host}/api/v1${path}`)
    socket.onmessage = (event) => {
      messages.value.push(event.data)
    }
  }

  onMounted(connect)
  onUnmounted(() => socket?.close())

  return { messages, connect }
}
