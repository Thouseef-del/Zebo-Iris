import { useState, useRef } from 'react';
import api from '../../api/client';

export default function RegisterPatient() {
    const [form, setForm] = useState({
        name: '',
        address: '',
        phone_no: '',
        relationship: '',
    });
    const [imageFile, setImageFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [status, setStatus] = useState(null); // { type, message }
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef(null);

    const handleChange = (e) => {
        setForm({ ...form, [e.target.name]: e.target.value });
    };

    const handleFileSelect = (file) => {
        if (file && file.type.startsWith('image/')) {
            setImageFile(file);
            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target.result);
            reader.readAsDataURL(file);
            setStatus(null);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        handleFileSelect(file);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus(null);

        if (!form.name || !form.address || !form.phone_no || !form.relationship) {
            return setStatus({ type: 'error', message: 'All fields are required.' });
        }
        if (!imageFile) {
            return setStatus({ type: 'error', message: 'Please upload an iris image.' });
        }

        setLoading(true);

        const formData = new FormData();
        formData.append('name', form.name);
        formData.append('address', form.address);
        formData.append('phone_no', form.phone_no);
        formData.append('relationship', form.relationship);
        formData.append('image', imageFile);

        try {
            const res = await api.post('/register/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            setStatus({
                type: 'success',
                message: `Patient registered successfully! ID: ${res.data.user_id} (Quality: ${(res.data.quality_score * 100).toFixed(0)}%)`,
            });

            // Reset form
            setForm({ name: '', address: '', phone_no: '', relationship: '' });
            setImageFile(null);
            setPreview(null);
        } catch (err) {
            const msg = err.response?.data?.message || 'Registration failed.';
            const issues = err.response?.data?.quality_issues;
            setStatus({
                type: 'error',
                message: issues ? `${msg} Issues: ${issues.join(', ')}` : msg,
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">🧬 Register New Patient</h1>
                <p className="page-subtitle">
                    Enter patient details and upload an iris image for biometric registration
                </p>
            </div>

            <form onSubmit={handleSubmit} className="glass-card" style={{ maxWidth: 700 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 20px' }}>
                    <div className="form-group">
                        <label className="form-label">Full Name</label>
                        <input
                            className="form-input"
                            name="name"
                            value={form.name}
                            onChange={handleChange}
                            placeholder="e.g. John Doe"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Phone Number</label>
                        <input
                            className="form-input"
                            name="phone_no"
                            value={form.phone_no}
                            onChange={handleChange}
                            placeholder="e.g. +91-9876543210"
                        />
                    </div>

                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                        <label className="form-label">Address</label>
                        <input
                            className="form-input"
                            name="address"
                            value={form.address}
                            onChange={handleChange}
                            placeholder="Full address"
                        />
                    </div>

                    <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                        <label className="form-label">Emergency Contact / Relationship</label>
                        <input
                            className="form-input"
                            name="relationship"
                            value={form.relationship}
                            onChange={handleChange}
                            placeholder="e.g. Father — Rajesh Doe — +91-1234567890"
                        />
                    </div>
                </div>

                {/* Image Upload */}
                <div className="form-group" style={{ marginTop: 8 }}>
                    <label className="form-label">Iris Image</label>
                    <div
                        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                        onClick={() => fileInputRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            style={{ display: 'none' }}
                            onChange={(e) => handleFileSelect(e.target.files[0])}
                        />
                        {preview ? (
                            <div className="upload-preview">
                                <img src={preview} alt="Iris preview" />
                            </div>
                        ) : (
                            <>
                                <div className="upload-zone-icon">📷</div>
                                <div className="upload-zone-text">
                                    Click to upload or drag & drop an iris image
                                </div>
                                <div className="upload-zone-hint">
                                    Supported: JPG, PNG — close-up eye / iris photo recommended
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {status && (
                    <div className={`status-message status-${status.type}`}>
                        <span>{status.type === 'success' ? '✓' : '⚠'}</span>
                        {status.message}
                    </div>
                )}

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                    style={{ width: '100%', marginTop: 8 }}
                >
                    {loading ? (
                        <>
                            <div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                            Processing Iris…
                        </>
                    ) : (
                        '🧬 Register Patient'
                    )}
                </button>
            </form>
        </div>
    );
}
