// Middleware implementations for state management

/**
 * This module provides middleware implementations for the state management system.
 * Middleware functions are used to intercept and process actions before they reach the store,
 * allowing for logging, validation, and other cross-cutting concerns. These middleware
 * functions are designed to work with the LocalStore to enhance the behavior of state updates.
 */

import type { Case } from "@/types/job.types" // Assuming Case type is needed for validation
import type { StoreMiddleware } from "./state.types"

/**
 * loggerMiddleware logs details about each action and the current state for debugging purposes.
 * It groups log output by action type to provide a clear view of state changes.
 * @param action The action being processed.
 * @param state The current state of the store.
 * @returns The original action, unchanged.
 */
export const loggerMiddleware: StoreMiddleware = (action, state) => {
    console.group(`[LocalStore] ${action.type}`)
    console.log("Action:", action)
    console.log("Previous State:", state)
    console.groupEnd()
    return action
}

/**
 * validationMiddleware validates actions before they are processed by the store.
 * It checks for required fields and data integrity to prevent invalid state updates.
 * @param action The action being processed.
 * @param _state The current state of the store (unused in this middleware).
 * @returns The action if valid, or null if the action is invalid and should be blocked.
 */
export const validationMiddleware: StoreMiddleware = (action, _state) => {
    switch (action.type) {
        case "CASES/ADD_CASE": {
            const caseData = action.payload as Case
            if (!caseData.id || !caseData.title) {
                console.error("[Validation] Invalid case data:", caseData)
                return null // Block invalid actions
            }
            break
        }
        case "CASES/UPDATE_CASE": {
            const { caseId, updates } = action.payload as {
                caseId: string
                updates: Partial<Case>
            }
            if (!caseId || !updates) {
                console.error("[Validation] Invalid update data:", action.payload)
                return null
            }
            break
        }
    }
    return action
}

/**
 * asyncMiddleware handles asynchronous actions by intercepting specific action types.
 * It can be extended to manage loading states or other async-specific logic.
 * @param action The action being processed.
 * @param _state The current state of the store (unused in this middleware).
 * @returns The original action, unchanged.
 */
export const asyncMiddleware: StoreMiddleware = (action, _state) => {
    // Handle async actions
    if (action.type.startsWith("ASYNC/")) {
        // For async operations, we could dispatch loading states
        // This is a simplified version - in a real app you'd have thunk-like functionality
        return action
    }
    return action
}

/**
 * persistenceMiddleware adds metadata to actions for persistence purposes.
 * It includes timestamps and persistence flags to track when and how actions are stored.
 * @param action The action being processed.
 * @param _state The current state of the store (unused in this middleware).
 * @returns The action with added metadata for persistence.
 */
export const persistenceMiddleware: StoreMiddleware = (action, _state) => {
    // Add metadata for persistence
    return {
        ...action,
        meta: {
            ...action.meta,
            timestamp: Date.now(),
            persisted: true,
        },
    }
}
