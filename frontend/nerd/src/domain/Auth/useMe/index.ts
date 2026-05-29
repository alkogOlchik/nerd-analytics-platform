import { useQuery } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"

export const ME_QUERY_KEY = ["me"] as const

export const useMe = () =>
  useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: authRepository.me,
    enabled: authRepository.hasTokens(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })

export type { User } from "./types"
