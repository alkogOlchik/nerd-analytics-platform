export interface ProductOption {
  label: string
  value: string
}

export interface PromptCardProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
}
