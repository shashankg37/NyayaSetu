import './KnowYourRightsPage.css';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { rightsDb } from '../data/rightsDb';
import { useAuth } from '../context/AuthContext';

export default function KnowYourRightsPage() {
    const navigate = useNavigate();
    const { token, logout } = useAuth();
    const [step, setStep] = useState(1);
    const [category, setCategory] = useState('');
    const [need, setNeed] = useState('');

    const handleCategorySelect = (val: string) => {
        if (category === val) {
            setCategory('');
        } else {
            setCategory(val);
        }
    };

    const handleNeedSelect = (val: string) => {
        if (need === val) {
            setNeed('');
        } else {
            setNeed(val);
        }
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
              <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '46px', width: 'auto' }} />
              </div>
              <div className="nav-center">
                <Link to="/">Home</Link>
                {token && <Link to="/dashboard">Dashboard</Link>}
                <Link to="/ask-nyaya">Ask Nyaya</Link>
                <Link to="/know-your-rights" className="active">Know Your Rights</Link>
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

            {/*  PROGRESS  */}
            <div className="progress-bar">
              <div className="progress-label">Step {step} of 3</div>
              <div className="progress-dots">
                <div className={`dot ${step >= 1 ? 'active' : ''}`}></div>
                <div className={`dot ${step >= 2 ? 'active' : ''}`}></div>
                <div className={`dot ${step >= 3 ? 'active' : ''}`}></div>
              </div>
            </div>

            {/*  STEPS  */}
            <div className="steps-wrapper">
              
              {/*  STEP 1  */}
              {step === 1 && (
                <div className="step visible">
                  <div className="eyebrow">Who Are You</div>
                  <div className="headline">I am a...</div>
                  <div className="card-grid">
                    {[
                      { val: 'woman', label: 'Woman', icon: 'W' },
                      { val: 'farmer', label: 'Farmer', icon: 'F' },
                      { val: 'worker', label: 'Worker', icon: 'Wo' },
                      { val: 'senior', label: 'Senior Citizen', icon: 'S' },
                      { val: 'consumer', label: 'Consumer', icon: 'C' },
                      { val: 'student', label: 'Student', icon: 'St' },
                      { val: 'entrepreneur', label: 'Entrepreneur', icon: 'E' },
                      { val: 'other', label: 'Other', icon: 'O' }
                    ].map(item => (
                      <div 
                        key={item.val}
                        className={`card ${category === item.val ? 'selected' : ''}`} 
                        onClick={() => handleCategorySelect(item.val)}
                      >
                        <span className="card-icon">{item.icon}</span>
                        <span className="card-label">{item.label}</span>
                      </div>
                    ))}
                  </div>
                  <div className="step-footer">
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
                  <div className="eyebrow">What Do You Need</div>
                  <div className="headline">I need help with...</div>
                  <div className="card-grid">
                    {[
                      { val: 'employment', label: 'Employment', icon: 'Em' },
                      { val: 'land', label: 'Land & Property', icon: 'L' },
                      { val: 'family', label: 'Family', icon: 'Fa' },
                      { val: 'housing', label: 'Housing', icon: 'H' },
                      { val: 'money', label: 'Money & Debt', icon: 'M' },
                      { val: 'safety', label: 'Safety', icon: 'Sa' }
                    ].map(item => (
                      <div 
                        key={item.val}
                        className={`card ${need === item.val ? 'selected' : ''}`} 
                        onClick={() => handleNeedSelect(item.val)}
                      >
                        <span className="card-icon">{item.icon}</span>
                        <span className="card-label">{item.label}</span>
                      </div>
                    ))}
                  </div>
                  <div className="step-footer">
                    <button className="back-link" onClick={() => setStep(1)}>Back</button>
                    <button 
                      className="btn-primary" 
                      disabled={!need} 
                      onClick={() => {
                        setStep(3);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/*  STEP 3  */}
              {step === 3 && (() => {
                const data = rightsDb[category]?.[need] || {
                  title: 'Your Rights',
                  sections: [
                    { heading: 'Your Right', text: 'You have fundamental rights under the Constitution of India including the right to equality (Article 14), the right to life and personal liberty (Article 21), and the right against exploitation (Articles 23-24). Various statutory laws provide additional protections based on your specific situation.' },
                    { heading: 'Your Remedy', text: 'You may approach the District Legal Services Authority for free legal aid under the Legal Services Authorities Act, 1987. For grievances related to government services, file a complaint under the Right to Services Act of your state. For fundamental rights violations, file a writ petition under Article 226 of the Constitution in the High Court.' },
                    { heading: 'What To Do', text: 'Document all relevant facts and gather supporting evidence. Approach the nearest Legal Services Authority or Legal Aid Clinic for free legal advice. File a written complaint with the appropriate authority based on your issue. You may also call the National Legal Aid Helpline (15100) for guidance.' },
                    { heading: 'Where To Go', citations: ['Constitution of India — Articles 14, 21, 226', 'Legal Services Authorities Act, 1987 — Section 12', 'National Legal Aid Helpline: 15100'] }
                  ]
                };
                return (
                  <div className="step visible">
                    <div className="eyebrow">Your Rights</div>
                    <div className="headline">{data.title}</div>
                    <div className="results-sections">
                      {data.sections.map((section, idx) => (
                        <div className="result-block" key={idx}>
                          <h3>{section.heading}</h3>
                          <p>{section.text}</p>
                          {section.citations && section.citations.length > 0 && (
                            <div style={{ marginTop: '8px' }}>
                              {section.citations.map((citation, cIdx) => (
                                <span className="citation-pill" key={cIdx}>{citation}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    <div className="result-actions">
                      <button className="btn-primary" onClick={() => navigate('/ask-nyaya')}>Ask Nyaya</button>
                      <button className="btn-outline-pill" onClick={resetWizard}>Start Over</button>
                    </div>
                  </div>
                );
              })()}

            </div>
        </div>
        </div>
    );
}
