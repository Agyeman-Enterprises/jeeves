import { useCallback, useEffect, useState } from "react"

export type ToastVariant = "info" | "error"

export interface JarvisToast {
  id: string
  message: string
  variant: ToastVariant
}

interface UseJarvisToastsOptions {
  ttlMs?: number
  maxToasts?: number
}

export interface UseJarvisToastsResult {
  toasts: JarvisToast[]
  notify: (message: string, variant?: ToastVariant) => void
  dismiss: (id: string) => void
}

const newId = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`)

export function useJarvisToasts(options: UseJarvisToastsOptions = {}): UseJarvisToastsResult {
  const { ttlMs = 3500, maxToasts = 3 } = options
  const [toasts, setToasts] = useState<JarvisToast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const notify = useCallback(
    (message: string, variant: ToastVariant = "info") => {
      const toast: JarvisToast = { id: newId(), message, variant }
      setToasts((prev) => {
        const next = [...prev, toast]
        if (next.length > maxToasts) {
          next.shift()
        }
        return next
      })

      setTimeout(() => dismiss(toast.id), ttlMs)
    },
    [dismiss, maxToasts, ttlMs],
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => setToasts([])
  }, [])

  return { toasts, notify, dismiss }
}


