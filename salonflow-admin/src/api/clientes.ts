import api from "./client"
import type { Cliente } from "../types/cliente"

export const getClientes = async (): Promise<Cliente[]> => {
  const response = await api.get("/clientes")
  return response.data
}