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
import { MyReviewsPage } from "./pages/MyReviewsPage"
import { PrivateRoute } from "./shared/ui/PrivateRoute"
// import { EmployeeRoute } from "./shared/ui/EmployeeRoute"

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
    path: routes.createTicket,
    element: <CreateTicketPage />
  },
  {
    path: routes.feedback,
    element: <FeedbackPage />
  },
  {
    path: routes.ticketStatus,
    element: <TicketStatusPage />
  },
  {
    path: routes.myReviews,
    element: <MyReviewsPage />
  },
  { path: routes.analytics, element: <AnalyticsPage /> },
  {
    element: <PrivateRoute />,
    children: [
      // TODO: вернуть EmployeeRoute когда роль admin/employee будет стабильно приходить с бека
      // {
      //   element: <EmployeeRoute />,
      //   children: [
      //     { path: routes.analytics, element: <AnalyticsPage /> },
      //   ],
      // },
      { path: routes.analytics, element: <AnalyticsPage /> },
      { path: routes.profile, element: <ProfilePage /> },
      { path: routes.settings, element: <SettingsPage /> },
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
