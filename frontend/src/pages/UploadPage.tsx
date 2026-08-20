import './UploadPage.css';
import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function UploadPage() {
    const { token, logout } = useAuth();
    const navigate = useNavigate();
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file || !token) return;
        setLoading(true);
        setMessage('');
        try {
            await api.uploadDocument(token, file);
            setMessage('Document uploaded successfully!');
            setTimeout(() => {
                navigate('/dashboard');
            }, 1500);
        } catch (err: any) {
            setMessage(err.message || 'Upload failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="theme-upload">
            <div className="page">
            <nav className="nav">
                <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                    <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '46px', width: 'auto' }} />
                </div>
                <div className="nav-center">
                    <Link className="nav-link" to="/">Home</Link>
                    {token && <Link className="nav-link" to="/dashboard">Dashboard</Link>}
                    <Link className="nav-link" to="/ask-nyaya">Ask Nyaya</Link>
                    <Link className="nav-link" to="/know-your-rights">Know Your Rights</Link>
                </div>
                <div className="nav-right">
                    {token ? (
                        <button className="btn-login" onClick={logout}>Logout</button>
                    ) : (
                        <>
                            <button className="btn-login" onClick={() => navigate('/login')}>Login</button>
                            <button className="btn-primary" onClick={() => navigate('/signup')}>Get Started</button>
                        </>
                    )}
                </div>
            </nav>

            <div className="page-wrap" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
                <div className="upload-card" style={{ maxWidth: '600px', width: '100%', padding: '2rem', background: 'var(--surface)', borderRadius: '12px', textAlign: 'center' }}>
                    <div className="eyebrow" style={{ marginBottom: '1rem', color: 'var(--accent-gold)', fontWeight: 'bold' }}>Analyze Document</div>
                    <h2 style={{ marginBottom: '2rem' }}>Upload your legal document</h2>
                    
                    <div 
                        className="upload-dropzone" 
                        style={{ border: '2px dashed var(--border-light)', padding: '3rem', borderRadius: '8px', cursor: 'pointer', marginBottom: '1.5rem', background: 'var(--bg)' }}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        {file ? (
                            <p style={{ fontWeight: 'bold' }}>{file.name}</p>
                        ) : (
                            <>
                                <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" fill="none" style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                                <p>Click or drag a file to this area to upload.</p>
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Support for PDF, DOCX, JPG.</p>
                            </>
                        )}
                        <input 
                            type="file" 
                            ref={fileInputRef} 
                            style={{ display: 'none' }} 
                            onChange={handleFileSelect}
                            accept=".pdf,.doc,.docx,.jpg,.png"
                        />
                    </div>

                    {message && (
                        <div style={{ marginBottom: '1rem', color: message.includes('success') ? 'green' : 'red' }}>
                            {message}
                        </div>
                    )}

                    <button 
                        className="btn-primary" 
                        style={{ width: '100%', padding: '0.75rem', opacity: (!file || loading) ? 0.7 : 1, cursor: (!file || loading) ? 'not-allowed' : 'pointer' }}
                        disabled={!file || loading}
                        onClick={handleUpload}
                    >
                        {loading ? 'Uploading...' : 'Upload & Analyze'}
                    </button>
                </div>
            </div>
        </div>
        </div>
    );
}
