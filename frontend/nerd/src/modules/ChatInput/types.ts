export interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (files: File[]) => void
  disabled?: boolean
  placeholder?: string
}
