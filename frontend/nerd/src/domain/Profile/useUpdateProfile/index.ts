import { useMutation, useQueryClient } from "@tanstack/react-query"
import { authRepository } from "data/repositories/Auth"
import type { UpdateProfileRequest } from "data/repositories/Profile"
import { ME_QUERY_KEY } from "domain/Auth/useMe"

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (req: UpdateProfileRequest) =>
      authRepository.updateMe({
        fullName: req.fullName,
        city: req.city,
        age: req.age,
        gender: req.gender,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY })
    },
  })
}
