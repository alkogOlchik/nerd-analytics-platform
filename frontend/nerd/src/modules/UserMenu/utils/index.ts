import type { User } from "domain/Auth"

export const getDisplayName = (user: User | undefined): string =>
  user?.fullName ?? user?.username ?? ""
