import { useEffect, useState } from 'react';
import api from '../../api/client';

export default function PatientList() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [deleteId, setDeleteId] = useState(null);

    const fetchUsers = () => {
        setLoading(true);
        api.get('/users')
            .then((res) => setUsers(res.data.data || []))
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchUsers(); }, []);

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this patient record?')) return;
        setDeleteId(id);
        try {
            await api.delete(`/users/${id}`);
            setUsers(users.filter((u) => u.id !== id));
        } catch (err) {
            alert(err.response?.data?.message || 'Delete failed');
        } finally {
            setDeleteId(null);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">👥 Patient Records</h1>
                <p className="page-subtitle">
                    All registered patients with iris biometric data — {users.length} total
                </p>
            </div>

            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
                {loading ? (
                    <div className="spinner-overlay">
                        <div className="spinner" />
                        <span className="spinner-text">Loading patients…</span>
                    </div>
                ) : users.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">👤</div>
                        <div className="empty-state-title">No patients registered yet</div>
                        <div className="empty-state-text">
                            Register the first patient from the Admin Dashboard.
                        </div>
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Phone</th>
                                <th>Address</th>
                                <th>Emergency Contact</th>
                                <th>Registered</th>
                                <th style={{ width: 100 }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((user) => (
                                <tr key={user.id}>
                                    <td style={{ fontWeight: 600 }}>{user.name}</td>
                                    <td>{user.phone_no}</td>
                                    <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {user.address}
                                    </td>
                                    <td>{user.relationship}</td>
                                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                        {user.registered_at ? new Date(user.registered_at).toLocaleDateString() : '—'}
                                    </td>
                                    <td>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => handleDelete(user.id)}
                                            disabled={deleteId === user.id}
                                            title="Delete patient"
                                        >
                                            {deleteId === user.id ? '…' : '🗑'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
