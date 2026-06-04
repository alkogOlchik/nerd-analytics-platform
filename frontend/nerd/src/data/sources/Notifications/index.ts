import { apiClient } from "data/apiClient"
import type { NotificationDto } from "./types"

const READ_IDS_KEY = "nerd_notifications_read"
const READ_ALL_TS_KEY = "nerd_notifications_read_all"

const getReadIds = (): Set<string> => {
  try {
    return new Set<string>(JSON.parse(localStorage.getItem(READ_IDS_KEY) ?? "[]"))
  } catch {
    return new Set()
  }
}

const saveReadIds = (ids: Set<string>) => {
  localStorage.setItem(READ_IDS_KEY, JSON.stringify([...ids]))
}

export const notificationsSource = {
  getNotifications: () =>
    apiClient.get<NotificationDto[]>("/notifications", { params: { limit: 100 } }).then((r) => r.data),

  getNotification: (id: string) =>
    apiClient.get<NotificationDto>(`/notifications/${id}`).then((r) => r.data),

  markAsRead: (id: string): Promise<void> => {
    const ids = getReadIds()
    ids.add(id)
    saveReadIds(ids)
    return Promise.resolve()
  },

  markAllAsRead: (): Promise<void> => {
    localStorage.setItem(READ_ALL_TS_KEY, new Date().toISOString())
    return Promise.resolve()
  },

  computeIsRead: (id: string, createdAt: string): boolean => {
    const readIds = getReadIds()
    if (readIds.has(id)) return true
    const readAllBefore = localStorage.getItem(READ_ALL_TS_KEY)
    if (readAllBefore && createdAt <= readAllBefore) return true
    return false
  },
}

export type { NotificationDto, NotificationTypeDto } from "./types"
