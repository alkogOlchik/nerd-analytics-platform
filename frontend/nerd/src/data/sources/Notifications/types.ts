export type NotificationTypeDto = "ticket_update" | "new_message" | "system" | "info"

export interface NotificationDto {
  id: string
  type: NotificationTypeDto
  title: string
  message: string
  is_read: boolean
  created_at: string
  ticket_id?: string
}
