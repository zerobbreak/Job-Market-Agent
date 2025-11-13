import { type RouteConfig } from "@react-router/dev/routes"

export default [
    {
        path: "/",
        file: "routes/index.tsx",
    },
    {
        path: "/jobs",
        file: "routes/jobs/jobs-home.tsx",
    },
    {
        path: "/jobs/:jobId",
        file: "routes/jobs/job-layout.tsx",
        children: [
            {
                index: true,
                file: "routes/jobs/job-upload.tsx",
            },
            {
                path: "job-materials/:jobMaterialId",
                file: "routes/jobs/job-material-detail.tsx",
            },
            {
                path: "new-job-material",
                file: "routes/jobs/new-job-material.tsx",
            },
        ],
    },
    {
        path: "/learn",
        file: "routes/learn.tsx",
    },
    {
        path: "/learn/:section/:page",
        file: "routes/learn/learn-layout.tsx",
    },
    {
        path: "/login",
        file: "routes/auth/login.tsx",
    },
    {
        path: "/register",
        file: "routes/auth/register.tsx",
    },
    {
        path: "/activate",
        file: "routes/auth/activate.tsx",
    },
    {
        path: "/forgot-password",
        file: "routes/auth/forgot-password.tsx",
    },
    {
        path: "/logout",
        file: "routes/auth/logout.tsx",
    },
    {
        path: "/refresh",
        file: "routes/auth/refresh.tsx",
    },
] satisfies RouteConfig