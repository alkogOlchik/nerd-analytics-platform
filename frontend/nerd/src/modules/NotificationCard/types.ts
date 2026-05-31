import type { Notification } from "data/repositories/Notifications"

export interface NotificationCardProps {
  notification: Notification
  onMarkAsRead: (id: string) => void
}
