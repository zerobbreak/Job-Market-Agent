import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { account, PROJECT_ID, API_ENDPOINT } from '../utils/appwrite';
import { ID } from 'appwrite';

interface User {
    $id: string;
    name: string;
    email: string;
    [key: string]: any;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name: string) => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkUserStatus();
    }, []);

    const checkUserStatus = async () => {
        if (!PROJECT_ID || !API_ENDPOINT) {
            setUser(null)
            setLoading(false)
            return
        }
        try {
            const accountDetails = await account.get()
            setUser(accountDetails)
        } catch (_) {
            setUser(null)
        } finally {
            setLoading(false)
        }
    };

    const login = async (email: string, password: string) => {
        if (!PROJECT_ID || !API_ENDPOINT) {
            throw new Error('Authentication service not configured')
        }
        await account.createEmailPasswordSession(email, password)
        await checkUserStatus()
    };

    const register = async (email: string, password: string, name: string) => {
        if (!PROJECT_ID || !API_ENDPOINT) {
            throw new Error('Authentication service not configured')
        }
        await account.create(ID.unique(), email, password, name)
        await login(email, password)
    };

    const logout = async () => {
        if (!PROJECT_ID || !API_ENDPOINT) {
            setUser(null)
            return
        }
        await account.deleteSession('current')
        setUser(null)
    };

    return <AuthContext.Provider value={{ user, loading, login, register, logout }}>
        {children}
    </AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
