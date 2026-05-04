import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, allowedRoles }) {
    const { isAuthenticated, role, loading } = useAuth();

    if (loading) {
        return (
            <div className="spinner-overlay">
                <div className="spinner" />
                <span className="spinner-text">Verifying session…</span>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (allowedRoles && !allowedRoles.includes(role)) {
        return <Navigate to={`/${role}`} replace />;
    }

    return children;
}
