import { useMutation, useQueryClient } from "@tanstack/react-query"
import { reviewsRepository } from "data/repositories/Reviews"
import type { UpdateReviewInput } from "data/repositories/Reviews"
import { REVIEWS_QUERY_KEY } from "../useReviews"

export const useUpdateReview = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateReviewInput }) =>
      reviewsRepository.updateReview(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REVIEWS_QUERY_KEY })
    },
  })
}
