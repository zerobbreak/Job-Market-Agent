import { useCallback, useEffect, useState } from "react"

/**
 * Custom hook for debounced form validation
 * Prevents excessive validation calls during typing
 */
export function useDebouncedValidation<T>(
    value: T,
    validator: (val: T) => { isValid: boolean; errors: string[] },
    delay = 300
) {
    const [debouncedValue, setDebouncedValue] = useState(value)
    const [validation, setValidation] = useState(() => validator(value))

    // Debounce the value
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedValue(value)
        }, delay)

        return () => clearTimeout(timer)
    }, [value, delay])

    // Validate when debounced value changes
    useEffect(() => {
        const result = validator(debouncedValue)
        setValidation(result)
    }, [debouncedValue, validator])

    return validation
}

/**
 * Hook for debounced API calls
 * Prevents excessive API requests during user input
 */
export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
    callback: T,
    delay = 300
): T {
    const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null)

    const debouncedCallback = useCallback(
        (...args: Parameters<T>) => {
            if (debounceTimer) {
                clearTimeout(debounceTimer)
            }

            const timer = setTimeout(() => {
                callback(...args)
            }, delay)

            setDebounceTimer(timer)
        },
        [callback, delay, debounceTimer]
    )

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (debounceTimer) {
                clearTimeout(debounceTimer)
            }
        }
    }, [debounceTimer])

    return debouncedCallback as T
}
