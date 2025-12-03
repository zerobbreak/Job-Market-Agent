import { account } from './appwrite';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface ApiOptions extends RequestInit {
    headers?: Record<string, string>;
}

export const apiClient = async (endpoint: string, options: ApiOptions = {}) => {
    try {
        // Get a fresh JWT token
        const jwt = await account.createJWT();
        const token = jwt.jwt;

        // Prepare headers
        const headers: Record<string, string> = {
            ...(options.headers || {}),
            'Authorization': `Bearer ${token}`,
        };

        // If body is JSON and Content-Type is not set, set it to application/json
        // Note: FormData should NOT have Content-Type set manually (browser does it)
        if (!(options.body instanceof FormData) && !('Content-Type' in headers)) {
            headers['Content-Type'] = 'application/json';
        }

        // Make the request
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: headers as HeadersInit,
        });

        // Handle 401 Unauthorized (optional: trigger logout or refresh)
        if (response.status === 401) {
            console.error('Unauthorized access. Token might be expired.');
            // You might want to redirect to login here or throw a specific error
            throw new Error('Unauthorized');
        }

        return response;
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
};
