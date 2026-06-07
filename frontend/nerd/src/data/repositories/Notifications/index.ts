import { notificationsSource } from "data/sources/Notifications"
import type { NotificationDto } from "data/sources/Notifications"
import { MOCK_NOTIFICATIONS } from "./mocks"
import type { Notification, NotificationType } from "./types"

const IS_MOCK = import.meta.env.VITE_IS_MOCK === "true"

const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

// — Real API mapping —

const TITLE_MAP: Record<string, string> = {
  push_ticket: "Обновление по обращению",
  push_general: "Push-уведомление",
  email_ticket: "Email по обращению",
  email_general: "Email-уведомление",
}

const MESSAGE_MAP: Record<string, string> = {
  push_ticket: "Получено обновление статуса вашего обращения",
  push_general: "Системное push-уведомление от платформы",
  email_ticket: "По вашему обращению отправлено письмо",
  email_general: "На ваш email отправлено системное письмо",
}

const mapNotification = (dto: NotificationDto): Notification => {
  const key = `${dto.type}_${dto.ticket_id ? "ticket" : "general"}`
  const uiType: NotificationType = dto.ticket_id
    ? dto.type === "push"
      ? "ticket_update"
      : "new_message"
    : "info"

  return {
    id: dto.id,
    type: uiType,
    title: TITLE_MAP[key] ?? "Уведомление",
    message: MESSAGE_MAP[key] ?? "Уведомление от платформы",
    isRead: dto.is_read,
    createdAt: dto.created_at,
    ticketId: dto.ticket_id ?? undefined,
  }
}

// — Mock implementation —

const mockStore: Notification[] = [...MOCK_NOTIFICATIONS]

const mockRepository = {
  getNotifications: async (): Promise<Notification[]> => {
    await delay(300)
    return [...mockStore]
  },

  markAsRead: async (id: string): Promise<void> => {
    await delay(200)
    const item = mockStore.find((n) => n.id === id)
    if (item) item.isRead = true
  },

  markAllAsRead: async (): Promise<void> => {
    await delay(200)
    mockStore.forEach((n) => {
      n.isRead = true
    })
  },
}

// — Real implementation —

const realRepository = {
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

export const notificationsRepository = IS_MOCK ? mockRepository : realRepository

export type { Notification, NotificationType } from "./types"
