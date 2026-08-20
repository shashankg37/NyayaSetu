import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const stepLabels = ['Profile', 'Details', 'Consent'];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, token, updateProfile } = useAuth();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    fullName: user?.full_name ?? '',
    phone: user?.phone ?? '',
    city: user?.city ?? '',
    issueType: user?.issue_type ?? 'general',
    consentGiven: user?.consent_given ?? false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const updateField = (key: keyof typeof form, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => ({ ...prev, [key]: '' }));
  };

  const validateStep = () => {
    const nextErrors: Record<string, string> = {};

    if (step === 0 && !form.fullName.trim()) nextErrors.fullName = 'Full name is required.';
    if (step === 1 && !form.phone.trim()) nextErrors.phone = 'Phone number is required.';
    if (step === 1 && !form.city.trim()) nextErrors.city = 'City is required.';
    if (step === 2 && !form.consentGiven) nextErrors.consentGiven = 'Please accept the consent statement to continue.';

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const nextStep = () => {
    if (!validateStep()) return;
    setStep((current) => Math.min(current + 1, stepLabels.length - 1));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!validateStep()) return;
    if (!token) {
      navigate('/login');
      return;
    }

    setSubmitting(true);
    try {
      await updateProfile({
        full_name: form.fullName,
        phone: form.phone,
        city: form.city,
        issue_type: form.issueType,
        preferred_language: user?.preferred_language ?? 'en',
        consent_given: form.consentGiven,
      });
      navigate('/dashboard');
    } catch (err) {
      setErrors({ consentGiven: err instanceof Error ? err.message : 'Unable to save onboarding details.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-shell onboarding-shell">
      <div className="auth-panel onboarding-panel">
        <Link to="/" className="brand-mark auth-brand">
          <span className="brand-icon">NS</span>
          <span className="brand-word">Nyaya Setu</span>
        </Link>

        <div className="auth-copy">
          <span className="eyebrow">ONBOARDING</span>
          <h1>Tell us about your legal need.</h1>
          <p>We’ll use this to tailor guidance and help you take the next right step.</p>
        </div>

        <div className="stepper" aria-label="Onboarding progress">
          {stepLabels.map((label, index) => (
            <div key={label} className={`step-dot ${index <= step ? 'active' : ''}`}>
              <span>{index + 1}</span>
              <small>{label}</small>
            </div>
          ))}
        </div>

        <form className="auth-form onboarding-form" onSubmit={handleSubmit}>
          {step === 0 && (
            <label>
              <span>Full name</span>
              <input
                type="text"
                value={form.fullName}
                onChange={(e) => updateField('fullName', e.target.value)}
                placeholder="Your full name"
              />
              {errors.fullName && <small className="field-error">{errors.fullName}</small>}
            </label>
          )}

          {step === 1 && (
            <>
              <label>
                <span>Phone number</span>
                <input
                  type="tel"
                  value={form.phone}
                  onChange={(e) => updateField('phone', e.target.value)}
                  placeholder="+91 98765 43210"
                />
                {errors.phone && <small className="field-error">{errors.phone}</small>}
              </label>

              <label>
                <span>City / location</span>
                <input
                  type="text"
                  value={form.city}
                  onChange={(e) => updateField('city', e.target.value)}
                  placeholder="Bengaluru"
                />
                {errors.city && <small className="field-error">{errors.city}</small>}
              </label>

              <label>
                <span>Issue type</span>
                <select value={form.issueType} onChange={(e) => updateField('issueType', e.target.value)}>
                  <option value="general">General legal query</option>
                  <option value="employment">Employment</option>
                  <option value="property">Property</option>
                  <option value="family">Family</option>
                  <option value="consumer">Consumer</option>
                </select>
              </label>
            </>
          )}

          {step === 2 && (
            <div className="consent-box">
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.consentGiven}
                  onChange={(e) => updateField('consentGiven', e.target.checked)}
                />
                <span>I consent to use my profile and document details to help me understand my legal issue and receive guidance.</span>
              </label>
              {errors.consentGiven && <small className="field-error">{errors.consentGiven}</small>}
              <div className="info-line">Signed in as {user?.email ?? 'your account'}</div>
            </div>
          )}

          {step < stepLabels.length - 1 ? (
            <button type="button" className="primary-button full-width" onClick={nextStep}>
              Continue
            </button>
          ) : (
            <button type="submit" className="primary-button full-width" disabled={submitting}>
              {submitting ? 'Saving...' : 'Finish onboarding'}
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
