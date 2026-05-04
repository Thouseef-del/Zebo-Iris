import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

export default function LoginPage() {
    const [selectedRole, setSelectedRole] = useState(null);
    const [pin, setPin] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedRole) return setError('Please select a role');
        if (!pin) return setError('Please enter your PIN');

        setLoading(true);
        setError('');

        try {
            await login(selectedRole, pin);
            navigate(`/${selectedRole}`);
        } catch (err) {
            setError(err.response?.data?.message || 'Login failed. Check your PIN.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-bg-effects">
                <div className="login-orb orb-1" />
                <div className="login-orb orb-2" />
                <div className="login-orb orb-3" />
            </div>

            <div className="login-card">
                <div className="login-header">
                    <div className="login-logo">👁️</div>
                    <h1 className="login-title">IrisScan</h1>
                    <p className="login-subtitle">Emergency Identification System</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="role-selector">
                        <button
                            type="button"
                            className={`role-option ${selectedRole === 'admin' ? 'selected' : ''}`}
                            onClick={() => { setSelectedRole('admin'); setError(''); }}
                        >
                            <span className="role-icon">🔑</span>
                            <span className="role-name">Administrator</span>
                            <span className="role-desc">Register patients & manage records</span>
                        </button>

                        <button
                            type="button"
                            className={`role-option ${selectedRole === 'doctor' ? 'selected' : ''}`}
                            onClick={() => { setSelectedRole('doctor'); setError(''); }}
                        >
                            <span className="role-icon">🩺</span>
                            <span className="role-name">Doctor</span>
                            <span className="role-desc">Scan iris & identify patients</span>
                        </button>
                    </div>

                    {selectedRole && (
                        <div className="pin-section">
                            <label className="form-label">Access PIN</label>
                            <input
                                type="password"
                                className="form-input pin-input"
                                value={pin}
                                onChange={(e) => setPin(e.target.value)}
                                placeholder="Enter your PIN"
                                maxLength={8}
                                autoFocus
                            />
                        </div>
                    )}

                    {error && (
                        <div className="status-message status-error">
                            <span>⚠</span> {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        className="btn btn-primary login-btn"
                        disabled={!selectedRole || !pin || loading}
                    >
                        {loading ? (
                            <>
                                <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                                Authenticating…
                            </>
                        ) : (
                            <>🔐 Secure Login</>
                        )}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Biometric Emergency Identification Platform</p>
                </div>
            </div>
        </div>
    );
}
