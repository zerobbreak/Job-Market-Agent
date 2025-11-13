/// <reference types="vitest" />

import tsconfigPaths from "vite-tsconfig-paths"
import { defineConfig } from "vitest/config"

export default defineConfig({
    plugins: [tsconfigPaths()],
    test: {
        globals: true,
        environment: "jsdom",
        setupFiles: ["./tests/setup.ts"],
        // Include co-located test files throughout the app directory
        include: ["app/**/*.{test,spec}.{js,ts,jsx,tsx}"],
        // Exclude E2E tests and build artifacts
        exclude: ["tests/e2e/**", "node_modules/**", "build/**", ".react-router/**"],
        coverage: {
            provider: "v8",
            reporter: ["text", "json", "html"],
            exclude: [
                "tests/e2e/**",
                "**/*.config.*",
                "app/root.tsx", // Often just a wrapper
                "**/*.test.*",
                "**/*.spec.*",
            ],
        },
    },
})
