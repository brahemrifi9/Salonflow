import api from "./client"
import type { LoginResponse } from "../types/user"

export const login = async (
  email: string,
  password: string
): Promise<LoginResponse> => {
  const formData = new URLSearchParams()
  formData.append("username", email)
  formData.append("password", password)

  const response = await api.post("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  })

  return response.data
}