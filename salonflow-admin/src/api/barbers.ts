import api from "./client"
import type { Barber } from "../types/barber"

export const getAdminBarbers = async (): Promise<Barber[]> => {
  const response = await api.get("/admin/barbers")
  return response.data
}