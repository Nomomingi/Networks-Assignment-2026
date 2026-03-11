import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

interface AuthContextValue {
    user: string | null;        // username, or null when logged out
    loading: boolean;
    login: (username: string, password: string) => Promise<string | null>;
    signup: (username: string, password: string) => Promise<string | null>;
    logout: () => void;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);  // true while rehydrating

    // Rehydrate from sessionStorage on first mount
    useEffect(() => {
        const stored = sessionStorage.getItem('chat_user');
        if (stored) setUser(stored);
        setLoading(false);
    }, []);

    /**
     * Calls POST /api/login.
     * Returns null on success, or an error string to display.
     */
    const login = useCallback(async (username: string, password: string): Promise<string | null> => {
        try {
            const res = await fetch(`${API_BASE}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();
            if (res.ok) {
                setUser(data.username);
                sessionStorage.setItem('chat_user', data.username);
                return null;    // success
            }
            return data.error ?? 'Login failed';
        } catch {
            return 'Could not reach the server. Is the bridge running?';
        }
    }, []);

    /**
     * Calls POST /api/signup.
     * Returns null on success, or an error string to display.
     */
    const signup = useCallback(async (username: string, password: string): Promise<string | null> => {
        try {
            const res = await fetch(`${API_BASE}/api/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();
            if (res.ok) {
                // Server auto-logs in after signup (matches CLI behaviour)
                setUser(data.username);
                sessionStorage.setItem('chat_user', data.username);
                return null;    // success
            }
            return data.error ?? 'Sign-up failed';
        } catch {
            return 'Could not reach the server. Is the bridge running?';
        }
    }, []);

    const logout = useCallback(() => {
        setUser(null);
        sessionStorage.removeItem('chat_user');
    }, []);

    return (
        <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
    return ctx;
}
