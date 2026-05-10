import type { ReactNode } from "react"
import { NavLink, useNavigate } from "react-router-dom"
import { useAuth } from "../hooks/useAuth"

type Props = {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}

export default function Layout({ title, subtitle, actions, children }: Props) {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#111827",
        color: "white",
      }}
    >
      <header
        style={{
          borderBottom: "1px solid #1f2937",
          background: "#0f172a",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: "16px 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <div style={{ fontWeight: 700, fontSize: 18 }}>SalonFlow Admin</div>

            <nav style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <NavItem to="/">Dashboard</NavItem>
              <NavItem to="/bookings">Bookings</NavItem>
              <NavItem to="/bookings/new">New Booking</NavItem>
              <NavItem to="/barbers/blocks">Schedule Blocks</NavItem>
            </nav>
          </div>

          <button onClick={handleLogout} style={buttonDanger}>
            Logout
          </button>
        </div>
      </header>

      <main
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: 24,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            flexWrap: "wrap",
            marginBottom: 24,
          }}
        >
          <div>
            <h1 style={{ margin: 0 }}>{title}</h1>
            {subtitle && (
              <p style={{ marginTop: 8, color: "#9ca3af" }}>{subtitle}</p>
            )}
          </div>

          {actions && <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>{actions}</div>}
        </div>

        {children}
      </main>
    </div>
  )
}

function NavItem({ to, children }: { to: string; children: ReactNode }) {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        padding: "8px 12px",
        borderRadius: 8,
        textDecoration: "none",
        color: "white",
        background: isActive ? "#2563eb" : "#1f2937",
        border: isActive ? "none" : "1px solid #374151",
        fontSize: 14,
      })}
    >
      {children}
    </NavLink>
  )
}

const buttonDanger: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 8,
  border: "none",
  background: "#dc2626",
  color: "white",
  cursor: "pointer",
}