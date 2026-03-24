import api from "./client"
import type { Service } from "../types/service"

export const getServices = async (): Promise<Service[]> => {
  const response = await api.get("/admin/services")
  return response.data
}