import { Navigate, Outlet } from "react-router-dom"
import { useMe } from "domain/Auth/useMe"
import { authRepository } from "data/repositories/Auth"
import { routes } from "shared/utils/routes"

export const PrivateRoute = () => {
  const { data: user, isLoading } = useMe()

  if (!authRepository.hasTokens()) {
    return <Navigate to={routes.login} replace />
  }

  if (isLoading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          background: "var(--color-bg-secondary)",
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            border: "3px solid rgba(155, 116, 245, 0.2)",
            borderTopColor: "var(--color-purple-accent)",
            animation: "spin 0.8s linear infinite",
          }}
        />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  if (!user) {
    return <Navigate to={routes.login} replace />
  }

  return <Outlet />
}
