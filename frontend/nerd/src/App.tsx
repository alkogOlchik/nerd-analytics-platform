import { createBrowserRouter, RouterProvider, type RouteObject } from "react-router-dom"
import { routes } from "./shared/utils/routes"
import { MainPage } from "./pages/MainPage"
import { AssistantPage } from "./pages/AssistantPage"
import { TicketsPage } from "./pages/TicketsPage"
import { NotificationsPage } from "./pages/NotificationsPage"
import { ProfilePage } from "./pages/ProfilePage"
import { SettingsPage } from "./pages/SettingsPage"
import { NotFoundPage } from "./pages/NotFoundPage"
import { LoginPage } from "./pages/LoginPage"
import { RegisterPage } from "./pages/RegisterPage"
import { AnalyticsPage } from "./pages/AnalyticsPage"
import { CreateTicketPage } from "./pages/CreateTicketPage"
import { FeedbackPage } from "./pages/FeedbackPage"
import { TicketStatusPage } from "./pages/TicketStatusPage"
import { PrivateRoute } from "./shared/ui/PrivateRoute"

const appRoutes: RouteObject[] = [
  // Публичные маршруты — доступны без авторизации
  { path: routes.login, element: <LoginPage /> },
  { path: routes.register, element: <RegisterPage /> },
  { path: routes.main, element: <MainPage /> },
  { path: routes.assistant, element: <AssistantPage /> },

  // Создание обращения и отслеживание статуса — доступны без авторизации,
  // при анонимном создании обращения запрашивается email (временный токен).
  { path: routes.createTicket, element: <CreateTicketPage /> },
  { path: routes.ticketStatus, element: <TicketStatusPage /> },

  // Приватные маршруты — требуют авторизации
  {
    element: <PrivateRoute />,
    children: [
      { path: routes.tickets, element: <TicketsPage /> },
      { path: routes.notifications, element: <NotificationsPage /> },
      { path: routes.feedback, element: <FeedbackPage /> },
      { path: routes.analytics, element: <AnalyticsPage /> },
      { path: routes.profile, element: <ProfilePage /> },
      { path: routes.settings, element: <SettingsPage /> },
    ],
  },

  { path: "*", element: <NotFoundPage /> },
]

const router = createBrowserRouter(appRoutes)

function App() {
  return <RouterProvider router={router} />
}

export default App