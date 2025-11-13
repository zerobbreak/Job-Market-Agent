// Store initialization logic for state management

/**
 * This module handles the initialization and migration logic for the state management system.
 * It provides functions to create and configure the store with middleware, initialize it with
 * data based on the environment, and manage migrations for state persistence across versions.
 */

import { LocalStore } from "./state.client" // Assuming LocalStore is still accessible
import {
    asyncMiddleware,
    loggerMiddleware,
    persistenceMiddleware,
    validationMiddleware,
} from "./state.middleware"
import type { Migration } from "./state.types" // Assuming Migration type is defined here

/**
 * createConfiguredStore creates and configures a LocalStore instance with middleware.
 * It initializes the store with mock data if configured for development mode.
 * @returns A Promise resolving to the configured LocalStore instance.
 */
const createConfiguredStore = async () => {
    const store = LocalStore.getInstance({
        persistKey: "jc-local-store",
        version: "1.0.0",
        maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
        debug: import.meta.env.DEV,
    })

    // Add middleware (order matters)
    if (import.meta.env.DEV) {
        store.use(loggerMiddleware)
    }
    store.use(validationMiddleware)
    store.use(asyncMiddleware)
    store.use(persistenceMiddleware)

    // Initialize store
    store.initialize()

    // Dynamic data initialization based on environment
    if (store.getState().cases.length === 0) {
        // Check if we should use mock data
        const useMockData =
            import.meta.env.VITE_USE_MOCK_DATA === "true" ||
            (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

        if (useMockData) {
            try {
                const { initializeMockData } = await import("../../mocks")
                initializeMockData(store)
                console.log("[Store] Initialized with mock data")
            } catch (error) {
                console.warn("[Store] Failed to load mock data:", error)
            }
        } else {
            console.log("[Store] Initialized without data - ready for API integration")
        }
    }

    return store
}

/**
 * initializeStoreWithMigrations enhances a LocalStore instance with migration support.
 * It overrides the storage loading mechanism to handle version migrations and data expiration.
 * @param store The LocalStore instance to enhance with migration capabilities.
 * @returns The enhanced LocalStore instance.
 */
const initializeStoreWithMigrations = (store: LocalStore) => {
    // Override the loadFromStorage method safely (using type assertion for protected access)
    // biome-ignore lint/suspicious/noExplicitAny: Protected method access requires type assertion for migration system
    const _originalLoad = (store as any).loadFromStorage.bind(store)

    // biome-ignore lint/suspicious/noExplicitAny: Protected method override requires type assertion for migration system
    ;(store as any).loadFromStorage = function () {
        if (typeof window === "undefined") return

        try {
            const stored = localStorage.getItem(this.config.persistKey)
            if (!stored) return

            const data = JSON.parse(stored)

            // Check if migration is needed
            if (data.version && data.version !== this.config.version) {
                console.log(`[LocalStore] Migrating from ${data.version} to ${this.config.version}`)
                data.state = runMigrations(data.state, data.version)
                data.version = this.config.version

                // Save migrated data
                localStorage.setItem(this.config.persistKey, JSON.stringify(data))
            }

            // Check data age
            if (this.config.maxAge && Date.now() - data.timestamp > this.config.maxAge) {
                console.warn("[LocalStore] Data expired, starting fresh")
                return
            }

            this.state = { ...this.state, ...data.state }
        } catch (error) {
            console.warn("[LocalStore] Failed to load migrated state:", error)
        }
    }

    return store
}

/**
 * getLocalStore is the recommended way to obtain a fully configured LocalStore instance.
 * It asynchronously creates and initializes the store with migration support.
 * @returns A Promise resolving to the fully configured LocalStore instance.
 */
// New LocalStore API (recommended) - Async initialization
export const getLocalStore = async (): Promise<LocalStore> => {
    const store = await createConfiguredStore()
    return initializeStoreWithMigrations(store)
}

/**
 * runMigrations applies migrations to the stored state based on version changes.
 * It iterates through defined migrations to update the state structure or data format.
 * @param state The current state to migrate.
 * @param fromVersion The version of the state to migrate from.
 * @returns The migrated state.
 */
// Migration runner
// biome-ignore lint/suspicious/noExplicitAny: Migration runner needs to handle any state version
const runMigrations = (state: any, fromVersion: string): any => {
    let migratedState = { ...state }

    for (const migration of migrations) {
        if (migration.fromVersion === fromVersion) {
            console.log(
                `[Migration] Running migration ${migration.fromVersion} -> ${migration.toVersion}`
            )
            migratedState = migration.migrate(migratedState)
        }
    }

    return migratedState
}

/**
 * migrations is an array of migration definitions for state version updates.
 * Each migration specifies the versions it applies to and a function to transform the state.
 */
// Migrations array
const migrations: Migration[] = [
    // Example migration from 0.9.0 to 1.0.0
    {
        fromVersion: "0.9.0",
        toVersion: "1.0.0",
        migrate: (state) => ({
            ...state,
            version: "1.0.0",
            ui: {
                isLoading: false,
                lastUpdated: new Date().toISOString(),
            },
        }),
    },
]
