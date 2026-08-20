import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type MessageItem = {
  role: 'user' | 'assistant';
  content: string;
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuth();
  const [message, setMessage] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<MessageItem[]>([
    {
      role: 'assistant',
      content: 'Hi! I can help you understand your legal issue, review documents, or guide you to the next right step.',
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!message.trim() || !token) return;

    const input = message.trim();
    setError('');
    setMessage('');
    setIsSending(true);

    try {
      const response = await api.askQuestion(token, input, conversationId);
      setConversationId(response.conversation_id);

      const fallbackText = typeof response.reply?.your_right === 'string'
        ? response.reply.your_right
        : typeof response.reply?.summary === 'string'
          ? response.reply.summary
          : JSON.stringify(response.reply ?? {});

      setChatMessages((prev) => [
        ...prev,
        { role: 'user', content: input },
        { role: 'assistant', content: fallbackText },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to send message.');
    } finally {
      setIsSending(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="dashboard-shell">
      <header className="dashboard-topbar">
        <div className="max-shell dashboard-nav">
          <Link to="/" className="brand-mark">
            <span className="brand-icon">NS</span>
            <span className="brand-word">Nyaya Setu</span>
          </Link>

          <div className="dashboard-actions">
            <span className="user-pill">{user?.email ?? 'Citizen'}</span>
            <button type="button" className="secondary-button" onClick={handleLogout}>Logout</button>
          </div>
        </div>
      </header>

      <main className="max-shell dashboard-grid">
        <aside className="dashboard-sidebar">
          <div className="profile-card">
            <div className="avatar-ring">{(user?.email ?? 'N').slice(0, 1).toUpperCase()}</div>
            <h3>{user?.email ?? 'Member'}</h3>
            <p>{user?.role ?? 'Citizen'}</p>
          </div>

          <div className="sidebar-card">
            <span className="muted-label">Summary</span>
            <ul>
              <li>Verified legal guidance</li>
              <li>Document analysis</li>
              <li>Next-step recommendations</li>
            </ul>
          </div>

          <div className="sidebar-card quick-actions">
            <span className="muted-label">Quick actions</span>
            <Link to="/upload" className="mini-action">Upload document</Link>
            <Link to="/services" className="mini-action">Explore services</Link>
            <Link to="/case-studies" className="mini-action">Review case studies</Link>
          </div>
        </aside>

        <section className="dashboard-main">
          <div className="welcome-card">
            <div>
              <span className="eyebrow">DASHBOARD</span>
              <h1>Legal guidance, organised.</h1>
            </div>
            <Link to="/" className="ghost-link">Back to landing</Link>
          </div>

          <div className="stats-grid compact">
            <div className="metric-card dashboard-stat neutral">
              <strong>Live</strong>
              <span>Workspace active</span>
            </div>
            <div className="metric-card dashboard-stat neutral">
              <strong>Ready</strong>
              <span>Awaiting your details</span>
            </div>
            <div className="metric-card dashboard-stat neutral">
              <strong>Guidance</strong>
              <span>Personalised as you use the app</span>
            </div>
          </div>

          <div className="widget-grid">
            <div className="info-card">
              <div className="info-card-head">
                <span className="chip">Workspace</span>
                <h3>What happens here</h3>
              </div>
              <ul className="timeline">
                <li><strong>Upload</strong><span>Share one document or fact pattern for review.</span></li>
                <li><strong>Ask</strong><span>Describe your issue to receive legal guidance.</span></li>
                <li><strong>Review</strong><span>Use the next-step recommendations as your case evolves.</span></li>
              </ul>
            </div>

            <div className="info-card">
              <div className="info-card-head">
                <span className="chip">Steps</span>
                <h3>Next actions</h3>
              </div>
              <ul className="checklist">
                <li>Complete your profile</li>
                <li>Upload a relevant document</li>
                <li>Ask a question to begin the review</li>
              </ul>
            </div>
          </div>

          <div className="chat-panel">
            <div className="chat-header">
              <h3>Ask Nyaya Setu</h3>
              <span className="live-pill">Online</span>
            </div>

            <div className="chat-feed">
              {chatMessages.map((item, idx) => (
                <div key={`${item.role}-${idx}`} className={`chat-bubble ${item.role}`}>
                  {item.content}
                </div>
              ))}
              {error && <div className="error-banner">{error}</div>}
            </div>

            <form className="chat-form" onSubmit={handleSubmit}>
              <input
                type="text"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Ask about your legal concern..."
                aria-label="Legal question"
              />
              <button type="submit" className="primary-button" disabled={isSending}>
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}
