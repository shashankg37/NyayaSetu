import { useState, useRef, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type MessageItem = {
  role: 'user' | 'assistant';
  content: string;
  structuredReply?: Record<string, unknown>;
  audioUrl?: string;
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

  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!message.trim() || !token) return;

    const input = message.trim();
    setError('');
    setMessage('');
    setIsSending(true);

    // Show user message instantly
    setChatMessages((prev) => [...prev, { role: 'user', content: input }]);

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
        { role: 'assistant', content: fallbackText, structuredReply: response.reply },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to Nyaya Setu. Make sure the backend is running.');
    } finally {
      setIsSending(false);
    }
  };

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = { mimeType: 'audio/webm;codecs=opus' };
      const recorder = new MediaRecorder(stream, MediaRecorder.isTypeSupported(options.mimeType) ? options : undefined);
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      
      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        audioChunksRef.current = [];
        await submitVoice(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      setError('');
    } catch {
      setError('Microphone permission denied or unsupported.');
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const submitVoice = async (audioBlob: Blob) => {
    if (!token) return;
    setIsSending(true);
    setError('');
    
    try {
      const response = await api.voiceChat(token, audioBlob, conversationId);
      setConversationId(response.conversation_id);
      
      let audioUrl: string | undefined;
      if (response.reply_audio_b64) {
        const byteCharacters = atob(response.reply_audio_b64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'audio/mpeg' });
        audioUrl = URL.createObjectURL(blob);
        
        const audio = new Audio(audioUrl);
        audio.play().catch(e => console.log('Autoplay prevented', e));
      }

      setChatMessages(prev => [
        ...prev,
        { role: 'user', content: response.transcript || '(Voice message)' },
        { role: 'assistant', content: response.reply_text, audioUrl }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to process voice.');
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


          <div className="chat-panel">
            <div className="chat-header">
              <h3>Ask Nyaya Setu</h3>
              <span className="live-pill">Online</span>
            </div>

            <div className="chat-feed">
              {chatMessages.map((item, idx) => (
                <div key={`${item.role}-${idx}`} className={`chat-bubble ${item.role}`}>
                  {item.structuredReply ? (
                    <div style={{ display: 'grid', gap: '12px' }}>
                      {Boolean(item.structuredReply.your_right) && (
                        <div>
                          <strong style={{ color: 'var(--accent-brown)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Your Right</strong>
                          <p style={{ margin: '4px 0 0', color: 'inherit' }}>{String(item.structuredReply.your_right)}</p>
                        </div>
                      )}
                      {Boolean(item.structuredReply.summary) && (
                        <div>
                          <strong style={{ color: 'var(--accent-brown)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Summary</strong>
                          <p style={{ margin: '4px 0 0', color: 'inherit' }}>{String(item.structuredReply.summary)}</p>
                        </div>
                      )}
                      {Boolean(item.structuredReply.explanation) && (
                        <div>
                          <strong style={{ color: 'var(--accent-brown)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Explanation</strong>
                          <p style={{ margin: '4px 0 0', color: 'inherit' }}>{String(item.structuredReply.explanation)}</p>
                        </div>
                      )}
                      {Boolean(item.structuredReply.next_action) && (
                        <div>
                          <strong style={{ color: 'var(--accent-brown)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Next Action</strong>
                          <p style={{ margin: '4px 0 0', color: 'inherit' }}>{String(item.structuredReply.next_action)}</p>
                        </div>
                      )}
                      {Boolean(item.structuredReply.evidence_status) && (
                        <div>
                          <strong style={{ color: 'var(--accent-brown)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Evidence</strong>
                          <p style={{ margin: '4px 0 0', color: 'inherit' }}>{String(item.structuredReply.evidence_status)}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    item.content
                  )}
                  {item.audioUrl && (
                    <div style={{ marginTop: '12px' }}>
                      <audio controls src={item.audioUrl} style={{ width: '100%', maxHeight: '36px', outline: 'none' }} />
                    </div>
                  )}
                </div>
              ))}
              {error && <div className="error-banner">{error}</div>}
              {isSending && <div className="chat-bubble assistant" style={{ fontStyle: 'italic', opacity: 0.7 }}>Processing...</div>}
            </div>

            <form className="chat-form" onSubmit={handleSubmit}>
              <button 
                type="button" 
                className="secondary-button" 
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                disabled={isSending && !isRecording}
                style={{ padding: '0 1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '12px', background: isRecording ? 'rgba(194, 84, 84, 0.1)' : 'transparent', borderColor: isRecording ? '#c25454' : 'rgba(61, 41, 29, 0.7)' }}
                aria-label={isRecording ? "Stop recording" : "Start recording"}
                title={isRecording ? "Stop recording" : "Start recording"}
              >
                {isRecording ? '⏹' : '🎙'}
              </button>
              <input
                type="text"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder={isRecording ? "Listening..." : "Ask about your legal concern..."}
                aria-label="Legal question"
                disabled={isRecording || isSending}
              />
              <button type="submit" className="primary-button" disabled={isSending || isRecording || !message.trim()} style={{ borderRadius: '12px' }}>
                Send
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}
