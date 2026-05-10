import api from "./client"
import type { BarberBlock } from "../types/barberBlock"

export const getBarberBlocks = async (barberId: number): Promise<BarberBlock[]> => {
  const response = await api.get(`/barbers/${barberId}/blocks`)
  return response.data
}

export const createBarberBlock = async (
  barberId: number,
  payload: { date: string; start_time: string; end_time: string; reason?: string }
): Promise<BarberBlock> => {
  const response = await api.post(`/barbers/${barberId}/blocks`, payload)
  return response.data
}

export const deleteBarberBlock = async (barberId: number, blockId: number): Promise<void> => {
  await api.delete(`/barbers/${barberId}/blocks/${blockId}`)
}
