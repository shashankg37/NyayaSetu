import './DashboardPage.css';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type AuthUser } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
    const navigate = useNavigate();
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
                <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
                    <div className="ns-badge">NS</div>
                    <span className="ns-wordmark">Nyaya Setu</span>
                </div>
                <div className="nav-center">
                    <Link className="nav-link" to="/">Home</Link>
                    <Link className="nav-link active" to="/dashboard">Dashboard</Link>
                    <Link className="nav-link" to="/ask-nyaya">Ask Nyaya</Link>
                    <Link className="nav-link" to="/know-your-rights">Know Your Rights</Link>
                </div>
                <div className="nav-right">
                    <button className="btn-login" onClick={logout}>Logout</button>
                </div>
            </nav>

            <div className="page-wrap" style={{ padding: '4rem 2rem', maxWidth: '1200px', margin: '0 auto' }}>
                <h1 style={{ marginBottom: '2rem' }}>
                    {loading ? 'Loading...' : `Welcome, ${profile?.full_name || profile?.email?.split('@')[0] || 'User'}`}
                </h1>

                <div className="dashboard-grid">
                    <div className="dashboard-card">
                        <h3>Ask Nyaya</h3>
                        <p>Get instant legal guidance grounded in Indian law.</p>
                        <Link to="/ask-nyaya" className="dashboard-btn">Start Chat</Link>
                    </div>

                    <div className="dashboard-card">
                        <h3>Analyze Document</h3>
                        <p>Upload legal notices, contracts, or FIRs for AI analysis.</p>
                        <Link to="/upload" className="dashboard-btn">Upload File</Link>
                    </div>

                    <div className="dashboard-card">
                        <h3>Know Your Rights</h3>
                        <p>Explore legal guides, templates, and procedures.</p>
                        <Link to="/know-your-rights" className="dashboard-btn">Explore Library</Link>
                    </div>
                </div>
            </div>
        </div>
        </div>
    );
}
