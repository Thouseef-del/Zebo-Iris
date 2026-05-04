import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';

export default function AdminDashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        api.get('/stats')
            .then((res) => setStats(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">📊 Admin Dashboard</h1>
                <p className="page-subtitle">Overview of the iris recognition system</p>
            </div>

            {loading ? (
                <div className="spinner-overlay">
                    <div className="spinner" />
                    <span className="spinner-text">Loading statistics…</span>
                </div>
            ) : (
                <>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-icon" style={{ background: 'rgba(0, 229, 255, 0.1)', color: '#00e5ff' }}>
                                👥
                            </div>
                            <div className="stat-value">{stats?.total_registered_users ?? 0}</div>
                            <div className="stat-label">Total Registered Patients</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-icon" style={{ background: 'rgba(0, 230, 118, 0.1)', color: '#00e676' }}>
                                🟢
                            </div>
                            <div className="stat-value">Online</div>
                            <div className="stat-label">System Status</div>
                        </div>

                        <div className="stat-card">
                            <div className="stat-icon" style={{ background: 'rgba(255, 171, 64, 0.1)', color: '#ffab40' }}>
                                🧬
                            </div>
                            <div className="stat-value">Active</div>
                            <div className="stat-label">Iris Engine</div>
                        </div>
                    </div>

                    <div className="stats-grid">
                        <div
                            className="glass-card"
                            style={{ cursor: 'pointer' }}
                            onClick={() => navigate('/admin/register')}
                        >
                            <h3 style={{ marginBottom: 8, fontSize: '1rem' }}>🧬 Register New Patient</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                Add a new patient with iris biometric data for emergency identification.
                            </p>
                            <div style={{ marginTop: 16 }}>
                                <span className="btn btn-primary" style={{ fontSize: '0.8rem' }}>
                                    Start Registration →
                                </span>
                            </div>
                        </div>

                        <div
                            className="glass-card"
                            style={{ cursor: 'pointer' }}
                            onClick={() => navigate('/admin/patients')}
                        >
                            <h3 style={{ marginBottom: 8, fontSize: '1rem' }}>👥 View Patient Records</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                                Browse and manage all registered patient iris records.
                            </p>
                            <div style={{ marginTop: 16 }}>
                                <span className="btn btn-secondary" style={{ fontSize: '0.8rem' }}>
                                    View Records →
                                </span>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
