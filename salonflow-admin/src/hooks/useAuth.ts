import { useState, useEffect } from "react"
import api from "../api/client"
import type { AdminUser } from "../types/user"
 
export function useAuth() {
  const token = localStorage.getItem("token")
  const isAuthenticated = !!token
  const [businessId, setBusinessId] = useState<number | null>(null)
 
  useEffect(() => {
    if (token) {
      api.get<AdminUser>("/auth/me").then((res) => {
        setBusinessId(res.data.business_id)
        localStorage.setItem("business_id", String(res.data.business_id))
      }).catch(() => {})
    }
  }, [token])
 
  const saveToken = (newToken: string) => {
    localStorage.setItem("token", newToken)
  }
 
  const logout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("business_id")
  }
 
  const getBusinessId = (): number => {
    return businessId ?? Number(localStorage.getItem("business_id")) ?? 1
  }
 
  return {
    token,
    isAuthenticated,
    saveToken,
    logout,
    getBusinessId,
  }
}