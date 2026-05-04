import { useNavigate } from 'react-router-dom';

export default function DoctorDashboard() {
    const navigate = useNavigate();

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">🩺 Doctor Portal</h1>
                <p className="page-subtitle">
                    Emergency iris identification — scan a patient's eye to retrieve their records
                </p>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon" style={{ background: 'rgba(0, 229, 255, 0.1)', color: '#00e5ff' }}>
                        👁️
                    </div>
                    <div className="stat-value" style={{ fontSize: '1.3rem' }}>Ready</div>
                    <div className="stat-label">Iris Scanner</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ background: 'rgba(0, 230, 118, 0.1)', color: '#00e676' }}>
                        🟢
                    </div>
                    <div className="stat-value" style={{ fontSize: '1.3rem' }}>Online</div>
                    <div className="stat-label">Database Connection</div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon" style={{ background: 'rgba(255, 171, 64, 0.1)', color: '#ffab40' }}>
                        ⚡
                    </div>
                    <div className="stat-value" style={{ fontSize: '1.3rem' }}>&lt;2s</div>
                    <div className="stat-label">Avg. Match Time</div>
                </div>
            </div>

            <div
                className="glass-card"
                style={{ cursor: 'pointer', textAlign: 'center', padding: '48px 32px' }}
                onClick={() => navigate('/doctor/scan')}
            >
                <div style={{ fontSize: '4rem', marginBottom: 16 }}>👁️</div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 8 }}>
                    Scan Patient Iris
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: 450, margin: '0 auto 24px' }}>
                    Upload a close-up iris photo to instantly identify a patient and retrieve their
                    emergency contact information.
                </p>
                <span className="btn btn-primary" style={{ fontSize: '1rem', padding: '14px 32px' }}>
                    👁️ Start Iris Scan →
                </span>
            </div>
        </div>
    );
}
