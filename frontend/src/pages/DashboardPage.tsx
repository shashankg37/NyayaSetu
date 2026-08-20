import './DashboardPage.css';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type AuthUser } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
    const { token, logout } = useAuth();
    const [profile, setProfile] = useState<AuthUser | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            api.getProfile(token)
                .then(setProfile)
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [token]);

    return (
        <div className="theme-dashboard">
            <div className="page">
            <nav className="nav">
                <div className="nav-left">
                    <div className="ns-badge">NS</div>
                    <span className="ns-wordmark">Nyaya Setu</span>
                </div>
                <div className="nav-center">
                    <Link className="nav-link" to="/">Home</Link>
                    <Link className="nav-link" to="/ask-nyaya">Ask Nyaya</Link>
                    <Link className="nav-link" to="/upload">Upload Document</Link>
                </div>
                <div className="nav-right">
                    <button className="btn-outline-pill" onClick={logout}>Logout</button>
                </div>
            </nav>

            <div className="page-wrap" style={{ padding: '4rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
                <div className="eyebrow" style={{ color: 'var(--accent-gold)', marginBottom: '1rem', fontWeight: 'bold' }}>Your Hub</div>
                <h1 style={{ marginBottom: '2rem' }}>
                    {loading ? 'Loading...' : `Welcome, ${profile?.full_name || profile?.email?.split('@')[0] || 'User'}`}
                </h1>

                <div className="dashboard-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
                    <div className="dashboard-card" style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                        <h3>Ask Nyaya</h3>
                        <p style={{ margin: '1rem 0', color: 'var(--text-secondary)' }}>Get instant legal guidance grounded in Indian law.</p>
                        <Link to="/ask-nyaya" className="btn-primary" style={{ display: 'inline-block', textDecoration: 'none' }}>Start Chat</Link>
                    </div>

                    <div className="dashboard-card" style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                        <h3>Analyze Document</h3>
                        <p style={{ margin: '1rem 0', color: 'var(--text-secondary)' }}>Upload legal notices, contracts, or FIRs for AI analysis.</p>
                        <Link to="/upload" className="btn-primary" style={{ display: 'inline-block', textDecoration: 'none' }}>Upload File</Link>
                    </div>

                    <div className="dashboard-card" style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                        <h3>Know Your Rights</h3>
                        <p style={{ margin: '1rem 0', color: 'var(--text-secondary)' }}>Explore legal guides, templates, and procedures.</p>
                        <Link to="/know-your-rights" className="btn-primary" style={{ display: 'inline-block', textDecoration: 'none' }}>Explore Library</Link>
                    </div>
                </div>
            </div>
        </div>
        </div>
    );
}
