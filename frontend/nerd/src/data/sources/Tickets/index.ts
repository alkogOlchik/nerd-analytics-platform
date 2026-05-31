import { MOCK_TICKETS } from "./constants"
import type { TicketDto } from "./types"

const delay = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

export const ticketsSource = {
  getTickets: async (): Promise<TicketDto[]> => {
    await delay(300)
    return [...MOCK_TICKETS]
  },
}

export type { TicketDto }
