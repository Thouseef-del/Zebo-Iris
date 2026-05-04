import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Header.css';

export default function Header() {
    const { role, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <header className="app-header">
            <div className="header-left">
                <div className="header-status">
                    <span className="status-dot" />
                    <span className="status-text">System Online</span>
                </div>
            </div>

            <div className="header-right">
                <div className="header-role">
                    <span className="header-role-icon">
                        {role === 'admin' ? '🔑' : '🩺'}
                    </span>
                    <span className="header-role-text">
                        {role === 'admin' ? 'Admin Panel' : 'Doctor Portal'}
                    </span>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                    ⏻ Logout
                </button>
            </div>
        </header>
    );
}
