import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

type AuthPageProps = {
  mode: 'login' | 'signup';
};

export default function AuthPage({ mode }: AuthPageProps) {
  const navigate = useNavigate();
  const { login, signup, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('en');
  const [error, setError] = useState('');

  const isSignup = mode === 'signup';

  const validate = () => {
    if (!email.trim() || !email.includes('@')) {
      return 'Please enter a valid email address.';
    }

    if (password.length < 8) {
      return 'Password must be at least 8 characters long.';
    }

    if (isSignup && password !== confirmPassword) {
      return 'Passwords do not match.';
    }

    return '';
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      if (isSignup) {
        await signup(email, password, preferredLanguage);
        navigate('/onboarding');
      } else {
        await login(email, password);
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed. Please try again.');
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <Link to="/" className="brand-mark auth-brand">
          <span className="brand-icon">NS</span>
          <span className="brand-word">Nyaya Setu</span>
        </Link>

        <div className="auth-copy">
          <span className="eyebrow">SECURE ACCESS</span>
          <h1>{isSignup ? 'Create your account' : 'Welcome back'}</h1>
          <p>
            {isSignup
              ? 'Start your legal-awareness journey with secure account access.'
              : 'Sign in to resume your legal guidance dashboard.'}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Email address</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>

          <label>
            <span>Password</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </label>

          {isSignup && (
            <>
              <label>
                <span>Confirm password</span>
                <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
              </label>

              <label>
                <span>Preferred language</span>
                <select value={preferredLanguage} onChange={(e) => setPreferredLanguage(e.target.value)}>
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                  <option value="kn">Kannada</option>
                  <option value="ml">Malayalam</option>
                  <option value="ta">Tamil</option>
                </select>
              </label>
            </>
          )}

          {error && <div className="error-banner">{error}</div>}

          <button type="submit" className="primary-button full-width" disabled={loading}>
            {loading ? 'Please wait...' : isSignup ? 'Create Account' : 'Login'}
          </button>
        </form>

        <div className="auth-switch">
          {isSignup ? 'Already have an account?' : 'Need an account?'}{' '}
          <Link to={isSignup ? '/login' : '/signup'}>{isSignup ? 'Sign in' : 'Create one'}</Link>
        </div>
      </div>
    </div>
  );
}
