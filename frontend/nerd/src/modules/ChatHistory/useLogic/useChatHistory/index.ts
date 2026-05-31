import type { ChatHistoryProps } from "modules/ChatHistory/types"

export const useChatHistory = ({
  onSelect,
  onNewChat,
}: Pick<ChatHistoryProps, "onSelect" | "onNewChat">) => {
  const handleSelect = (sessionId: string) => {
    onSelect(sessionId)
  }

  const handleNewChat = () => {
    onNewChat()
  }

  return { handleSelect, handleNewChat }
}
