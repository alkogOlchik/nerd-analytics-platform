import { MOCK_NOTIFICATIONS } from "./constants"
import type { NotificationDto } from "./types"

const mutableMocks: NotificationDto[] = [...MOCK_NOTIFICATIONS]

const delay = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

export const notificationsSource = {
  getNotifications: async (): Promise<NotificationDto[]> => {
    await delay(300)
    return [...mutableMocks]
  },

  markAsRead: async (id: string): Promise<void> => {
    await delay(200)
    const item = mutableMocks.find((n) => n.id === id)
    if (item) item.is_read = true
  },

  markAllAsRead: async (): Promise<void> => {
    await delay(200)
    mutableMocks.forEach((n) => {
      n.is_read = true
    })
  },
}

export type { NotificationDto, NotificationTypeDto } from "./types"
