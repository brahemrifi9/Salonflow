import { useNavigate } from "react-router-dom"
import Layout from "../components/Layout"

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <Layout
      title="Dashboard"
      subtitle="Quick access to your admin tools"
      actions={
        <button onClick={() => navigate("/bookings/new")} style={buttonPrimary}>
          New booking
        </button>
      }
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 16,
        }}
      >
        <div
          style={{
            background: "#1f2937",
            borderRadius: 12,
            padding: 20,
          }}
        >
          <h2 style={{ marginTop: 0 }}>Bookings</h2>
          <p style={{ color: "#9ca3af" }}>
            View today’s and upcoming bookings.
          </p>

          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button
              onClick={() => navigate("/bookings")}
              style={buttonPrimary}
            >
              Open bookings
            </button>

            <button
              onClick={() => navigate("/bookings/new")}
              style={buttonSecondary}
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
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