export type Cliente = {
  id: number
  nombre: string
  telefono: string
  email?: string
}

export type Barber = {
  id: number
  name: string
}

export type Service = {
  id: number
  name: string
}

export type Booking = {
  id: number
  cliente: Cliente
  barber: Barber
  service: Service
  start_time: string
  end_time: string
  booking_ref: string
  cancelled_at: string | null
}

export type LoginResponse = {
  access_token: string
  token_type: string
}

export type AdminUser = {
  id: number
  email: string
  is_admin: boolean
}