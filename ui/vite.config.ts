import { reactRouter } from "@react-router/dev/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"
import tsconfigPaths from "vite-tsconfig-paths"

export default defineConfig({
    plugins: [reactRouter(), tailwindcss(), tsconfigPaths()],
    server: {
        proxy: {
            "/api/auth": {
                target: "http://localhost:8083",
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api\/auth/, "/auth"),
            },
            "/api/job-market": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api\/job-market(.*)/, "/job-market/api/v1$1"),
            },
        },
    },
})
