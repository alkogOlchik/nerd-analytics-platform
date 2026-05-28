import { useState } from "react"

export const useSidebar = () => {
  const [activeItem, setActiveItem] = useState("home")

  const handleSelect = (id: string) => {
    setActiveItem(id)
  }

  return {
    activeItem,
    handleSelect,
  }
}
