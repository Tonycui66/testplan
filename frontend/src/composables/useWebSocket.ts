import { onMounted, onUnmounted, ref } from 'vue'

export function useWebSocket(path: string) {
  const messages = ref<string[]>([])
  const connected = ref(false)
  const error = ref('')
  let socket: globalThis.WebSocket | null = null
  let reconnectTimer: number | null = null
  let heartbeatTimer: number | null = null

  function token() {
    return localStorage.getItem('access_token') ?? ''
  }

  function cleanup() {
    if (reconnectTimer !== null) window.clearTimeout(reconnectTimer)
    if (heartbeatTimer !== null) window.clearInterval(heartbeatTimer)
    socket?.close()
    reconnectTimer = null
    heartbeatTimer = null
  }

  function connect() {
    const accessToken = token()
    const separator = path.includes('?') ? '&' : '?'
    const url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1${path}${separator}token=${encodeURIComponent(accessToken)}`
    socket = new globalThis.WebSocket(url)
    socket.onopen = () => {
      connected.value = true
      error.value = ''
      heartbeatTimer = window.setInterval(() => socket?.send('ping'), 30000)
    }
    socket.onmessage = (event) => {
      if (event.data !== 'pong') messages.value.push(event.data)
    }
    socket.onerror = () => {
      error.value = 'WebSocket connection error'
    }
    socket.onclose = () => {
      connected.value = false
      if (heartbeatTimer !== null) window.clearInterval(heartbeatTimer)
      reconnectTimer = window.setTimeout(connect, 2000)
    }
  }

  onMounted(connect)
  onUnmounted(cleanup)

  return { messages, connected, error, connect }
}
