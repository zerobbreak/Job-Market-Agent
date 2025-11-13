// Type definitions for state management

import type { Job } from "@/types/job.types"

/**
 * StoreState represents the overall state structure of the application.
 * It encapsulates all managed data including jobs, the currently selected job,
 * UI-related state, and versioning information.
 */
export interface StoreState {
    /** Array of all jobs managed in the application */
    jobs: Job[]
    /** Currently selected job for detailed view or operations, null if none selected */
    currentJob: Job | null
    /** UI-related state for managing loading indicators and update timestamps */
    ui: {
        /** Indicates if the application is in a loading state (e.g., during API calls) */
        isLoading: boolean
        /** Timestamp of the last state update, null if not updated yet */
        lastUpdated: string | null
    }
    /** Version of the state schema for migration purposes */
    version: string
}

/**
 * StoreAction defines the structure of actions that can modify the store's state.
 * Actions are used to trigger state changes in a predictable manner.
 * @template T The type of payload the action carries, defaults to any for flexibility.
 */
// biome-ignore lint/suspicious/noExplicitAny: Generic action type for flexibility in store middleware
export interface StoreAction<T = any> {
    /** Type identifier for the action, used to determine how to process it */
    type: string
    /** Optional data payload for the action */
    payload?: T
    /** Optional metadata for additional context or middleware processing */
    // biome-ignore lint/suspicious/noExplicitAny: Meta can contain any type of additional data
    meta?: Record<string, any>
}

/**
 * StoreMiddleware defines a function type for middleware that processes actions
 * before they reach the store. Middleware can modify, block, or log actions.
 */
export type StoreMiddleware = (action: StoreAction, state: StoreState) => StoreAction | null

/**
 * StoreSubscriber defines a callback function type for listeners that react
 * to state changes. Subscribers are notified after each state update.
 */
export type StoreSubscriber = (state: StoreState, action?: StoreAction) => void

/**
 * StoreConfig defines configuration options for the store, controlling
 * persistence, versioning, and debugging behavior.
 */
export interface StoreConfig {
    /** Key used for persisting state in localStorage */
    persistKey: string
    /** Version identifier for the state schema */
    version: string
    /** Maximum age of persisted data in milliseconds before it is considered expired */
    maxAge?: number
    /** Enables debug logging if true */
    debug?: boolean
}

/**
 * Migration defines a structure for state migration between different versions.
 * It includes the version range and a function to transform the state.
 */
export interface Migration {
    /** Source version to migrate from */
    fromVersion: string
    /** Target version to migrate to */
    toVersion: string
    /** Function to transform the state from the source to the target version */
    // biome-ignore lint/suspicious/noExplicitAny: Migration functions need to handle any version of state
    migrate: (state: any) => any
}
