import { createBrowserRouter, RouterProvider, type RouteObject } from "react-router-dom"
import { routes } from "./shared/utils/routes"
import { MainPage } from "./pages/MainPage"
import { AssistantPage } from "./pages/AssistantPage"
import { TicketsPage } from "./pages/TicketsPage"
import { FavoritesPage } from "./pages/FavoritesPage"
import { NotificationsPage } from "./pages/NotificationsPage"
import { ProfilePage } from "./pages/ProfilePage"
import { NotFoundPage } from "./pages/NotFoundPage"

const appRoutes: RouteObject[] = [
  {
    path: routes.main,
    element: <MainPage />,
  },
  {
    path: routes.assistant,
    element: <AssistantPage />,
  },
  {
    path: routes.tickets,
    element: <TicketsPage />,
  },
  {
    path: routes.favorites,
    element: <FavoritesPage />,
  },
  {
    path: routes.notifications,
    element: <NotificationsPage />,
  },
  {
    path: routes.profile,
    element: <ProfilePage />,
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
