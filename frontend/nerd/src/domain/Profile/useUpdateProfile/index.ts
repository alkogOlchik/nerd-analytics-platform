import { useMutation, useQueryClient } from "@tanstack/react-query"
import { profileRepository } from "data/repositories/Profile"
import type { UpdateProfileRequest } from "data/repositories/Profile"
import { PROFILE_LOCAL_QUERY_KEY } from "../useProfile"

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (req: UpdateProfileRequest) => {
      profileRepository.saveLocalData(req)
      return Promise.resolve()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILE_LOCAL_QUERY_KEY })
    },
  })
}
