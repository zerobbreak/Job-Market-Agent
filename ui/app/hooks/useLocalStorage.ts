import { useCallback, useEffect, useState } from "react"

/**
 * Custom hook for managing localStorage with React state synchronization
 * Automatically syncs with localStorage and handles JSON serialization/deserialization
 *
 * @param key - The localStorage key
 * @param initialValue - The initial value if key doesn't exist
 * @returns A tuple of [value, setValue, removeValue]
 *
 * @example
 * ```tsx
 * const [theme, setTheme, removeTheme] = useLocalStorage('theme', 'light');
 *
 * // Set a new value
 * setTheme('dark');
 *
 * // Remove from localStorage
 * removeTheme();
 * ```
 */
export function useLocalStorage<T>(
    key: string,
    initialValue: T
): [T, (value: T | ((val: T) => T)) => void, () => void] {
    // State to store our value
    const [storedValue, setStoredValue] = useState<T>(() => {
        try {
            // Get from local storage by key
            const item = window.localStorage.getItem(key)
            // Parse stored json or return initialValue
            return item ? JSON.parse(item) : initialValue
        } catch (error) {
            // If error, return initial value
            console.warn(`Error reading localStorage key "${key}":`, error)
            return initialValue
        }
    })

    // Return a wrapped version of useState's setter function that persists the new value to localStorage
    const setValue = useCallback(
        (value: T | ((val: T) => T)) => {
            try {
                // Allow value to be a function so we have the same API as useState
                const valueToStore = value instanceof Function ? value(storedValue) : value
                // Save state
                setStoredValue(valueToStore)
                // Save to local storage
                window.localStorage.setItem(key, JSON.stringify(valueToStore))
            } catch (error) {
                console.warn(`Error setting localStorage key "${key}":`, error)
            }
        },
        [key, storedValue]
    )

    // Remove from localStorage
    const removeValue = useCallback(() => {
        try {
            window.localStorage.removeItem(key)
            setStoredValue(initialValue)
        } catch (error) {
            console.warn(`Error removing localStorage key "${key}":`, error)
        }
    }, [key, initialValue])

    // Listen for changes to this localStorage key from other tabs/windows
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === key && e.newValue !== null) {
                try {
                    setStoredValue(JSON.parse(e.newValue))
                } catch (error) {
                    console.warn(`Error parsing localStorage change for key "${key}":`, error)
                }
            }
        }

        window.addEventListener("storage", handleStorageChange)
        return () => window.removeEventListener("storage", handleStorageChange)
    }, [key])

    return [storedValue, setValue, removeValue]
}
