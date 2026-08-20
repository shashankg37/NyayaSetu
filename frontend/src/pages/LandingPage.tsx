import './LandingPage.css';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {
    const navigate = useNavigate();
    const { token, logout } = useAuth();

    return (
        <div className="theme-landing">
            <>
            {/*  NAV  */}
            <nav className="nav">
              <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '46px', width: 'auto' }} />
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
              <div className="hero-content">
                <p className="hero-eyebrow">Bridge to Justice</p>
                <h1 className="hero-headline">Know Your Rights.<br />Know Your Next Step.</h1>
                <div className="hero-actions">
                  {token ? (
                    <button className="btn-primary" onClick={() => navigate('/dashboard')}>Go to Dashboard</button>
                  ) : (
                    <button className="btn-primary" onClick={() => navigate('/signup')}>Get Started</button>
                  )}
                  <button className="btn-outline" onClick={() => navigate('/ask-nyaya')}>Ask Nyaya</button>
                </div>
              </div>
              <div className="hero-image">
                <span className="hero-watermark">JUSTICE</span>
                <img src="/lady.png" alt="Lady Justice" />
              </div>
            </section>

            {/*  HOW IT WORKS  */}
            <section className="how-it-works">
              <div className="how-it-works-inner">
                <div className="hiw-col" onClick={() => navigate('/ask-nyaya')} style={{ cursor: 'pointer' }}>
                  <svg className="hiw-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="8" y="6" width="32" height="36" rx="2"/>
                    <line x1="16" y1="14" x2="32" y2="14"/>
                    <line x1="16" y1="21" x2="32" y2="21"/>
                    <line x1="16" y1="28" x2="26" y2="28"/>
                    <circle cx="36" cy="36" r="8" fill="#FBF8F3" strokeWidth="1.7"/>
                    <line x1="36" y1="33" x2="36" y2="37"/>
                    <circle cx="36" cy="39" r="0.5" fill="currentColor" stroke="none"/>
                  </svg>
                  <p className="hiw-step">Step One</p>
                  <h3 className="hiw-title">Ask</h3>
                  <p className="hiw-desc">Type your legal question in plain language. No jargon needed.</p>
                </div>
                <div className="hiw-col" onClick={() => navigate('/ask-nyaya')} style={{ cursor: 'pointer' }}>
                  <svg className="hiw-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 8h18l8 8v26a2 2 0 0 1-2 2H10a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2z"/>
                    <polyline points="28 8 28 16 36 16"/>
                    <line x1="16" y1="26" x2="32" y2="26"/>
                    <line x1="16" y1="32" x2="28" y2="32"/>
                    <line x1="16" y1="38" x2="24" y2="38"/>
                  </svg>
                  <p className="hiw-step">Step Two</p>
                  <h3 className="hiw-title">Get Grounded Answers</h3>
                  <p className="hiw-desc">Receive analysis backed by Indian law, explained clearly.</p>
                </div>
                <div className="hiw-col" onClick={() => navigate('/draft-document')} style={{ cursor: 'pointer' }}>
                  <svg className="hiw-icon" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="24" y1="6" x2="24" y2="42"/>
                    <line x1="8" y1="6" x2="40" y2="6"/>
                    <path d="M10 14l-4 14h14l-4-14"/>
                    <path d="M38 14l-4 14h14l-4-14"/>
                    <line x1="20" y1="42" x2="28" y2="42"/>
                  </svg>
                  <p className="hiw-step">Step Three</p>
                  <h3 className="hiw-title">Take Action</h3>
                  <p className="hiw-desc">Generate documents, file complaints, or find the right authority.</p>
                </div>
              </div>
            </section>

            {/*  CORE FEATURES  */}
            <section className="features">
              <div className="features-header">
                <p className="features-eyebrow">What We Offer</p>
                <h2 className="features-title">Tools That Empower You</h2>
              </div>
              <div className="features-grid">
                <div className="feature-card" onClick={() => navigate('/ask-nyaya')} style={{ cursor: 'pointer' }}>
                  <p className="feature-eyebrow">AI Assistant</p>
                  <svg className="feature-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="4" y="6" width="28" height="20" rx="2"/>
                    <line x1="12" y1="14" x2="24" y2="14"/>
                    <line x1="12" y1="19" x2="20" y2="19"/>
                    <path d="M14 30l4-4h-8z"/>
                  </svg>
                  <h3 className="feature-title">Ask Nyaya</h3>
                  <p className="feature-desc">Conversational AI trained on Indian legal frameworks. Ask anything — from tenancy disputes to consumer rights — and receive clear, sourced answers.</p>
                </div>
                <div className="feature-card" onClick={() => navigate('/know-your-rights')} style={{ cursor: 'pointer' }}>
                  <p className="feature-eyebrow">Knowledge Base</p>
                  <svg className="feature-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 4h14l8 8v20a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>
                    <polyline points="20 4 20 12 28 12"/>
                    <line x1="10" y1="20" x2="26" y2="20"/>
                    <line x1="10" y1="26" x2="22" y2="26"/>
                  </svg>
                  <h3 className="feature-title">Know Your Rights</h3>
                  <p className="feature-desc">Browse plain-language guides organized by topic — employment, family, property, criminal law, and more — written for citizens, not lawyers.</p>
                </div>
                <div className="feature-card" onClick={() => navigate('/upload')} style={{ cursor: 'pointer' }}>
                  <p className="feature-eyebrow">Document Analysis</p>
                  <svg className="feature-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="6" y="4" width="24" height="28" rx="2"/>
                    <line x1="12" y1="12" x2="24" y2="12"/>
                    <line x1="12" y1="18" x2="24" y2="18"/>
                    <line x1="12" y1="24" x2="20" y2="24"/>
                    <circle cx="26" cy="28" r="6" fill="#FBF8F3" strokeWidth="1.7"/>
                    <line x1="24" y1="28" x2="28" y2="28"/>
                    <line x1="26" y1="26" x2="26" y2="30"/>
                  </svg>
                  <h3 className="feature-title">Document Intelligence</h3>
                  <p className="feature-desc">Upload contracts, notices, or FIRs. Nyaya Setu highlights key clauses, flags risks, and explains obligations in everyday language.</p>
                </div>
                <div className="feature-card" onClick={() => navigate('/draft-document')} style={{ cursor: 'pointer' }}>
                  <p className="feature-eyebrow">Legal Drafting</p>
                  <svg className="feature-icon" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M8 32l2-8L26 6l4 4L14 28z"/>
                    <line x1="22" y1="10" x2="26" y2="14"/>
                    <line x1="8" y1="32" x2="10" y2="34"/>
                    <line x1="24" y1="16" x2="28" y2="20"/>
                  </svg>
                  <h3 className="feature-title">Legal Drafting</h3>
                  <p className="feature-desc">Generate RTI applications, legal notices, complaints, and petitions tailored to your situation — ready to file or send.</p>
                </div>
              </div>
            </section>

            {/*  TRUST BAR  */}
            <section className="trust">
              <h2 className="trust-title">Built for Every Indian Citizen</h2>
              <p className="trust-desc">Available in Hindi, English, and regional languages. No legal training required. No hidden fees. Just clarity when you need it most.</p>
            </section>

            {/*  FOOTER  */}
            <footer className="footer">
              <div className="footer-inner">
                <div className="footer-brand">
                  <div className="footer-logo" style={{ display: 'flex', alignItems: 'center' }}>
                    <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '45px', width: 'auto' }} />
                  </div>
                  <p className="footer-tagline">Bridging the gap between citizens and the law.</p>
                </div>
                <div className="footer-col">
                  <p className="footer-col-title">Product</p>
                  <Link to="/ask-nyaya">Ask Nyaya</Link>
                  <Link to="/know-your-rights">Know Your Rights</Link>
                  <Link to="/upload">Document Analysis</Link>
                  <Link to="/draft-document">Legal Drafting</Link>
                </div>
                <div className="footer-col">
                  <p className="footer-col-title">Resources</p>
                  <Link to="/know-your-rights">Legal Guides</Link>
                  <Link to="#">FAQ</Link>
                  <Link to="#">Blog</Link>
                  <Link to="#">Changelog</Link>
                </div>
                <div className="footer-col">
                  <p className="footer-col-title">Company</p>
                  <Link to="#">About</Link>
                  <Link to="#">Contact</Link>
                  <Link to="#">Privacy Policy</Link>
                  <Link to="#">Terms of Service</Link>
                </div>
              </div>
              <div className="footer-bottom">
                <p className="footer-copy">&copy; 2026 Nyaya Setu. All rights reserved.</p>
              </div>
            </footer>
        </>
        </div>
    );
}
