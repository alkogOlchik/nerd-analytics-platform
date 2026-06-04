import { Navigate, Outlet } from "react-router-dom"
import { useMe } from "domain/Auth/useMe"
import { routes } from "shared/utils/routes"

export const EmployeeRoute = () => {
  const { data: user, isLoading } = useMe()

  if (isLoading) return null

  if (user?.role !== "employee") {
    return <Navigate to={routes.main} replace />
  }

  return <Outlet />
}
