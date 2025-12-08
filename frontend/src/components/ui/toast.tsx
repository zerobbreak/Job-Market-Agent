import * as React from "react"
import { cn } from "../../lib/utils"

type ToastItem = {
  id: string
  title?: string
  description?: string
  variant?: "default" | "success" | "error"
}

type ToastContextValue = {
  toasts: ToastItem[]
  show: (t: Omit<ToastItem, "id">) => void
  remove: (id: string) => void
}

const ToastContext = React.createContext<ToastContextValue | undefined>(undefined)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([])
  const show = React.useCallback((t: Omit<ToastItem, "id">) => {
    const id = Math.random().toString(36).slice(2)
    const item = { id, ...t }
    setToasts((prev) => [...prev, item])
    setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== id))
    }, 4000)
  }, [])
  const remove = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((x) => x.id !== id))
  }, [])
  return (
    <ToastContext.Provider value={{ toasts, show, remove }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = React.useContext(ToastContext)
  if (!ctx) throw new Error("Missing ToastProvider")
  return ctx
}

export function ToastViewport() {
  const { toasts, remove } = useToast()
  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 w-80">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "border rounded-lg shadow-sm p-3 text-sm animate-in fade-in-0",
            t.variant === "success" && "bg-green-50 border-green-200 text-green-800",
            t.variant === "error" && "bg-red-50 border-red-200 text-red-800",
            (!t.variant || t.variant === "default") && "bg-white border-gray-200 text-gray-800"
          )}
        >
          {t.title && <div className="font-semibold mb-1">{t.title}</div>}
          {t.description && <div className="text-gray-600">{t.description}</div>}
          <button className="mt-2 text-xs text-gray-500" onClick={() => remove(t.id)}>Dismiss</button>
        </div>
      ))}
    </div>
  )
}
