window.__env__ = {
	// OAuth provider URL - defaults to localhost for local development
	VITE_OAUTH_PROVIDER_URL:
		"${VITE_OAUTH_PROVIDER_URL}" && "${VITE_OAUTH_PROVIDER_URL}" !== "undefined"
			? "${VITE_OAUTH_PROVIDER_URL}"
			: "http://localhost:8083",

	// API URL - defaults to localhost for local development
	VITE_JOB_MARKET_API_URL:
		"${VITE_JOB_MARKET_API_URL}" && "${VITE_JOB_MARKET_API_URL}" !== "undefined"
			? "${VITE_JOB_MARKET_API_URL}"
			: "http://localhost:8000/job-market/api/v1",

	// Session secret - uses a safe default for development
	// NOTE: In production, set VITE_SESSION_SECRET to a strong random value
	VITE_SESSION_SECRET:
		"${VITE_SESSION_SECRET}" && "${VITE_SESSION_SECRET}" !== "undefined"
			? "${VITE_SESSION_SECRET}"
			: "development-secret-change-in-production",

	// Mode - defaults to development
	VITE_MODE: "${VITE_MODE}" && "${VITE_MODE}" !== "undefined" ? "${VITE_MODE}" : "development",
};
