import { useQuery } from "@tanstack/react-query"
import { notificationsRepository } from "data/repositories/Notifications"

export const NOTIFICATIONS_QUERY_KEY = ["notifications"] as const

export const useNotifications = () => {
  return useQuery({
    queryKey: NOTIFICATIONS_QUERY_KEY,
    queryFn: notificationsRepository.getNotifications,
    staleTime: 30 * 1000,
  })
}
