import { useMutation, useQueryClient } from "@tanstack/react-query"
import { profileRepository } from "data/repositories/Profile"
import type { UpdateProfileRequest } from "data/repositories/Profile"
import { ME_QUERY_KEY } from "domain/Auth/useMe"

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (req: UpdateProfileRequest) => profileRepository.updateProfile(req),
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(ME_QUERY_KEY, updatedUser)
    },
  })
}