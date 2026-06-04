import { createBrowserRouter, RouterProvider, type RouteObject } from "react-router-dom"
import { routes } from "./shared/utils/routes"
import { MainPage } from "./pages/MainPage"
import { AssistantPage } from "./pages/AssistantPage"
import { TicketsPage } from "./pages/TicketsPage"
import { FavoritesPage } from "./pages/FavoritesPage"
import { NotificationsPage } from "./pages/NotificationsPage"
import { ProfilePage } from "./pages/ProfilePage"
import { NotFoundPage } from "./pages/NotFoundPage"
import { LoginPage } from "./pages/LoginPage"
import { RegisterPage } from "./pages/RegisterPage"
import { AnalyticsPage } from "./pages/AnalyticsPage"
import { PrivateRoute } from "./shared/ui/PrivateRoute"
import { EmployeeRoute } from "./shared/ui/EmployeeRoute"

const appRoutes: RouteObject[] = [
  {
    path: routes.login,
    element: <LoginPage />,
  },
  {
    path: routes.register,
    element: <RegisterPage />,
  },
  {
    path: routes.main,
    element: <MainPage />,
  },
  {
    path: routes.assistant,
    element: <AssistantPage />,
  },
  { path: routes.tickets,
    element: <TicketsPage />
  },
  {
    path: routes.notifications,
    element: <NotificationsPage />
  },
  {
    element: <PrivateRoute />,
    children: [
      {
        element: <EmployeeRoute />,
        children: [
          { path: routes.analytics, element: <AnalyticsPage /> },
        ],
      },
      { path: routes.favorites, element: <FavoritesPage /> },
      { path: routes.profile, element: <ProfilePage /> },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]

const router = createBrowserRouter(appRoutes)

function App() {
  return <RouterProvider router={router} />
}

export default App
