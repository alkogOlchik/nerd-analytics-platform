import { reviewsSource } from "data/sources/Reviews"
import type { ReviewDto } from "data/sources/Reviews"
import type { Review, CreateReviewInput, UpdateReviewInput } from "./types"

const mapReview = (dto: ReviewDto): Review => ({
  id: dto.id,
  ticketId: dto.ticket_id,
  clientId: dto.client_id,
  product: dto.product,
  rating: dto.rating,
  comment: dto.comment,
  createdAt: dto.created_at,
  aiSuggestedCategory: dto.ai_suggested_category,
  finalCategory: dto.final_category,
  isAdminChanged: dto.is_admin_changed,
  sentiment: dto.sentiment,
  keywordsPositive: dto.keywords_positive ?? [],
  keywordsNeutral: dto.keywords_neutral ?? [],
  keywordsNegative: dto.keywords_negative ?? [],
  confidence: dto.confidence,
})

export const reviewsRepository = {
  getReviews: async (params?: { ticketId?: string }): Promise<Review[]> => {
    const dtos = await reviewsSource.getReviews({ ticket_id: params?.ticketId })
    return dtos.map(mapReview)
  },

  getReview: async (id: string): Promise<Review> => {
    const dto = await reviewsSource.getReview(id)
    return mapReview(dto)
  },

  createReview: async (input: CreateReviewInput): Promise<Review> => {
    const dto = await reviewsSource.createReview({
      ticket_id: input.ticketId,
      product: input.product,
      rating: input.rating,
      comment: input.comment,
    })
    return mapReview(dto)
  },

  updateReview: async (id: string, input: UpdateReviewInput): Promise<Review> => {
    const dto = await reviewsSource.updateReview(id, {
      rating: input.rating,
      comment: input.comment,
      product: input.product,
      final_category: input.finalCategory,
      is_admin_changed: input.isAdminChanged,
    })
    return mapReview(dto)
  },
}

export type { Review, ReviewSentiment, CreateReviewInput, UpdateReviewInput } from "./types"
