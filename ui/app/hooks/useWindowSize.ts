import { useEffect, useState } from "react"

/**
 * Window size dimensions
 */
interface WindowSize {
    width: number | undefined
    height: number | undefined
}

/**
 * Custom hook that tracks window dimensions and updates on resize
 * Useful for responsive design and conditional rendering based on screen size
 *
 * @returns Object with width and height of the window
 *
 * @example
 * ```tsx
 * const { width, height } = useWindowSize();
 *
 * const isMobile = width && width < 768;
 * const isTablet = width && width >= 768 && width < 1024;
 * const isDesktop = width && width >= 1024;
 *
 * return (
 *   <div>
 *     {isMobile && <MobileLayout />}
 *     {isTablet && <TabletLayout />}
 *     {isDesktop && <DesktopLayout />}
 *   </div>
 * );
 * ```
 */
export function useWindowSize(): WindowSize {
    const [windowSize, setWindowSize] = useState<WindowSize>({
        width: undefined,
        height: undefined,
    })

    useEffect(() => {
        // Handler to call on window resize
        function handleResize() {
            setWindowSize({
                width: window.innerWidth,
                height: window.innerHeight,
            })
        }

        // Add event listener
        window.addEventListener("resize", handleResize)

        // Call handler right away so state gets updated with initial window size
        handleResize()

        // Remove event listener on cleanup
        return () => window.removeEventListener("resize", handleResize)
    }, []) // Empty array ensures that effect is only run on mount

    return windowSize
}
