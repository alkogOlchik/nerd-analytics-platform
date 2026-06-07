import { apiClient } from "data/apiClient"
import type { ReviewDto, CreateReviewRequest, UpdateReviewRequest, ClassifyReviewRequest } from "./types"

export const reviewsSource = {
  getReviews: (params?: { ticket_id?: string; skip?: number; limit?: number }) =>
    apiClient
      .get<ReviewDto[]>("/reviews", { params: { limit: 100, ...params } })
      .then((r) => r.data),

  getReview: (id: string) =>
    apiClient.get<ReviewDto>(`/reviews/${id}`).then((r) => r.data),

  createReview: (req: CreateReviewRequest) =>
    apiClient.post<ReviewDto>("/reviews", req).then((r) => r.data),

  updateReview: (id: string, req: UpdateReviewRequest) =>
    apiClient.patch<ReviewDto>(`/reviews/${id}`, req).then((r) => r.data),

  classifyReview: (req: ClassifyReviewRequest) =>
    apiClient.post<ReviewDto>("/ai/classify/review", req).then((r) => r.data),
}

export type { ReviewDto, CreateReviewRequest, UpdateReviewRequest, ClassifyReviewRequest } from "./types"
