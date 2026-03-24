import axios from "axios"

// Read from Vercel / Vite env
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// Fail fast if not defined (prevents silent bugs)
if (!API_BASE_URL) {
  throw new Error("VITE_API_BASE_URL is not defined")
}

const api = axios.create({
  baseURL: API_BASE_URL,
})

// Attach JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

// Handle auth errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token")
      window.location.href = "/login"
    }

    return Promise.reject(error)
  }
)

export default api