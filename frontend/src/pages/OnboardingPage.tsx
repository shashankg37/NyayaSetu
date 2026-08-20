import './OnboardingPage.css';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function OnboardingPage() {
    const { token } = useAuth();
    const navigate = useNavigate();
    
    const [fullName, setFullName] = useState('');
    const [city, setCity] = useState('');
    const [issueType, setIssueType] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleComplete = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;
        setLoading(true);
        setError('');
        
        try {
            await api.updateProfile(token, {
                full_name: fullName,
                city: city,
                issue_type: issueType
            });
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Failed to update profile');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="theme-onboarding">
            <div className="page">
            <nav className="nav" style={{ borderBottom: 'none' }}>
                <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                    <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '46px', width: 'auto' }} />
                </div>
            </nav>

            <div className="page-wrap" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
                <div className="auth-card" style={{ width: '100%', maxWidth: '500px' }}>
                    <div className="eyebrow" style={{ color: 'var(--accent-gold)' }}>Step 2 of 2</div>
                    <h2 style={{ marginBottom: '0.5rem' }}>Complete your profile</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>This helps us provide more accurate legal information tailored to your jurisdiction.</p>

                    {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

                    <form onSubmit={handleComplete}>
                        <div className="field" style={{ marginBottom: '1.5rem' }}>
                            <label htmlFor="fullName" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Full Name</label>
                            <input 
                                type="text" 
                                id="fullName" 
                                style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-light)', borderRadius: '6px' }}
                                placeholder="E.g. Rajesh Kumar" 
                                value={fullName}
                                onChange={e => setFullName(e.target.value)}
                            />
                        </div>

                        <div className="field" style={{ marginBottom: '1.5rem' }}>
                            <label htmlFor="city" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>City / District</label>
                            <input 
                                type="text" 
                                id="city" 
                                style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-light)', borderRadius: '6px' }}
                                placeholder="E.g. Mumbai, Maharashtra" 
                                value={city}
                                onChange={e => setCity(e.target.value)}
                            />
                        </div>

                        <div className="field" style={{ marginBottom: '2rem' }}>
                            <label htmlFor="issueType" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Primary Legal Interest (Optional)</label>
                            <select 
                                id="issueType" 
                                style={{ width: '100%', padding: '0.75rem', border: '1px solid var(--border-light)', borderRadius: '6px', background: 'var(--bg)' }}
                                value={issueType}
                                onChange={e => setIssueType(e.target.value)}
                            >
                                <option value="">Select an area</option>
                                <option value="property">Property & Real Estate</option>
                                <option value="family">Family & Divorce</option>
                                <option value="consumer">Consumer Rights</option>
                                <option value="labor">Employment & Labor</option>
                                <option value="criminal">Criminal Defense</option>
                                <option value="business">Business & Corporate</option>
                            </select>
                        </div>

                        <button 
                            type="submit" 
                            className="btn-primary" 
                            style={{ width: '100%', padding: '0.75rem' }}
                            disabled={loading}
                        >
                            {loading ? 'Saving...' : 'Go to Dashboard'}
                        </button>
                    </form>
                    <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                        <button className="btn-outline-pill" onClick={() => navigate('/dashboard')} style={{ border: 'none' }}>Skip for now</button>
                    </div>
                </div>
            </div>
        </div>
        </div>
    );
}
