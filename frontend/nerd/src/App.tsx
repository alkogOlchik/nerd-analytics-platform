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
import { PrivateRoute } from "./shared/ui/PrivateRoute"

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
    element: <PrivateRoute />,
    children: [
      { path: routes.assistant, element: <AssistantPage /> },
      { path: routes.tickets, element: <TicketsPage /> },
      { path: routes.favorites, element: <FavoritesPage /> },
      { path: routes.notifications, element: <NotificationsPage /> },
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
