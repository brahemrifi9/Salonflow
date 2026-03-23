import { useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import dayjs from "dayjs"
import { getAdminBookings, cancelAdminBooking } from "../api/bookings"
import { getAdminBarbers } from "../api/barbers"
import type { Booking } from "../types/booking"
import type { Barber } from "../types/barber"
import Layout from "../components/Layout"

export default function Bookings() {
  const navigate = useNavigate()
  const location = useLocation()

  const successMessage = (location.state as { success?: string } | null)?.success

  const [bookings, setBookings] = useState<Booking[]>([])
  const [barbers, setBarbers] = useState<Barber[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showCancelled, setShowCancelled] = useState(true)
  const [todayOnly, setTodayOnly] = useState(false)
  const [selectedBarberId, setSelectedBarberId] = useState("")
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null)

  const loadData = async () => {
    try {
      setLoading(true)
      setError("")

      const [bookingsData, barbersData] = await Promise.all([
        getAdminBookings(),
        getAdminBarbers(),
      ])

      setBookings(bookingsData)
      setBarbers(barbersData)
    } catch (err) {
      console.error(err)
      setError("Failed to load bookings")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (successMessage) {
      navigate(location.pathname, { replace: true })
    }
  }, [successMessage, navigate, location.pathname])

  const handleCancelBooking = async (bookingId: number) => {
    const confirmed = window.confirm("Cancel this booking?")
    if (!confirmed) return

    try {
      setSuccess("")
      setActionLoadingId(bookingId)
      await cancelAdminBooking(bookingId)

      setBookings((prev) =>
        prev.map((booking) =>
          booking.id === bookingId
            ? {
                ...booking,
                cancelled_at: new Date().toISOString(),
              }
            : booking
        )
      )

      setSuccess("Booking cancelled successfully")
    } catch (err: any) {
      console.error(err)
      const detail = err?.response?.data?.detail
      alert(detail || "Failed to cancel booking")
    } finally {
      setActionLoadingId(null)
    }
  }

  const filteredBookings = useMemo(() => {
    let result = [...bookings]

    result.sort(
      (a, b) => dayjs(a.start_time).valueOf() - dayjs(b.start_time).valueOf()
    )

    if (!showCancelled) {
      result = result.filter((booking) => !booking.cancelled_at)
    }

    if (todayOnly) {
      result = result.filter((booking) =>
        dayjs(booking.start_time).isSame(dayjs(), "day")
      )
    }

    if (selectedBarberId) {
      result = result.filter(
        (booking) => String(booking.barber.id) === selectedBarberId
      )
    }

    return result
  }, [bookings, showCancelled, todayOnly, selectedBarberId])

  return (
    <Layout
      title="Bookings"
      subtitle="View and manage salon bookings"
      actions={
        <>
          <button onClick={() => navigate("/bookings/new")} style={buttonPrimary}>
            New booking
          </button>
          <button onClick={loadData} style={buttonSecondary}>
            Refresh
          </button>
        </>
      }
    >
      {successMessage && <SuccessBox message={successMessage} />}
      {success && <SuccessBox message={success} />}

      <div
        style={{
          background: "#1f2937",
          borderRadius: 12,
          padding: 16,
          marginBottom: 16,
          display: "flex",
          gap: 16,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <label style={labelStyle}>
          <input
            type="checkbox"
            checked={todayOnly}
            onChange={(e) => setTodayOnly(e.target.checked)}
          />
          Today only
        </label>

        <label style={labelStyle}>
          <input
            type="checkbox"
            checked={showCancelled}
            onChange={(e) => setShowCancelled(e.target.checked)}
          />
          Show cancelled
        </label>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "#9ca3af", fontSize: 14 }}>Barber</span>
          <select
            value={selectedBarberId}
            onChange={(e) => setSelectedBarberId(e.target.value)}
            style={selectStyle}
          >
            <option value="">All barbers</option>
            {barbers.map((barber) => (
              <option key={barber.id} value={barber.id}>
                {barber.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div
        style={{
          background: "#1f2937",
          borderRadius: 12,
          padding: 16,
          overflowX: "auto",
        }}
      >
        {loading && <p>Loading bookings...</p>}
        {!loading && error && <p style={{ color: "#f87171" }}>{error}</p>}
        {!loading && !error && filteredBookings.length === 0 && (
          <p style={{ color: "#9ca3af" }}>No bookings found.</p>
        )}

        {!loading && !error && filteredBookings.length > 0 && (
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              minWidth: 1050,
            }}
          >
            <thead>
              <tr style={{ borderBottom: "1px solid #374151" }}>
                <th style={thStyle}>Date</th>
                <th style={thStyle}>Time</th>
                <th style={thStyle}>Client</th>
                <th style={thStyle}>Phone</th>
                <th style={thStyle}>Barber</th>
                <th style={thStyle}>Service</th>
                <th style={thStyle}>Ref</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredBookings.map((booking) => {
                const isCancelled = !!booking.cancelled_at
                const isCancelling = actionLoadingId === booking.id

                return (
                  <tr
                    key={booking.id}
                    style={{
                      borderBottom: "1px solid #374151",
                      opacity: isCancelled ? 0.65 : 1,
                    }}
                  >
                    <td style={tdStyle}>{dayjs(booking.start_time).format("DD/MM/YYYY")}</td>
                    <td style={tdStyle}>{dayjs(booking.start_time).format("HH:mm")}</td>
                    <td style={tdStyle}>{booking.cliente?.nombre ?? "-"}</td>
                    <td style={tdStyle}>{booking.cliente?.telefono ?? "-"}</td>
                    <td style={tdStyle}>{booking.barber?.name ?? "-"}</td>
                    <td style={tdStyle}>{booking.service?.name ?? "-"}</td>
                    <td style={tdStyle}>{booking.booking_ref}</td>
                    <td style={tdStyle}>
                      <span
                        style={{
                          padding: "6px 10px",
                          borderRadius: 999,
                          fontSize: 12,
                          fontWeight: 600,
                          background: isCancelled ? "#7f1d1d" : "#064e3b",
                          color: "white",
                        }}
                      >
                        {isCancelled ? "Cancelled" : "Active"}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      {isCancelled ? (
                        <span style={{ color: "#9ca3af", fontSize: 13 }}>
                          No actions
                        </span>
                      ) : (
                        <button
                          onClick={() => handleCancelBooking(booking.id)}
                          disabled={isCancelling}
                          style={{
                            padding: "8px 12px",
                            borderRadius: 8,
                            border: "none",
                            background: "#dc2626",
                            color: "white",
                            cursor: isCancelling ? "default" : "pointer",
                            opacity: isCancelling ? 0.7 : 1,
                          }}
                        >
                          {isCancelling ? "Cancelling..." : "Cancel"}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  )
}

function SuccessBox({ message }: { message: string }) {
  return (
    <div
      style={{
        background: "#064e3b",
        color: "white",
        padding: "12px 16px",
        borderRadius: 10,
        marginBottom: 16,
      }}
    >
      {message}
    </div>
  )
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "12px 10px",
  fontSize: 14,
  color: "#9ca3af",
  fontWeight: 600,
}

const tdStyle: React.CSSProperties = {
  padding: "14px 10px",
  fontSize: 14,
}

const labelStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: 14,
}

const selectStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid #374151",
  background: "#111827",
  color: "white",
}

const buttonPrimary: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 8,
  border: "none",
  background: "#2563eb",
  color: "white",
  cursor: "pointer",
}

const buttonSecondary: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 8,
  border: "1px solid #374151",
  background: "#1f2937",
  color: "white",
  cursor: "pointer",
}