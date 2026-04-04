import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { getClientes } from "../api/clientes"
import { getAdminBarbers } from "../api/barbers"
import { getServices } from "../api/services"
import { createBooking } from "../api/bookings"
import api from "../api/client"
import type { Cliente } from "../types/cliente"
import type { Barber } from "../types/barber"
import type { Service } from "../types/service"
import Layout from "../components/Layout"
import { useAuth } from "../hooks/useAuth"

type AvailabilitySlot = {
  start_time_madrid: string
}

type AvailabilityResponse = {
  slots: AvailabilitySlot[]
}

export default function NewBooking() {
  const navigate = useNavigate()

  const { getBusinessId } = useAuth()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [barbers, setBarbers] = useState<Barber[]>([])
  const [services, setServices] = useState<Service[]>([])

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")

  const [clienteId, setClienteId] = useState("")
  const [barberId, setBarberId] = useState("")
  const [serviceId, setServiceId] = useState("")
  const [date, setDate] = useState("")
  const [time, setTime] = useState("")
  const [availableSlots, setAvailableSlots] = useState<string[]>([])

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        setError("")

        const [clientesData, barbersData, servicesData] = await Promise.all([
          getClientes(),
          getAdminBarbers(),
          getServices(),
        ])

        setClientes(clientesData)
        setBarbers(barbersData)
        setServices(servicesData)
      } catch (err) {
        console.error(err)
        setError("Failed to load form data")
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  useEffect(() => {
    if (!barberId || !serviceId || !date) {
      setAvailableSlots([])
      setTime("")
      return
    }

    const fetchSlots = async () => {
      try {
        const response = await api.get<AvailabilityResponse>("/public/availability", {
          params: {
            business_id: getBusinessId(),
            barber_id: barberId,
            service_id: serviceId,
            date,
          },
        })

        const slotTimes = response.data.slots.map((slot) =>
          new Date(slot.start_time_madrid).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          })
        )

        setAvailableSlots(slotTimes)
        setTime("")
      } catch (err) {
        console.error(err)
        setAvailableSlots([])
        setTime("")
      }
    }

    fetchSlots()
  }, [barberId, serviceId, date])

  const minDate = useMemo(() => {
    const today = new Date()
    return today.toISOString().split("T")[0]
  }, [])

  const isFormValid =
    !!clienteId &&
    !!barberId &&
    !!serviceId &&
    !!date &&
    !!time &&
    availableSlots.includes(time)

  const handleSubmit = async () => {
    try {
      setError("")

      if (!isFormValid) {
        setError("Please complete all fields with a valid available time")
        return
      }

      setSubmitting(true)

      const start_time = new Date(`${date}T${time}`).toISOString()

      await createBooking({
        cliente_id: Number(clienteId),
        barber_id: Number(barberId),
        service_id: Number(serviceId),
        start_time,
      })

      navigate("/bookings", {
        state: { success: "Booking created successfully" },
      })
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || "Failed to create booking")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Layout
      title="New Booking"
      subtitle="Create a booking manually from the admin dashboard"
    >
      <div
        style={{
          background: "#1f2937",
          borderRadius: 12,
          padding: 20,
          maxWidth: 720,
        }}
      >
        {loading && <p>Loading form data...</p>}

        {!loading && error && (
          <div
            style={{
              background: "#7f1d1d",
              color: "white",
              padding: "12px 16px",
              borderRadius: 10,
              marginBottom: 16,
            }}
          >
            {error}
          </div>
        )}

        {!loading && (
          <div style={{ display: "grid", gap: 16 }}>
            <div>
              <label style={labelStyle}>Client</label>
              <select
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
                style={inputStyle}
              >
                <option value="">Select a client</option>
                {clientes.map((cliente) => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nombre} - {cliente.telefono}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Barber</label>
              <select
                value={barberId}
                onChange={(e) => setBarberId(e.target.value)}
                style={inputStyle}
              >
                <option value="">Select a barber</option>
                {barbers.map((barber) => (
                  <option key={barber.id} value={barber.id}>
                    {barber.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Service</label>
              <select
                value={serviceId}
                onChange={(e) => setServiceId(e.target.value)}
                style={inputStyle}
              >
                <option value="">Select a service</option>
                {services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name} ({service.duration_minutes} min)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Date</label>
              <input
                type="date"
                value={date}
                min={minDate}
                onChange={(e) => setDate(e.target.value)}
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Time</label>
              <select
                value={time}
                onChange={(e) => setTime(e.target.value)}
                style={inputStyle}
                disabled={!barberId || !serviceId || !date || availableSlots.length === 0}
              >
                <option value="">
                  {!barberId || !serviceId || !date
                    ? "Select barber, service and date first"
                    : availableSlots.length === 0
                    ? "No available slots"
                    : "Select a time"}
                </option>
                {availableSlots.map((slot) => (
                  <option key={slot} value={slot}>
                    {slot}
                  </option>
                ))}
              </select>
            </div>

            <button
              style={{
                ...buttonPrimary,
                opacity: submitting || !isFormValid ? 0.7 : 1,
                cursor: submitting || !isFormValid ? "default" : "pointer",
              }}
              onClick={handleSubmit}
              disabled={submitting || !isFormValid}
            >
              {submitting ? "Creating..." : "Create booking"}
            </button>
          </div>
        )}
      </div>
    </Layout>
  )
}

const labelStyle: React.CSSProperties = {
  display: "block",
  marginBottom: 8,
  fontSize: 14,
  color: "#9ca3af",
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: 8,
  border: "1px solid #374151",
  background: "#111827",
  color: "white",
  outline: "none",
}

const buttonPrimary: React.CSSProperties = {
  padding: "12px 16px",
  borderRadius: 8,
  border: "none",
  background: "#2563eb",
  color: "white",
  fontWeight: 600,
}