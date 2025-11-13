// Utility methods and dev tools for state management

/**
 * This module provides utility methods and development tools for state management.
 * These utilities assist in debugging, monitoring performance, and handling data persistence.
 * They are designed to work with the LocalStore to offer insights and control over the state.
 */

import { LocalStore } from "./state.client" // Assuming LocalStore is still accessible
import type { StoreAction, StoreState } from "./state.types"

/**
 * createStoreInspector creates a debugging tool for inspecting the state store.
 * It provides methods to get snapshots, subscribe to changes with logging, monitor performance,
 * and enable time travel debugging.
 * @returns An object with methods for inspecting and debugging the store.
 */
export const createStoreInspector = () => {
    const store = LocalStore.getInstance()

    return {
        // Get current state snapshot
        /**
         * getSnapshot retrieves the current state of the store as a snapshot.
         * @returns The current state of the store.
         */
        getSnapshot: () => store.getState(),

        // Subscribe to state changes with detailed logging
        /**
         * subscribeWithLogging subscribes to state changes and logs updates with a custom name.
         * @param name A name for the subscription to identify logs.
         * @returns A function to unsubscribe from state changes.
         */
        subscribeWithLogging: (name: string) => {
            return store.subscribe((state, action) => {
                console.group(`[${name}] State Update`)
                console.log("Action:", action)
                console.log("New State:", state)
                console.groupEnd()
            })
        },

        // Time travel debugging (stores history)
        /**
         * createTimeTraveler enables time travel debugging by storing state history and actions.
         * @returns An object with methods to access history, actions, current index, and unsubscribe.
         */
        createTimeTraveler: () => {
            const history: StoreState[] = []
            const actions: StoreAction[] = []

            const unsubscribe = store.subscribe((state, action) => {
                history.push({ ...state })
                if (action) actions.push(action)
            })

            return {
                /**
                 * getHistory retrieves the history of state snapshots.
                 * @returns An array of past state snapshots.
                 */
                getHistory: () => history,
                /**
                 * getActions retrieves the history of actions performed.
                 * @returns An array of past actions.
                 */
                getActions: () => actions,
                /**
                 * getCurrentIndex retrieves the current index in the history.
                 * @returns The index of the current state in history.
                 */
                getCurrentIndex: () => history.length - 1,
                /**
                 * unsubscribe stops tracking state changes for time travel.
                 */
                unsubscribe,
            }
        },

        // Performance monitoring
        /**
         * monitorPerformance monitors the performance of state updates by counting actions per second.
         * @returns A function to unsubscribe from performance monitoring.
         */
        monitorPerformance: () => {
            let startTime = Date.now()
            let actionCount = 0

            const unsubscribe = store.subscribe(() => {
                actionCount++
                const now = Date.now()
                if (now - startTime > 1000) {
                    // Log every second
                    console.log(`[Performance] ${actionCount} actions in ${now - startTime}ms`)
                    actionCount = 0
                    startTime = now
                }
            })

            return unsubscribe
        },
    }
}

/**
 * obfuscate performs basic obfuscation on data for storage (not true encryption).
 * This is a placeholder for proper encryption in production environments.
 * @param data The string data to obfuscate.
 * @returns The obfuscated string.
 */
export const obfuscate = (data: string): string => {
    // Simple base64 encoding with a salt
    const salt = "jc-store-salt-2024"
    const salted = salt + data + salt
    return btoa(salted).split("").reverse().join("")
}

/**
 * deobfuscate reverses the obfuscation process to retrieve the original data.
 * Throws an error if deobfuscation fails.
 * @param data The obfuscated string to deobfuscate.
 * @returns The original string data.
 * @throws Error if deobfuscation fails.
 */
export const deobfuscate = (data: string): string => {
    try {
        // Reverse the obfuscation
        const reversed = data.split("").reverse().join("")
        const decoded = atob(reversed)
        const salt = "jc-store-salt-2024"
        return decoded.slice(salt.length, -salt.length)
    } catch {
        throw new Error("Failed to deobfuscate data")
    }
}
