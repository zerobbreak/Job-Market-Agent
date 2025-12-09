import { account } from './appwrite';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface ApiOptions extends RequestInit {
    headers?: Record<string, string>;
}

export const apiClient = async (endpoint: string, options: ApiOptions = {}) => {
    let token: string | undefined
    try {
        const jwt = await account.createJWT()
        token = jwt.jwt
    } catch (_) {}

    const headers: Record<string, string> = {
        ...(options.headers || {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    }

    if (!(options.body instanceof FormData) && !('Content-Type' in headers)) {
        headers['Content-Type'] = 'application/json'
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: headers as HeadersInit,
    })

    if (response.status === 401) {
        console.error('Unauthorized access. Token might be expired.')
        throw new Error('Unauthorized')
    }

    return response
};
