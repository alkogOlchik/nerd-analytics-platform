import { useQuery } from "@tanstack/react-query"
import { reviewsRepository } from "data/repositories/Reviews"

export const REVIEWS_QUERY_KEY = ["reviews"] as const

export const useReviews = (params?: { ticketId?: string }) => {
  return useQuery({
    queryKey: [...REVIEWS_QUERY_KEY, params],
    queryFn: () => reviewsRepository.getReviews(params),
    staleTime: 60 * 1000,
  })
}
