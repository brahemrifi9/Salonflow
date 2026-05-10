export type BarberBlock = {
  id: number
  barber_id: number
  date: string
  start_time: string
  end_time: string
  reason: string | null
  created_at: string
}

export type ConflictingBooking = {
  id: number
  booking_ref: string
  start_time: string
  end_time: string
  cliente_nombre: string
  cliente_telefono: string
}
