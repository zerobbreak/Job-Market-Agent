import { useCallback, useState } from "react"

/**
 * Return type for useToggle hook
 */
interface UseToggleReturn {
    /** Current boolean value */
    value: boolean
    /** Toggle the value */
    toggle: () => void
    /** Set to true */
    on: () => void
    /** Set to false */
    off: () => void
    /** Set to a specific value */
    set: (value: boolean) => void
}

/**
 * Custom hook for managing boolean toggle state with convenient methods
 * Provides a clean API for boolean state management
 *
 * @param initialValue - The initial boolean value (default: false)
 * @returns Object with value and toggle methods
 *
 * @example
 * ```tsx
 * const { value: isOpen, toggle, on, off } = useToggle(false);
 *
 * return (
 *   <div>
 *     <button onClick={toggle}>
 *       {isOpen ? 'Close' : 'Open'} Modal
 *     </button>
 *     <button onClick={on}>Open</button>
 *     <button onClick={off}>Close</button>
 *   </div>
 * );
 * ```
 */
export function useToggle(initialValue = false): UseToggleReturn {
    const [value, setValue] = useState<boolean>(initialValue)

    const toggle = useCallback(() => {
        setValue((prev) => !prev)
    }, [])

    const on = useCallback(() => {
        setValue(true)
    }, [])

    const off = useCallback(() => {
        setValue(false)
    }, [])

    const set = useCallback((newValue: boolean) => {
        setValue(newValue)
    }, [])

    return {
        value,
        toggle,
        on,
        off,
        set,
    }
}
