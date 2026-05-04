import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const adminLinks = [
    { to: '/admin', icon: '📊', label: 'Dashboard', end: true },
    { to: '/admin/register', icon: '🧬', label: 'Register Patient' },
    { to: '/admin/patients', icon: '👥', label: 'Patient Records' },
];

const doctorLinks = [
    { to: '/doctor', icon: '📊', label: 'Dashboard', end: true },
    { to: '/doctor/scan', icon: '👁️', label: 'Scan Iris' },
];

export default function Sidebar() {
    const { role } = useAuth();
    const links = role === 'admin' ? adminLinks : doctorLinks;

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="sidebar-logo">👁️</div>
                <div>
                    <div className="sidebar-title">IrisScan</div>
                    <div className="sidebar-version">Emergency ID System</div>
                </div>
            </div>

            <nav className="sidebar-nav">
                <div className="sidebar-section-label">Navigation</div>
                {links.map((link) => (
                    <NavLink
                        key={link.to}
                        to={link.to}
                        end={link.end}
                        className={({ isActive }) =>
                            `sidebar-link ${isActive ? 'active' : ''}`
                        }
                    >
                        <span className="sidebar-link-icon">{link.icon}</span>
                        <span>{link.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="sidebar-role-badge">
                    {role === 'admin' ? '🔑 Administrator' : '🩺 Doctor'}
                </div>
            </div>
        </aside>
    );
}
