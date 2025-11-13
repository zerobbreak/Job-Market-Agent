import { useEffect, useState } from "react"

/**
 * Custom hook that debounces a value by delaying updates until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked
 *
 * @param value - The value to debounce
 * @param delay - The delay in milliseconds
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState("");
 * const debouncedSearchTerm = useDebounce(searchTerm, 300);
 *
 * // Use debouncedSearchTerm for API calls to avoid excessive requests
 * useEffect(() => {
 *   searchAPI(debouncedSearchTerm);
 * }, [debouncedSearchTerm]);
 * ```
 */
export function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value)

    useEffect(() => {
        // Update debounced value after delay
        const handler = setTimeout(() => {
            setDebouncedValue(value)
        }, delay)

        // Cancel the timeout if value changes (also on delay change or unmount)
        return () => {
            clearTimeout(handler)
        }
    }, [value, delay])

    return debouncedValue
}
