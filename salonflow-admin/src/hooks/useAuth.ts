export function useAuth() {
  const token = localStorage.getItem("token")

  const isAuthenticated = !!token

  const saveToken = (newToken: string) => {
    localStorage.setItem("token", newToken)
  }

  const logout = () => {
    localStorage.removeItem("token")
  }

  return {
    token,
    isAuthenticated,
    saveToken,
    logout,
  }
}