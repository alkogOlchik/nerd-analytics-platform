import { notificationsSource } from "data/sources/Notifications"
import type { NotificationDto } from "data/sources/Notifications"
import type { Notification } from "./types"

const mapNotification = (dto: NotificationDto): Notification => ({
  id: dto.id,
  type: dto.type,
  title: dto.title,
  message: dto.message,
  isRead: dto.is_read,
  createdAt: dto.created_at,
  ticketId: dto.ticket_id,
})

export const notificationsRepository = {
  getNotifications: async (): Promise<Notification[]> => {
    const dtos = await notificationsSource.getNotifications()
    return dtos.map(mapNotification)
  },

  markAsRead: async (id: string): Promise<void> => {
    await notificationsSource.markAsRead(id)
  },

  markAllAsRead: async (): Promise<void> => {
    await notificationsSource.markAllAsRead()
  },
}

export type { Notification, NotificationType } from "./types"
