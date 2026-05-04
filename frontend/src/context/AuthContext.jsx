import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [token, setToken] = useState(localStorage.getItem('iris_token'));
    const [role, setRole] = useState(localStorage.getItem('iris_role'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Verify token on mount
        if (token) {
            api.get('/auth/verify')
                .then((res) => {
                    setRole(res.data.role);
                    localStorage.setItem('iris_role', res.data.role);
                })
                .catch(() => {
                    logout();
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const login = async (selectedRole, pin) => {
        const res = await api.post('/auth/login', { role: selectedRole, pin });
        const { token: newToken, role: newRole } = res.data;
        localStorage.setItem('iris_token', newToken);
        localStorage.setItem('iris_role', newRole);
        setToken(newToken);
        setRole(newRole);
        return res.data;
    };

    const logout = () => {
        localStorage.removeItem('iris_token');
        localStorage.removeItem('iris_role');
        setToken(null);
        setRole(null);
    };

    const isAuthenticated = !!token;

    return (
        <AuthContext.Provider value={{ token, role, login, logout, isAuthenticated, loading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}
