import { useState, type FormEvent } from "react"
import { useNavigate } from "react-router-dom"
import { login } from "../api/auth"
import { useAuth } from "../hooks/useAuth"

export default function Login() {
  const navigate = useNavigate()
  const { saveToken } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const data = await login(email, password)

      if (!data?.access_token) {
        throw new Error("No token received")
      }

      saveToken(data.access_token)
      navigate("/")
    } catch (err: any) {
      if (err?.response?.status === 401) {
        setError("Invalid email or password")
      } else {
        setError("Login failed. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: "#111827",
        color: "white",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: "100%",
          maxWidth: 380,
          padding: 24,
          borderRadius: 12,
          background: "#1f2937",
          display: "flex",
          flexDirection: "column",
          gap: 16,
          boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 28 }}>SalonFlow Admin</h1>
          <p style={{ marginTop: 8, color: "#9ca3af" }}>Sign in to continue</p>
        </div>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            padding: 12,
            borderRadius: 8,
            border: "1px solid #374151",
            background: "#111827",
            color: "white",
            outline: "none",
          }}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            padding: 12,
            borderRadius: 8,
            border: "1px solid #374151",
            background: "#111827",
            color: "white",
            outline: "none",
          }}
        />

        {error && (
          <div style={{ color: "#f87171", fontSize: 14 }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: 12,
            borderRadius: 8,
            border: "none",
            background: "#2563eb",
            color: "white",
            fontWeight: 600,
            cursor: "pointer",
            opacity: loading ? 0.8 : 1,
          }}
        >
          {loading ? "Signing in..." : "Login"}
        </button>
      </form>
    </div>
  )
}