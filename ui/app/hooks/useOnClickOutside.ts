import { useEffect, useRef } from "react"

/**
 * Custom hook that handles clicks outside of a specified element
 * Useful for closing dropdowns, modals, and other overlays
 *
 * @param handler - Function to call when clicking outside
 * @returns Ref to attach to the element you want to protect
 *
 * @example
 * ```tsx
 * const ref = useOnClickOutside(() => setIsOpen(false));
 *
 * return (
 *   <div ref={ref}>
 *     <button onClick={() => setIsOpen(!isOpen)}>Toggle</button>
 *     {isOpen && <div>Dropdown content</div>}
 *   </div>
 * );
 * ```
 */
export function useOnClickOutside<T extends HTMLElement = HTMLElement>(
    handler: (event: MouseEvent | TouchEvent) => void
) {
    const ref = useRef<T>(null)

    useEffect(() => {
        const listener = (event: MouseEvent | TouchEvent) => {
            // Do nothing if clicking ref's element or descendent elements
            if (!ref.current || ref.current.contains(event.target as Node)) {
                return
            }

            handler(event)
        }

        document.addEventListener("mousedown", listener)
        document.addEventListener("touchstart", listener)

        return () => {
            document.removeEventListener("mousedown", listener)
            document.removeEventListener("touchstart", listener)
        }
    }, [handler])

    return ref
}
