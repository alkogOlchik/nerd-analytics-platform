import { apiClient } from "data/apiClient"
import type { NotificationDto } from "./types"

export const notificationsSource = {
  getNotifications: () =>
    apiClient.get<NotificationDto[]>("/notifications", { params: { limit: 100 } }).then((r) => r.data),

  getNotification: (id: string) =>
    apiClient.get<NotificationDto>(`/notifications/${id}`).then((r) => r.data),

  markAsRead: (id: string): Promise<void> =>
    apiClient.patch(`/notifications/${id}`, { is_read: true }).then(() => undefined),

  markAllAsRead: (): Promise<void> =>
    apiClient.post("/notifications/read-all").then(() => undefined),
}

export type { NotificationDto, NotificationTypeDto } from "./types"
