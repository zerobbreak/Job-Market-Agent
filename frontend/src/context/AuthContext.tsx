import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { account } from '../utils/appwrite';
import { ID } from 'appwrite';

interface AuthContextType {
    user: any;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, name: string) => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkUserStatus();
    }, []);

    const checkUserStatus = async () => {
        try {
            const accountDetails = await account.get();
            setUser(accountDetails);
        } catch (error) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        await account.createEmailPasswordSession(email, password);
        await checkUserStatus();
    };

    const register = async (email: string, password: string, name: string) => {
        await account.create(ID.unique(), email, password, name);
        await login(email, password);
    };

    const logout = async () => {
        await account.deleteSession('current');
        setUser(null);
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
