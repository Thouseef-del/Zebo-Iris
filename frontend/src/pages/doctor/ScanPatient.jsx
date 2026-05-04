import { useState, useRef } from 'react';
import api from '../../api/client';

export default function ScanPatient() {
    const [imageFile, setImageFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileSelect = (file) => {
        if (file && file.type.startsWith('image/')) {
            setImageFile(file);
            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target.result);
            reader.readAsDataURL(file);
            setResult(null);
            setError(null);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        handleFileSelect(e.dataTransfer.files[0]);
    };

    const handleScan = async () => {
        if (!imageFile) return;

        setLoading(true);
        setResult(null);
        setError(null);

        const formData = new FormData();
        formData.append('image', imageFile);

        try {
            const res = await api.post('/scan/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(res.data);
        } catch (err) {
            const msg = err.response?.data?.message || 'Scan failed. Please try again.';
            const issues = err.response?.data?.quality_issues;
            setError(issues ? `${msg} Issues: ${issues.join(', ')}` : msg);
        } finally {
            setLoading(false);
        }
    };

    const resetScan = () => {
        setImageFile(null);
        setPreview(null);
        setResult(null);
        setError(null);
    };

    const isMatch = result?.status === 'Match Found';
    const confidence = result ? (1 - (result.hamming_distance ?? 1)) * 100 : 0;

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">👁️ Scan Patient Iris</h1>
                <p className="page-subtitle">
                    Upload a close-up iris photograph to identify the patient
                </p>
            </div>

            {/* Upload Section */}
            {!result && !loading && (
                <div className="glass-card" style={{ maxWidth: 600 }}>
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
                                <div className="upload-zone-icon">👁️</div>
                                <div className="upload-zone-text">
                                    Upload a close-up iris / eye photo
                                </div>
                                <div className="upload-zone-hint">
                                    Click or drag & drop — JPG, PNG supported
                                </div>
                            </>
                        )}
                    </div>

                    {imageFile && (
                        <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
                            <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleScan}>
                                🔍 Scan & Identify
                            </button>
                            <button className="btn btn-secondary" onClick={resetScan}>
                                ✕ Clear
                            </button>
                        </div>
                    )}

                    {error && (
                        <div className="status-message status-error" style={{ marginTop: 16 }}>
                            <span>⚠</span> {error}
                        </div>
                    )}
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="glass-card" style={{ maxWidth: 600 }}>
                    <div className="spinner-overlay">
                        <div className="spinner" />
                        <span className="spinner-text">Analyzing iris pattern…</span>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: 4 }}>
                            Segmenting → Normalizing → Encoding → Matching
                        </p>
                    </div>
                </div>
            )}

            {/* Result */}
            {result && (
                <div className={`result-card ${isMatch ? 'match-found' : 'no-match'}`} style={{ maxWidth: 600 }}>
                    <div className={`result-badge ${isMatch ? 'match' : 'no-match'}`}>
                        {isMatch ? '✓ Patient Identified' : '⚠ No Match Found'}
                    </div>

                    {isMatch ? (
                        <>
                            {/* Confidence */}
                            <div className="confidence-meter">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                        MATCH CONFIDENCE
                                    </span>
                                    <span className="confidence-value">{confidence.toFixed(1)}%</span>
                                </div>
                                <div className="confidence-bar-bg">
                                    <div
                                        className="confidence-bar-fill"
                                        style={{ width: `${confidence}%` }}
                                    />
                                </div>
                            </div>

                            {/* Patient Details */}
                            <div className="result-details">
                                <div className="result-field">
                                    <span className="result-field-label">Patient Name</span>
                                    <span className="result-field-value">{result.user?.name || '—'}</span>
                                </div>
                                <div className="result-field">
                                    <span className="result-field-label">Phone</span>
                                    <span className="result-field-value">{result.user?.phone_no || '—'}</span>
                                </div>
                                <div className="result-field" style={{ gridColumn: '1 / -1' }}>
                                    <span className="result-field-label">Address</span>
                                    <span className="result-field-value">{result.user?.address || '—'}</span>
                                </div>
                                <div className="result-field" style={{ gridColumn: '1 / -1' }}>
                                    <span className="result-field-label">Emergency Contact / Relationship</span>
                                    <span className="result-field-value">{result.user?.relationship || '—'}</span>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div style={{ padding: '16px 0' }}>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                No matching patient was found in the database.
                                Ensure the iris image is clear and taken at close range.
                            </p>
                        </div>
                    )}

                    <div style={{ marginTop: 24 }}>
                        <button className="btn btn-primary" onClick={resetScan}>
                            👁️ New Scan
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
