import { useState, type ChangeEvent, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';

const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.webp'];

export default function UploadPage() {
  const { token } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState('No file selected');
  const [language, setLanguage] = useState('en');
  const [issueType, setIssueType] = useState('general');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [pending, setPending] = useState(false);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      setFileName('No file selected');
      return;
    }

    const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setSelectedFile(null);
      setFileName('No file selected');
      setError('Please upload a PDF, JPG, JPEG, PNG, or WEBP file.');
      return;
    }

    setSelectedFile(file);
    setFileName(file.name);
    setError('');
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!selectedFile) {
      setError('Please choose a document to continue.');
      setSubmitted(false);
      return;
    }

    if (!notes.trim()) {
      setError('Please add a short description of your legal issue.');
      setSubmitted(false);
      return;
    }

    if (!token) {
      setError('Please sign in before uploading a document.');
      setSubmitted(false);
      return;
    }

    try {
      setPending(true);
      setError('');
      await api.uploadDocument(token, selectedFile);
      setSubmitted(true);
    } catch (uploadError) {
      setSubmitted(false);
      setError(uploadError instanceof Error ? uploadError.message : 'Document upload failed.');
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="page-shell">
      <header className="page-topbar">
        <div className="max-shell nav-bar">
          <Link to="/" className="brand-mark">
            <span className="brand-icon">NS</span>
            <span className="brand-word">Nyaya Setu</span>
          </Link>

          <nav className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/services">Services</Link>
            <Link to="/case-studies">Case Studies</Link>
            <Link to="/upload">Upload</Link>
            <Link to="/dashboard">Dashboard</Link>
          </nav>
        </div>
      </header>

      <main className="max-shell page-body upload-body">
        <section className="page-hero compact">
          <span className="eyebrow">DOCUMENT UPLOAD</span>
          <h1>Share your document and get a structured review.</h1>
        </section>

        <form className="upload-form info-card" onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="document">Upload document</label>
            <input id="document" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,image/png,application/pdf,image/jpeg,image/webp" onChange={handleFileChange} />
            <small>{fileName}</small>
          </div>

          <div className="field-row">
            <div className="field-group">
              <label htmlFor="language">Language</label>
              <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="kn">Kannada</option>
                <option value="ta">Tamil</option>
              </select>
            </div>

            <div className="field-group">
              <label htmlFor="issueType">Issue type</label>
              <select id="issueType" value={issueType} onChange={(e) => setIssueType(e.target.value)}>
                <option value="general">General legal query</option>
                <option value="employment">Employment</option>
                <option value="property">Property</option>
                <option value="family">Family</option>
                <option value="consumer">Consumer</option>
              </select>
            </div>
          </div>

          <div className="field-group">
            <label htmlFor="notes">Short description</label>
            <textarea
              id="notes"
              rows={5}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Explain your issue, timeline, and what you need help with..."
            />
          </div>

          {error && <div className="error-banner">{error}</div>}
          {submitted && (
            <div className="success-banner">
              Document queued successfully. Our review workflow has been started for {fileName}.
            </div>
          )}

          <button type="submit" className="primary-button" disabled={pending}>
            {pending ? 'Uploading...' : 'Submit for review'}
          </button>
        </form>
      </main>
    </div>
  );
}
