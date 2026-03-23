export type Booking = {
  id: number
  booking_ref: string
  cliente_id: number
  barber_id: number
  service_id: number
  start_time: string
  end_time: string
  duration_minutes: number
  cancelled_at: string | null
  cliente: {
    id: number
    nombre: string
    telefono: string
    email?: string | null
  }
  barber: {
    id: number
    name: string
    is_active: boolean
  }
  service: {
    id: number
    name: string
    duration_minutes: number
    price_cents: number | null
    is_active: boolean
  }
}