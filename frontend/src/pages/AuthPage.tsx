import './AuthPage.css';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AuthPage() {
    const [mode, setMode] = useState<'login' | 'signup'>('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [language, setLanguage] = useState('');
    const [consent, setConsent] = useState(false);
    const [error, setError] = useState('');
    
    // Use the encapsulated methods from context, it already handles loading state if needed,
    // but we can manage local loading state too.
    const [loading, setLoading] = useState(false);

    const { login, signup } = useAuth();
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await signup(email, password, language || 'en');
            navigate('/onboarding');
        } catch (err: any) {
            setError(err.message || 'Signup failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="theme-auth">
            <>
            {/* ══════════ NAV ══════════ */}
            <nav>
                <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                    <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '36px', width: 'auto' }} />
                </div>
                <ul className="nav-links">
                    <li><Link to="/">Home</Link></li>
                    <li><Link to="/ask-nyaya">Ask Nyaya</Link></li>
                    <li><Link to="/know-your-rights">Know Your Rights</Link></li>
                </ul>
                <div className="nav-right">
                    <button className="btn-outline-pill" onClick={() => setMode('login')}>Login</button>
                    <button className="btn-primary" onClick={() => setMode('signup')}>Get Started</button>
                </div>
            </nav>

            {/* ══════════ PAGE ══════════ */}
            <div className="page-wrap">
                <div className="auth-card">
                    <div className="eyebrow">Secure Access</div>

                    {/* Tabs */}
                    <div className="tabs">
                        <button 
                            className={`tab-btn ${mode === 'login' ? 'active' : ''}`} 
                            onClick={() => setMode('login')}
                        >
                            Login
                        </button>
                        <button 
                            className={`tab-btn ${mode === 'signup' ? 'active' : ''}`} 
                            onClick={() => setMode('signup')}
                        >
                            Signup
                        </button>
                    </div>

                    {error && <div style={{ color: 'red', marginBottom: '1rem', fontSize: '0.9rem' }}>{error}</div>}

                    {/* LOGIN */}
                    {mode === 'login' && (
                        <div className="form-panel visible">
                            <form onSubmit={handleLogin}>
                                <div className="field">
                                    <label htmlFor="login-email">Email</label>
                                    <input 
                                        type="email" 
                                        id="login-email" 
                                        placeholder="you@example.com" 
                                        autoComplete="email" 
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="field">
                                    <label htmlFor="login-pass">Password</label>
                                    <input 
                                        type="password" 
                                        id="login-pass" 
                                        placeholder="Enter password" 
                                        autoComplete="current-password" 
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                                <button type="submit" className="btn-submit" disabled={loading}>
                                    {loading ? 'Logging in...' : 'Login'}
                                </button>
                            </form>
                            <p className="switch-text">Don't have an account? <span style={{cursor: 'pointer', textDecoration: 'underline'}} onClick={() => setMode('signup')}>Sign up</span></p>
                        </div>
                    )}

                    {/* SIGNUP */}
                    {mode === 'signup' && (
                        <div className="form-panel visible">
                            <form onSubmit={handleSignup}>
                                <div className="field">
                                    <label htmlFor="signup-email">Email</label>
                                    <input 
                                        type="email" 
                                        id="signup-email" 
                                        placeholder="you@example.com" 
                                        autoComplete="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="field">
                                    <label htmlFor="signup-pass">Password</label>
                                    <input 
                                        type="password" 
                                        id="signup-pass" 
                                        placeholder="Enter password" 
                                        autoComplete="new-password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="field">
                                    <label htmlFor="signup-lang">Preferred Language</label>
                                    <select id="signup-lang" value={language} onChange={(e) => setLanguage(e.target.value)} required>
                                        <option value="" disabled>Select language</option>
                                        <option value="en">English</option>
                                        <option value="hi">Hindi</option>
                                        <option value="ta">Tamil</option>
                                        <option value="te">Telugu</option>
                                        <option value="bn">Bengali</option>
                                        <option value="mr">Marathi</option>
                                        <option value="kn">Kannada</option>
                                        <option value="ml">Malayalam</option>
                                        <option value="gu">Gujarati</option>
                                        <option value="pa">Punjabi</option>
                                        <option value="or">Odia</option>
                                        <option value="as">Assamese</option>
                                    </select>
                                </div>
                                <div className="consent-row" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                                    <input 
                                        type="checkbox" 
                                        id="consent" 
                                        checked={consent}
                                        onChange={(e) => setConsent(e.target.checked)}
                                    />
                                    <label htmlFor="consent" style={{ fontSize: '0.85rem' }}>I agree to Nyaya Setu's data use and privacy terms</label>
                                </div>
                                <button type="submit" className="btn-submit" disabled={!consent || loading}>
                                    {loading ? 'Creating Account...' : 'Create Account'}
                                </button>
                            </form>
                            <p className="switch-text">Already have an account? <span style={{cursor: 'pointer', textDecoration: 'underline'}} onClick={() => setMode('login')}>Log in</span></p>
                        </div>
                    )}
                </div>
            </div>
        </>
        </div>
    );
}
