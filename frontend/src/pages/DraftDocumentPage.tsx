import './DraftDocumentPage.css';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function DraftDocumentPage() {
    const navigate = useNavigate();
    const { token, logout } = useAuth();
    const [step, setStep] = useState(1);
    const [docType, setDocType] = useState('');
    const [recipient, setRecipient] = useState('');
    const [details, setDetails] = useState('');

    const handleSelectOption = (type: string) => {
        setDocType(type);
    };

    const resetWizard = () => {
        setDocType('');
        setRecipient('');
        setDetails('');
        setStep(1);
    };

    const getPreviewHtml = () => {
        if (step === 1 && !docType) {
            return '<div className="paper-empty">Your document preview will appear here once you begin.</div>';
        }

        const today = new Date();
        const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
        const dateStr = today.getDate() + ' ' + months[today.getMonth()] + ' ' + today.getFullYear();
        const headerText = (docType || 'Legal Notice').toUpperCase();

        const toLine = recipient ? recipient : '[Recipient Name & Address]';
        let bodyHtml = '';

        if (docType === 'Legal Notice') {
            if (details) {
                bodyHtml = `<p>Dear Sir/Madam,</p>
                <p>Under instructions from and on behalf of my client, <strong>[Client Name]</strong>, I hereby serve you with the following legal notice:</p>
                <p>${details}</p>
                <p>You are called upon to remedy the grievance and comply with the demands within 15 days, failing which we will initiate legal action.</p>`;
            } else {
                bodyHtml = `<p>Dear Sir/Madam,</p>
                <p>Under instructions from and on behalf of my client, I hereby serve you with the following legal notice regarding the dispute.</p>`;
            }
        } else if (docType === 'Rental Agreement') {
            bodyHtml = `<p><strong>THIS RENTAL AGREEMENT</strong> is executed on ${dateStr}.</p>
            <p><strong>BETWEEN Landlord:</strong> ${toLine}</p>
            <p><strong>AND Tenant:</strong> [Tenant Name]</p>
            <p><strong>Terms:</strong> ${details || '[Details of agreement]'}</p>`;
        } else {
            bodyHtml = `<p>This document is executed on ${dateStr}.</p>
            <p><strong>To:</strong> ${toLine}</p>
            <p>${details || '[Document details will appear here]'}</p>`;
        }

        return `
            <div className="paper-header" style="font-weight: bold; font-size: 1.5rem; text-align: center; margin-bottom: 2rem;">${headerText}</div>
            <div className="paper-field"><strong>Date:</strong> ${dateStr}</div>
            <div className="paper-field"><strong>To:</strong> ${toLine}</div>
            <div className="paper-field"><strong>From:</strong> ${docType === 'Legal Notice' ? '[Advocate Name], Advocate' : '[Your Name]'}</div>
            <div className="paper-body" style="margin-top: 2rem; line-height: 1.6;">${bodyHtml}</div>
            <div className="paper-sig" style="margin-top: 3rem; border-top: 1px solid #ccc; width: 200px; padding-top: 0.5rem;">
                <div>Authorized Signatory</div>
            </div>
        `;
    };

    return (
        <div className="theme-draft-document">
            <div className="page">
            {/*  NAV  */}
            <nav className="nav">
              <div className="nav-left" onClick={() => navigate('/')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <img src="/logo.png" alt="Nyaya Setu Logo" style={{ height: '36px', width: 'auto' }} />
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

            <div className="page-wrap" style={{ display: 'flex', gap: '2rem', padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
              
              {/*  LEFT: Wizard  */}
              <div className="wizard-col" style={{ flex: 1, background: 'var(--surface)', padding: '2rem', borderRadius: '12px', border: '1px solid var(--border-light)' }}>
                <div className="progress-dots" style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
                  {[1, 2, 3, 4].map(s => (
                    <div 
                      key={s}
                      className={`dot ${step === s ? 'active' : ''}`} 
                      style={{ 
                        width: '12px', 
                        height: '12px', 
                        borderRadius: '50%', 
                        background: step >= s ? 'var(--accent-gold)' : 'var(--border-light)' 
                      }}
                    ></div>
                  ))}
                </div>

                {/*  STEP 1  */}
                {step === 1 && (
                  <div className="step visible">
                    <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold' }}>DOCUMENT DRAFTING</div>
                    <h2 className="step-headline" style={{ margin: '1rem 0' }}>What do you need to draft?</h2>
                    <div className="option-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', margin: '1.5rem 0' }}>
                      {[
                        'Legal Notice',
                        'Rental Agreement',
                        'Employment Contract',
                        'Power of Attorney',
                        'Consumer Complaint',
                        'Other'
                      ].map(type => (
                        <div 
                          key={type}
                          className={`option-card ${docType === type ? 'selected' : ''}`}
                          onClick={() => handleSelectOption(type)}
                          style={{
                            padding: '1rem',
                            border: docType === type ? '2px solid var(--accent-gold)' : '1px solid var(--border-light)',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '1rem'
                          }}
                        >
                          <div style={{
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            border: '2px solid var(--text-secondary)',
                            background: docType === type ? 'var(--accent-gold)' : 'transparent'
                          }}></div>
                          <span>{type}</span>
                        </div>
                      ))}
                    </div>
                    <button className="btn-primary" disabled={!docType} onClick={() => setStep(2)}>Next</button>
                  </div>
                )}

                {/*  STEP 2  */}
                {step === 2 && (
                  <div className="step visible">
                    <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold' }}>DOCUMENT DRAFTING</div>
                    <h2 className="step-headline" style={{ margin: '1rem 0' }}>Who is this addressed to?</h2>
                    <input 
                      className="field-input" 
                      type="text"
                      placeholder="e.g., Landlord, Employer, Consumer Forum"
                      value={recipient}
                      onChange={e => setRecipient(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid var(--border-light)',
                        borderRadius: '6px',
                        marginBottom: '1.5rem'
                      }}
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <button className="back-link" onClick={() => setStep(1)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>&larr; Back</button>
                      <button className="btn-primary" disabled={!recipient.trim()} onClick={() => setStep(3)}>Next</button>
                    </div>
                  </div>
                )}

                {/*  STEP 3  */}
                {step === 3 && (
                  <div className="step visible">
                    <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold' }}>DOCUMENT DRAFTING</div>
                    <h2 className="step-headline" style={{ margin: '1rem 0' }}>What should it say?</h2>
                    <textarea 
                      className="field-textarea"
                      placeholder="Describe the main points you want addressed in this document..."
                      value={details}
                      onChange={e => setDetails(e.target.value)}
                      style={{
                        width: '100%',
                        height: '150px',
                        padding: '0.75rem',
                        border: '1px solid var(--border-light)',
                        borderRadius: '6px',
                        marginBottom: '1.5rem'
                      }}
                    ></textarea>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <button className="back-link" onClick={() => setStep(2)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>&larr; Back</button>
                      <button className="btn-primary" onClick={() => setStep(4)}>Next</button>
                    </div>
                  </div>
                )}

                {/*  STEP 4  */}
                {step === 4 && (
                  <div className="step visible">
                    <div className="eyebrow" style={{ color: 'var(--accent-gold)', fontWeight: 'bold' }}>DOCUMENT DRAFTING</div>
                    <h2 className="step-headline" style={{ margin: '1rem 0' }}>Your Document is Ready</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Review your document on the right. You can export it when ready.</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <button className="back-link" onClick={() => setStep(3)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>&larr; Edit details</button>
                      <button className="btn-outline-pill" onClick={resetWizard}>Start Over</button>
                    </div>
                  </div>
                )}
              </div>

              {/*  RIGHT: Preview  */}
              <div className="preview-col" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div 
                  className="paper" 
                  style={{ 
                    background: '#fff', 
                    color: '#333', 
                    padding: '3rem', 
                    borderRadius: '8px', 
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)', 
                    minHeight: '400px' 
                  }}
                  dangerouslySetInnerHTML={{ __html: getPreviewHtml() }}
                />

                {step === 4 && (
                  <div className="export-row" style={{ display: 'flex', gap: '1rem' }}>
                    <button className="btn-primary" style={{ flex: 1 }} onClick={() => alert('PDF Export requires a backend configuration')}>Export as PDF</button>
                    <button className="btn-primary" style={{ flex: 1 }} onClick={() => alert('DOCX Export requires a backend configuration')}>Export as DOCX</button>
                  </div>
                )}
              </div>
            </div>
        </div>
        </div>
    );
}
