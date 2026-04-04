import api from "./client"
import type { Booking } from "../types/booking"

export const getAdminBookings = async (): Promise<Booking[]> => {
  const response = await api.get("/admin/bookings")
  return response.data
}

export const cancelAdminBooking = async (bookingId: number) => {
  const response = await api.patch(`/bookings/${bookingId}/cancel`)
  return response.data
}

export const createAdminBooking = async (payload: {
  cliente_id: number
  barber_id: number
  service_id: number
  start_time: string
}) => {
  const response = await api.post("/bookings/", payload)
  return response.data
}

export const createBooking = async (data: {
  cliente_id: number
  barber_id: number
  service_id: number
  start_time: string
}) => {
  const response = await api.post("/bookings/", data)
  return response.data
}