import { useEffect, useState } from "react"
import dayjs from "dayjs"
import { getAdminBarbers } from "../api/barbers"
import { getBarberBlocks, createBarberBlock, deleteBarberBlock } from "../api/barberBlocks"
import type { Barber } from "../types/barber"
import type { BarberBlock, ConflictingBooking } from "../types/barberBlock"
import Layout from "../components/Layout"

export default function BarberBlocks() {
  const [barbers, setBarbers] = useState<Barber[]>([])
  const [selectedBarberId, setSelectedBarberId] = useState<number | "">("")
  const [blocks, setBlocks] = useState<BarberBlock[]>([])
  const [loadingBlocks, setLoadingBlocks] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [conflicts, setConflicts] = useState<ConflictingBooking[]>([])

  const [form, setForm] = useState({
    date: dayjs().format("YYYY-MM-DD"),
    start_time: "09:00",
    end_time: "10:00",
    reason: "",
  })

  useEffect(() => {
    getAdminBarbers().then(setBarbers).catch(() => setError("Failed to load barbers"))
  }, [])

  useEffect(() => {
    if (selectedBarberId === "") {
      setBlocks([])
      return
    }
    setLoadingBlocks(true)
    setError("")
    getBarberBlocks(selectedBarberId as number)
      .then(setBlocks)
      .catch(() => setError("Failed to load blocks"))
      .finally(() => setLoadingBlocks(false))
  }, [selectedBarberId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedBarberId === "") return
    setError("")
    setSuccess("")
    setConflicts([])
    setSubmitting(true)
    try {
      const block = await createBarberBlock(selectedBarberId as number, {
        date: form.date,
        start_time: form.start_time,
        end_time: form.end_time,
        reason: form.reason || undefined,
      })
      setBlocks((prev) => [...prev, block].sort((a, b) => {
        if (a.date !== b.date) return a.date.localeCompare(b.date)
        return a.start_time.localeCompare(b.start_time)
      }))
      setSuccess("Block created successfully")
      setForm({ date: dayjs().format("YYYY-MM-DD"), start_time: "09:00", end_time: "10:00", reason: "" })
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (err?.response?.status === 409 && detail?.conflicts) {
        setConflicts(detail.conflicts)
        setError(detail.message || "Conflicting bookings exist — cancel them first")
      } else if (typeof detail === "string") {
        setError(detail)
      } else {
        setError("Failed to create block")
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (blockId: number) => {
    if (!window.confirm("Delete this block?")) return
    if (selectedBarberId === "") return
    setDeletingId(blockId)
    setError("")
    setSuccess("")
    try {
      await deleteBarberBlock(selectedBarberId as number, blockId)
      setBlocks((prev) => prev.filter((b) => b.id !== blockId))
      setSuccess("Block removed")
    } catch {
      setError("Failed to delete block")
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <Layout title="Schedule Blocks" subtitle="Block barber availability for specific time windows">
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

        {/* Barber selector */}
        <div style={card}>
          <label style={labelStyle}>
            <span style={labelText}>Barber</span>
            <select
              value={selectedBarberId}
              onChange={(e) => setSelectedBarberId(e.target.value === "" ? "" : Number(e.target.value))}
              style={selectStyle}
            >
              <option value="">— select a barber —</option>
              {barbers.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </label>
        </div>

        {selectedBarberId !== "" && (
          <>
            {/* Create block form */}
            <div style={card}>
              <h2 style={{ margin: "0 0 16px", fontSize: 16, color: "#e5e7eb" }}>New Block</h2>
              <form onSubmit={handleSubmit} style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "flex-end" }}>
                <label style={labelStyle}>
                  <span style={labelText}>Date</span>
                  <input
                    type="date"
                    required
                    value={form.date}
                    onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
                    style={inputStyle}
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelText}>Start time</span>
                  <input
                    type="time"
                    required
                    value={form.start_time}
                    onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
                    style={inputStyle}
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelText}>End time</span>
                  <input
                    type="time"
                    required
                    value={form.end_time}
                    onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
                    style={inputStyle}
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelText}>Reason (optional)</span>
                  <input
                    type="text"
                    placeholder="e.g. doctor appointment"
                    value={form.reason}
                    onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
                    style={{ ...inputStyle, minWidth: 220 }}
                  />
                </label>

                <button type="submit" disabled={submitting} style={buttonPrimary}>
                  {submitting ? "Creating..." : "Create block"}
                </button>
              </form>

              {error && (
                <div style={errorBox}>
                  <p style={{ margin: "0 0 8px", fontWeight: 600 }}>{error}</p>
                  {conflicts.length > 0 && (
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                      <thead>
                        <tr>
                          <th style={conflictTh}>Ref</th>
                          <th style={conflictTh}>Client</th>
                          <th style={conflictTh}>Phone</th>
                          <th style={conflictTh}>Start</th>
                          <th style={conflictTh}>End</th>
                        </tr>
                      </thead>
                      <tbody>
                        {conflicts.map((c) => (
                          <tr key={c.id}>
                            <td style={conflictTd}>{c.booking_ref}</td>
                            <td style={conflictTd}>{c.cliente_nombre}</td>
                            <td style={conflictTd}>{c.cliente_telefono}</td>
                            <td style={conflictTd}>{dayjs(c.start_time).format("HH:mm")}</td>
                            <td style={conflictTd}>{dayjs(c.end_time).format("HH:mm")}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
              {success && <div style={successBox}>{success}</div>}
            </div>

            {/* Existing blocks */}
            <div style={card}>
              <h2 style={{ margin: "0 0 16px", fontSize: 16, color: "#e5e7eb" }}>Existing Blocks</h2>
              {loadingBlocks && <p style={{ color: "#9ca3af" }}>Loading...</p>}
              {!loadingBlocks && blocks.length === 0 && (
                <p style={{ color: "#9ca3af" }}>No blocks for this barber.</p>
              )}
              {!loadingBlocks && blocks.length > 0 && (
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #374151" }}>
                      <th style={thStyle}>Date</th>
                      <th style={thStyle}>Start</th>
                      <th style={thStyle}>End</th>
                      <th style={thStyle}>Reason</th>
                      <th style={thStyle}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {blocks.map((block) => (
                      <tr key={block.id} style={{ borderBottom: "1px solid #374151" }}>
                        <td style={tdStyle}>{dayjs(block.date).format("DD/MM/YYYY")}</td>
                        <td style={tdStyle}>{block.start_time.slice(0, 5)}</td>
                        <td style={tdStyle}>{block.end_time.slice(0, 5)}</td>
                        <td style={tdStyle}>{block.reason ?? <span style={{ color: "#6b7280" }}>—</span>}</td>
                        <td style={tdStyle}>
                          <button
                            onClick={() => handleDelete(block.id)}
                            disabled={deletingId === block.id}
                            style={buttonDanger}
                          >
                            {deletingId === block.id ? "Removing..." : "Remove"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}

const card: React.CSSProperties = {
  background: "#1f2937",
  borderRadius: 12,
  padding: 20,
}

const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 6,
}

const labelText: React.CSSProperties = {
  fontSize: 13,
  color: "#9ca3af",
  fontWeight: 500,
}

const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid #374151",
  background: "#111827",
  color: "white",
  fontSize: 14,
}

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  minWidth: 200,
}

const buttonPrimary: React.CSSProperties = {
  padding: "10px 16px",
  borderRadius: 8,
  border: "none",
  background: "#2563eb",
  color: "white",
  cursor: "pointer",
  alignSelf: "flex-end",
}

const buttonDanger: React.CSSProperties = {
  padding: "6px 12px",
  borderRadius: 8,
  border: "none",
  background: "#dc2626",
  color: "white",
  cursor: "pointer",
  fontSize: 13,
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 10px",
  fontSize: 13,
  color: "#9ca3af",
  fontWeight: 600,
}

const tdStyle: React.CSSProperties = {
  padding: "12px 10px",
  fontSize: 14,
}

const errorBox: React.CSSProperties = {
  marginTop: 16,
  background: "#7f1d1d",
  color: "white",
  padding: "12px 16px",
  borderRadius: 10,
}

const successBox: React.CSSProperties = {
  marginTop: 16,
  background: "#064e3b",
  color: "white",
  padding: "12px 16px",
  borderRadius: 10,
}

const conflictTh: React.CSSProperties = {
  textAlign: "left",
  padding: "6px 8px",
  fontWeight: 600,
  color: "#fca5a5",
}

const conflictTd: React.CSSProperties = {
  padding: "6px 8px",
  color: "#fef2f2",
}
