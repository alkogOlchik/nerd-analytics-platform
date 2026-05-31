export type NotificationType = "ticket_update" | "new_message" | "system" | "info"

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  isRead: boolean
  createdAt: string
  ticketId?: string
}
