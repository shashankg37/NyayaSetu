import './KnowYourRightsPage.css';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function KnowYourRightsPage() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [category, setCategory] = useState('');
    const [need, setNeed] = useState('');

    const handleCategorySelect = (val: string) => {
        setCategory(val);
    };

    const handleNeedSelect = (val: string) => {
        setNeed(val);
    };

    const resetWizard = () => {
        setCategory('');
        setNeed('');
        setStep(1);
    };

    return (
        <div className="theme-know-your-rights">
            <div className="page">
            {/*  NAV  */}
            <nav className="nav">
              <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
                <div className="ns-badge">NS</div>
                <span className="ns-wordmark">Nyaya Setu</span>
              </div>
              <div className="nav-center">
                <Link to="/">Home</Link>
                <Link to="/ask-nyaya">Ask Nyaya</Link>
                <Link to="/know-your-rights" className="active">Know Your Rights</Link>
              </div>
              <div className="nav-right">
                <button className="btn-login" onClick={() => navigate('/login')}>Login</button>
                <button className="btn-primary" onClick={() => navigate('/signup')}>Get Started</button>
              </div>
            </nav>

            {/*  PROGRESS  */}
            <div className="progress-bar" style={{ padding: '2rem 0 1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div className="progress-label" style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Step {step} of 3</div>
              <div className="progress-dots" style={{ display: 'flex', gap: '0.5rem' }}>
                <div className={`dot ${step >= 1 ? 'active' : ''}`} style={{ width: '10px', height: '10px', borderRadius: '50%', background: step >= 1 ? 'var(--accent-gold)' : 'var(--border-light)' }}></div>
                <div className={`dot ${step >= 2 ? 'active' : ''}`} style={{ width: '10px', height: '10px', borderRadius: '50%', background: step >= 2 ? 'var(--accent-gold)' : 'var(--border-light)' }}></div>
                <div className={`dot ${step >= 3 ? 'active' : ''}`} style={{ width: '10px', height: '10px', borderRadius: '50%', background: step >= 3 ? 'var(--accent-gold)' : 'var(--border-light)' }}></div>
              </div>
            </div>

            {/*  STEPS  */}
            <div className="steps-wrapper" style={{ padding: '2rem 1rem', maxWidth: '800px', margin: '0 auto' }}>
              
              {/*  STEP 1  */}
              {step === 1 && (
                <div className="step visible">
                  <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold', marginBottom: '0.5rem' }}>Who Are You</div>
                  <div className="headline" style={{ fontSize: '2rem', marginBottom: '2rem' }}>I am a...</div>
                  <div className="card-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {[
                      { val: 'woman', label: 'Woman', icon: '👩' },
                      { val: 'farmer', label: 'Farmer', icon: '🚜' },
                      { val: 'worker', label: 'Worker', icon: '👷' },
                      { val: 'senior', label: 'Senior Citizen', icon: '👵' },
                      { val: 'consumer', label: 'Consumer', icon: '🛒' },
                      { val: 'student', label: 'Student', icon: '🎓' },
                      { val: 'entrepreneur', label: 'Entrepreneur', icon: '💼' },
                      { val: 'other', label: 'Other', icon: '👤' }
                    ].map(item => (
                      <div 
                        key={item.val}
                        className={`card ${category === item.val ? 'selected' : ''}`} 
                        onClick={() => handleCategorySelect(item.val)}
                        style={{
                          padding: '1.5rem',
                          background: 'var(--surface)',
                          borderRadius: '8px',
                          border: category === item.val ? '2px solid var(--accent-gold)' : '1px solid var(--border-light)',
                          cursor: 'pointer',
                          textAlign: 'center'
                        }}
                      >
                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{item.icon}</div>
                        <span className="card-label">{item.label}</span>
                      </div>
                    ))}
                  </div>
                  <div className="step-footer" style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                    <button 
                      className="btn-primary" 
                      disabled={!category} 
                      onClick={() => setStep(2)}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/*  STEP 2  */}
              {step === 2 && (
                <div className="step visible">
                  <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold', marginBottom: '0.5rem' }}>What Do You Need</div>
                  <div className="headline" style={{ fontSize: '2rem', marginBottom: '2rem' }}>I need help with...</div>
                  <div className="card-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                    {[
                      { val: 'employment', label: 'Employment', icon: '👔' },
                      { val: 'land', label: 'Land & Property', icon: '🏡' },
                      { val: 'family', label: 'Family', icon: '👨‍👩‍👧‍👦' },
                      { val: 'housing', label: 'Housing', icon: '🏢' },
                      { val: 'money', label: 'Money & Debt', icon: '💰' },
                      { val: 'safety', label: 'Safety', icon: '🛡️' }
                    ].map(item => (
                      <div 
                        key={item.val}
                        className={`card ${need === item.val ? 'selected' : ''}`} 
                        onClick={() => handleNeedSelect(item.val)}
                        style={{
                          padding: '1.5rem',
                          background: 'var(--surface)',
                          borderRadius: '8px',
                          border: need === item.val ? '2px solid var(--accent-gold)' : '1px solid var(--border-light)',
                          cursor: 'pointer',
                          textAlign: 'center'
                        }}
                      >
                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{item.icon}</div>
                        <span className="card-label">{item.label}</span>
                      </div>
                    ))}
                  </div>
                  <div className="step-footer" style={{ marginTop: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <button className="back-link" onClick={() => setStep(1)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>Back</button>
                    <button 
                      className="btn-primary" 
                      disabled={!need} 
                      onClick={() => setStep(3)}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/*  STEP 3  */}
              {step === 3 && (
                <div className="step visible">
                  <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold', marginBottom: '0.5rem' }}>Your Rights</div>
                  <div className="headline" style={{ fontSize: '2rem', marginBottom: '2rem' }}>
                    {category.toUpperCase()} rights regarding {need.toUpperCase()}
                  </div>
                  <div className="results-sections" style={{ background: 'var(--surface)', padding: '2rem', borderRadius: '8px', border: '1px solid var(--border-light)', marginBottom: '2rem' }}>
                    <h4>1. Right to Protection</h4>
                    <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
                      Under Indian law, you are protected against unfair practices, exploitation, and safety violations within this category.
                    </p>
                    <h4>2. Legal Redressal</h4>
                    <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                      You can file petitions, register complaints with dedicated tribunals, or consult free legal aid services if any rights are infringed.
                    </p>
                  </div>
                  <div className="result-actions" style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn-primary" onClick={() => navigate('/ask-nyaya')}>Ask Nyaya</button>
                    <button className="btn-outline-pill" onClick={resetWizard}>Start Over</button>
                  </div>
                </div>
              )}

            </div>
        </div>
        </div>
    );
}
