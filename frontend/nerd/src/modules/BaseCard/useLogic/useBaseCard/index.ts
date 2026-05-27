import type { BaseCardProps } from "modules/BaseCard/types"

export const useBaseCard = ({ hoverable, onClick }: BaseCardProps) => {
  const clickable = Boolean(onClick)

  return {
    clickable,
    hoverable,
    handleClick: onClick,
  }
}
