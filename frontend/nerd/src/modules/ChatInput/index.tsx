import { Send, Loader2, Mic, MicOff, Plus, X } from "lucide-react"
import { type KeyboardEvent, useRef, useEffect, useState, useCallback } from "react"
import clsx from "clsx"
import styles from "./styles.module.scss"
import type { ChatInputProps } from "./types"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const SpeechRecognitionAPI: any =
  typeof window !== "undefined"
    ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ((window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition ?? null)
    : null

export const ChatInput = ({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = "Напишите сообщение…",
}: ChatInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null)

  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [isRecording, setIsRecording] = useState(false)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${el.scrollHeight}px`
  }, [value])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && value.trim()) {
        handleSubmit()
      }
    }
  }

  const handleSubmit = () => {
    setAttachedFiles([])
    onSubmit()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    if (files.length === 0) return
    setAttachedFiles((prev) => [...prev, ...files])
    e.target.value = ""
  }

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const toggleRecording = useCallback(() => {
    if (!SpeechRecognitionAPI) return

    if (isRecording) {
      recognitionRef.current?.stop()
      setIsRecording(false)
      return
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognition = new SpeechRecognitionAPI() as any
    recognition.lang = "ru-RU"
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (event: any) => {
      const transcript: string = event.results[0]?.[0]?.transcript ?? ""
      if (transcript) {
        onChange(value ? `${value} ${transcript}` : transcript)
      }
    }

    recognition.onend = () => setIsRecording(false)
    recognition.onerror = () => setIsRecording(false)

    recognitionRef.current = recognition
    recognition.start()
    setIsRecording(true)
  }, [isRecording, value, onChange])

  return (
    <div className={styles.wrapper}>
      {attachedFiles.length > 0 && (
        <div className={styles.attachments}>
          {attachedFiles.map((file, i) => (
            <div key={i} className={styles.fileChip}>
              <span className={styles.fileName}>{file.name}</span>
              <button
                type="button"
                className={styles.removeFile}
                onClick={() => removeFile(i)}
                title="Удалить файл"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className={styles.inputRow}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className={styles.hiddenFileInput}
          onChange={handleFileChange}
        />
        <button
          className={styles.iconAction}
          type="button"
          title="Прикрепить файл"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
        >
          <Plus size={16} />
        </button>

        <textarea
          ref={textareaRef}
          className={styles.textarea}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={disabled}
        />

        <div className={styles.rightActions}>
          <button
            className={clsx(styles.iconAction, isRecording && styles.iconActionRecording)}
            type="button"
            title={
              !SpeechRecognitionAPI
                ? "Голосовой ввод недоступен в этом браузере"
                : isRecording
                  ? "Остановить запись"
                  : "Голосовой ввод"
            }
            onClick={toggleRecording}
            disabled={disabled || !SpeechRecognitionAPI}
          >
            {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
          <button
            className={styles.sendButton}
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            title="Отправить"
          >
            {disabled ? (
              <Loader2 size={18} className={styles.spinner} />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </div>
      <p className={styles.hint}>Enter — отправить · Shift+Enter — новая строка</p>
    </div>
  )
}
