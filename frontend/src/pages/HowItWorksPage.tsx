import './HowItWorksPage.css';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function HowItWorksPage() {
    const navigate = useNavigate();
    const { token, logout } = useAuth();

    return (
        <div className="theme-how-it-works">
            <>
            {/*  NAV  */}
            <nav className="nav">
              <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
                <div className="ns-badge">NS</div>
                <span className="ns-wordmark">Nyaya Setu</span>
              </div>
              <div className="nav-center">
                <Link to="/">Home</Link>
                {token && <Link to="/dashboard">Dashboard</Link>}
                <Link to="/ask-nyaya">Ask Nyaya</Link>
                <Link to="/know-your-rights">Know Your Rights</Link>
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

            {/*  HERO  */}
            <section className="hero">
              <p className="eyebrow">How It Works</p>
              <h1>Three steps to justice</h1>
              <p>Nyaya Setu makes legal guidance accessible. No jargon, no confusion &mdash; just clear answers and actionable steps.</p>
            </section>

            {/*  STEPS  */}
            <section className="steps-section">
              <div className="steps-track">
                {/*  Step 01  */}
                <div className="step">
                  <div className="step-left">
                    <div className="step-icon">
                      <svg viewBox="0 0 24 24">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                    </div>
                    <span className="step-number">01</span>
                  </div>
                  <div className="step-right">
                    <h3>Ask Your Question</h3>
                    <p>Type or speak your legal question in any language. Nyaya Setu understands plain language &mdash; no legal terminology needed.</p>
                  </div>
                </div>

                {/*  Step 02  */}
                <div className="step">
                  <div className="step-left">
                    <div className="step-icon">
                      <svg viewBox="0 0 24 24">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="9" y1="13" x2="15" y2="13"/>
                        <line x1="9" y1="17" x2="13" y2="17"/>
                      </svg>
                    </div>
                    <span className="step-number">02</span>
                  </div>
                  <div className="step-right">
                    <h3>Get Grounded Answers</h3>
                    <p>Receive clear, structured guidance: your rights under Indian law, what the law says, and what you can do &mdash; with citations to actual Acts and Sections.</p>
                  </div>
                </div>

                {/*  Step 03  */}
                <div className="step">
                  <div className="step-left">
                    <div className="step-icon">
                      <svg viewBox="0 0 24 24">
                        <line x1="12" y1="2" x2="12" y2="22"/>
                        <polyline points="18 8 12 2 6 8"/>
                        <line x1="4" y1="12" x2="20" y2="12"/>
                        <path d="M8 20l4-4 4 4"/>
                      </svg>
                    </div>
                    <span className="step-number">03</span>
                  </div>
                  <div className="step-right">
                    <h3>Take Action</h3>
                    <p>Draft legal documents, simulate your case timeline, or connect with legal aid &mdash; all from one place.</p>
                  </div>
                </div>
              </div>
            </section>

            {/*  CTA  */}
            <section className="cta-section">
              <h2>Ready to know your rights?</h2>
              <div className="cta-buttons">
                <button className="btn-primary" onClick={() => navigate('/signup')}>Get Started</button>
                <button className="btn-outline" onClick={() => navigate('/ask-nyaya')}>Ask Nyaya</button>
              </div>
            </section>

            {/*  FOOTER  */}
            <footer className="footer" style={{ padding: '2rem', textAlign: 'center', borderTop: '1px solid var(--border-light)' }}>
              <span>&copy; 2026 Nyaya Setu</span>
            </footer>
        </>
        </div>
    );
}
