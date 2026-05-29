import axios from "axios"

const BASE_URL = import.meta.env.VITE_API_URL as string

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
})

const getAccessToken = () => localStorage.getItem("access_token")
const getRefreshToken = () => localStorage.getItem("refresh_token")
const setTokens = (access: string, refresh: string) => {
  localStorage.setItem("access_token", access)
  localStorage.setItem("refresh_token", refresh)
}
const clearTokens = () => {
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let isRefreshing = false
const queue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

const processQueue = (error: unknown, token: string | null) => {
  queue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)))
  queue.length = 0
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    const axiosError = error as {
      response?: { status?: number }
      config?: { _retry?: boolean; headers?: Record<string, string> }
    }

    if (axiosError.response?.status !== 401 || axiosError.config?._retry) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject })
      }).then((token) => {
        if (axiosError.config) axiosError.config.headers!.Authorization = `Bearer ${token}`
        return apiClient(axiosError.config as Parameters<typeof apiClient>[0])
      })
    }

    axiosError.config!._retry = true
    isRefreshing = true

    try {
      const refreshToken = getRefreshToken()
      const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
        `${BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken },
      )
      setTokens(data.access_token, data.refresh_token)
      processQueue(null, data.access_token)
      if (axiosError.config) {
        axiosError.config.headers!.Authorization = `Bearer ${data.access_token}`
      }
      return apiClient(axiosError.config as Parameters<typeof apiClient>[0])
    } catch (refreshError) {
      processQueue(refreshError, null)
      clearTokens()
      window.location.href = "/login"
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)
