import './AskNyayaPage.css';
import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, type ChatReply } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type Message = {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  reply?: ChatReply;
  nextAction?: string | null;
  evidenceStatus?: string | null;
  timestamp: string;
};

/** Render a string or string[] as a bullet list or paragraph */
function RenderTextOrList({ value }: { value: string | string[] | undefined }) {
  if (!value) return null;
  if (Array.isArray(value)) {
    return (
      <ul style={{ margin: '0.5rem 0', paddingLeft: '1.25rem' }}>
        {value.map((item, i) => <li key={i}>{item}</li>)}
      </ul>
    );
  }
  return <div className="ai-section-text">{value}</div>;
}

function AIResponseCard({ reply, evidenceStatus }: { reply: ChatReply; evidenceStatus?: string | null }) {
  const sections: { label: string; content: React.ReactNode }[] = [];

  // Your Right (always first)
  if (reply.your_right) {
    sections.push({ label: 'Your Right', content: <div className="ai-section-text">{reply.your_right}</div> });
  }

  // What the Law Says
  if (reply.what_law_says) {
    sections.push({ label: 'What the Law Says', content: <RenderTextOrList value={reply.what_law_says} /> });
  }

  // What This Means
  if (reply.what_this_means) {
    sections.push({ label: 'What This Means', content: <div className="ai-section-text">{reply.what_this_means}</div> });
  }

  // AI Interpretation (document analysis)
  if (reply.ai_interpretation) {
    sections.push({ label: 'AI Interpretation', content: <div className="ai-section-text">{reply.ai_interpretation}</div> });
  }

  // What You Can Do
  if (reply.what_you_can_do) {
    sections.push({ label: 'What You Can Do', content: <RenderTextOrList value={reply.what_you_can_do} /> });
  }

  // Remedy
  if (reply.remedy) {
    sections.push({ label: 'Remedy', content: <div className="ai-section-text">{reply.remedy}</div> });
  }

  // Next Step
  if (reply.next_step) {
    sections.push({ label: 'Next Step', content: <div className="ai-section-text">{reply.next_step}</div> });
  }

  // Draft Text (drafting flow)
  if (reply.draft_text) {
    sections.push({
      label: 'Generated Draft',
      content: (
        <div>
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.9rem', background: 'rgba(0,0,0,0.03)', padding: '1rem', borderRadius: '6px', maxHeight: '300px', overflowY: 'auto' }}>
            {reply.draft_text}
          </pre>
          {(reply.pdf_path || reply.docx_path) && (
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
              {reply.pdf_path && <a href={`http://127.0.0.1:8000/${reply.pdf_path}`} target="_blank" rel="noreferrer" className="ai-chip">📄 Download PDF</a>}
              {reply.docx_path && <a href={`http://127.0.0.1:8000/${reply.docx_path}`} target="_blank" rel="noreferrer" className="ai-chip">📝 Download DOCX</a>}
            </div>
          )}
        </div>
      ),
    });
  }

  // Document extraction fields
  if (reply.user_document_extraction) {
    sections.push({
      label: 'Extracted from Your Document',
      content: (
        <div style={{ fontSize: '0.9rem' }}>
          {Object.entries(reply.user_document_extraction).map(([key, val]) => (
            <div key={key} style={{ marginBottom: '0.25rem' }}>
              <strong>{key.replace(/_/g, ' ')}:</strong> {String(val)}
            </div>
          ))}
        </div>
      ),
    });
  }

  // Lawyer Matches
  if (reply.matches && reply.matches.length > 0) {
    sections.push({
      label: 'Matched Lawyers',
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {reply.matches.map((lawyer, i) => {
            const name = String(lawyer.name || 'Lawyer');
            const spec = lawyer.specialization ? String(lawyer.specialization) : '';
            const loc = lawyer.location ? String(lawyer.location) : '';
            const phone = lawyer.phone ? String(lawyer.phone) : '';
            return (
            <div key={i} style={{ background: 'rgba(0,0,0,0.03)', padding: '0.75rem', borderRadius: '6px' }}>
              <strong>{name}</strong>
              {spec && <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>({spec})</span>}
              {loc && <div style={{ fontSize: '0.85rem' }}>📍 {loc}</div>}
              {phone && <div style={{ fontSize: '0.85rem' }}>📞 {phone}</div>}
            </div>
            );
          })}
        </div>
      ),
    });
  }

  // Citations
  if (reply.citations && reply.citations.length > 0) {
    sections.push({
      label: 'Citations',
      content: (
        <div className="ai-citation">
          <svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          {reply.citations.join(' | ')}
        </div>
      ),
    });
  }

  // Disclaimer
  if (reply.disclaimer) {
    sections.push({
      label: '',
      content: <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: 'var(--text-secondary)' }}>⚖️ {reply.disclaimer}</div>,
    });
  }

  // Evidence status badge
  const showBadge = evidenceStatus && evidenceStatus !== 'unknown';

  return (
    <div className="ai-card">
      {showBadge && (
        <div style={{
          display: 'inline-block',
          fontSize: '0.7rem',
          padding: '0.2rem 0.5rem',
          borderRadius: '4px',
          marginBottom: '0.75rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          background: evidenceStatus === 'sufficient' ? 'rgba(34,139,34,0.1)' : evidenceStatus === 'no_evidence' ? 'rgba(220,20,60,0.1)' : 'rgba(218,165,32,0.1)',
          color: evidenceStatus === 'sufficient' ? '#228B22' : evidenceStatus === 'no_evidence' ? '#DC143C' : '#B8860B',
        }}>
          {evidenceStatus === 'sufficient' ? '✓ Grounded in law' : evidenceStatus === 'no_evidence' ? '✗ No evidence found' : `⚠ ${evidenceStatus}`}
        </div>
      )}

      {sections.length === 0 && <div className="ai-section"><div className="ai-section-text">I have processed your request.</div></div>}

      {sections.map((section, i) => (
        <div className="ai-section" key={i}>
          {section.label && <div className="ai-section-label">{section.label}</div>}
          {section.content}
        </div>
      ))}

      {reply.fallback_used && (
        <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', padding: '0.4rem 0.6rem', background: 'rgba(218,165,32,0.08)', borderRadius: '4px', color: 'var(--text-secondary)' }}>
          ℹ️ This response used general knowledge. For case-specific guidance, consult a licensed advocate.
        </div>
      )}
    </div>
  );
}

export default function AskNyayaPage() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const chatEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    useEffect(() => {
        if (!token) {
            navigate('/login');
        }
    }, [token, navigate]);

    const formatTime = () => {
        const now = new Date();
        let h = now.getHours();
        const m = now.getMinutes();
        const ampm = h >= 12 ? 'PM' : 'AM';
        h = h % 12 || 12;
        return `Today, ${h}:${m < 10 ? '0' : ''}${m} ${ampm}`;
    };

    const handleSend = async (text: string) => {
        if (!text.trim() || !token) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            sender: 'user',
            text,
            timestamp: formatTime()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsLoading(true);

        try {
            const res = await api.askQuestion(token, text, conversationId);
            setConversationId(res.conversation_id);
            
            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                sender: 'ai',
                text: res.reply.your_right || res.reply.summary || 'I have processed your request.',
                reply: res.reply,
                nextAction: res.next_action,
                evidenceStatus: res.evidence_status,
                timestamp: formatTime()
            };
            setMessages(prev => [...prev, aiMsg]);
        } catch (error: any) {
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                sender: 'ai',
                text: error?.message || 'Sorry, I encountered an error processing your request.',
                timestamp: formatTime()
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="theme-ask-nyaya">
            <div className="page">
            <nav className="nav">
                <div className="nav-left">
                    <div className="ns-badge">NS</div>
                    <span className="ns-wordmark">Nyaya Setu</span>
                </div>
                <div className="nav-center">
                    <Link className="nav-link" to="/">Home</Link>
                    <Link className="nav-link active" to="/ask-nyaya">Ask Nyaya</Link>
                    <Link className="nav-link" to="/know-your-rights">Know Your Rights</Link>
                </div>
            </nav>

            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-title">Conversations</div>
                    <button className="btn-new-chat" onClick={() => { setMessages([]); setConversationId(null); }}>
                        <svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        New Chat
                    </button>
                </div>
                <div className="sidebar-list">
                    <div className="conv-group-label">Recent</div>
                    {conversationId && <div className="conv-item active">Current Conversation</div>}
                </div>
            </aside>

            <div className="chat-main">
                {messages.length === 0 ? (
                    <div className="welcome">
                        <div className="welcome-watermark">JUSTICE</div>
                        <div className="welcome-eyebrow">AI Legal Assistant</div>
                        <h1>How can I help you<br />today?</h1>
                        <p>Ask any legal question in English or Hindi. I'll ground my answer in actual Indian law and show you exactly what you can do.</p>
                        <div className="suggestions">
                            <div className="suggestion-card" onClick={() => handleSend("What are my rights as a tenant in India?")}>
                                <div className="suggestion-icon">
                                    <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                                </div>
                                <div className="suggestion-title">Tenant Rights</div>
                                <div className="suggestion-desc">What protections do I have as a renter?</div>
                            </div>
                            <div className="suggestion-card" onClick={() => handleSend("How do I file a consumer complaint in India?")}>
                                <div className="suggestion-icon">
                                    <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                                </div>
                                <div className="suggestion-title">Consumer Complaint</div>
                                <div className="suggestion-desc">Steps to file a complaint against a company</div>
                            </div>
                            <div className="suggestion-card" onClick={() => handleSend("What is the minimum wage for workers in my state?")}>
                                <div className="suggestion-icon">
                                    <svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                                </div>
                                <div className="suggestion-title">Worker Wages</div>
                                <div className="suggestion-desc">What am I legally entitled to earn?</div>
                            </div>
                            <div className="suggestion-card" onClick={() => handleSend("Can I get free legal aid?")}>
                                <div className="suggestion-icon">
                                    <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                                </div>
                                <div className="suggestion-title">Free Legal Aid</div>
                                <div className="suggestion-desc">Access government legal services</div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="chat-area visible">
                        <div className="chat-inner">
                            {messages.map(msg => (
                                msg.sender === 'user' ? (
                                    <div className="msg-row-user" key={msg.id}>
                                        <div>
                                            <div className="msg-user">{msg.text}</div>
                                            <div className="msg-time">{msg.timestamp}</div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="msg-row-ai" key={msg.id}>
                                        <div className="ai-avatar">
                                            <div className="ai-avatar-badge"><span>NS</span></div>
                                            <div className="ai-body">
                                                {msg.reply ? (
                                                    <AIResponseCard reply={msg.reply} evidenceStatus={msg.evidenceStatus} />
                                                ) : (
                                                    <div className="ai-card">
                                                        <div className="ai-section">
                                                            <div className="ai-section-text">{msg.text}</div>
                                                        </div>
                                                    </div>
                                                )}
                                                <div className="msg-time">{msg.timestamp}</div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            ))}
                            {isLoading && (
                                <div className="typing-row visible">
                                    <div className="ai-avatar">
                                        <div className="ai-avatar-badge"><span>NS</span></div>
                                        <div className="ai-body">
                                            <div className="typing-dots"><span></span><span></span><span></span></div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>
                    </div>
                )}
            </div>

            <div className="input-area">
                <div className="input-wrap">
                    <div className="input-bar">
                        <textarea 
                            className="input-field" 
                            placeholder="Ask a legal question..." 
                            rows={1}
                            value={inputValue}
                            onChange={e => setInputValue(e.target.value)}
                            onKeyDown={e => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend(inputValue);
                                }
                            }}
                        />
                        <div className="input-actions">
                            <button className={`send-btn ${!inputValue.trim() ? 'disabled' : ''}`} onClick={() => handleSend(inputValue)}>
                                <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                            </button>
                        </div>
                    </div>
                    <div className="input-hint">Nyaya Setu provides legal information, not legal advice. For case-specific guidance, consult a licensed advocate.</div>
                </div>
            </div>
        </div>
        </div>
    );
}
