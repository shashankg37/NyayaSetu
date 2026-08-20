import { Link } from 'react-router-dom';

const caseStudies = [
  {
    title: 'Employment notice review',
    outcome: 'Helped a citizen understand notice obligations and respond with a structured timeline.',
    tag: 'Employment',
  },
  {
    title: 'Property document clarification',
    outcome: 'Simplified key clauses and flagged issues for review before legal consultation.',
    tag: 'Property',
  },
  {
    title: 'Public grievance drafting',
    outcome: 'Prepared a complaint draft with issue framing and order of action for escalation.',
    tag: 'Public Rights',
  },
  {
    title: 'Family law guidance',
    outcome: 'Explained the legal process in understandable terms with next-step recommendations.',
    tag: 'Family',
  },
];

export default function CaseStudiesPage() {
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
            <Link to="/login">Login</Link>
          </nav>
        </div>
      </header>

      <main className="max-shell page-body">
        <section className="page-hero compact">
          <span className="eyebrow">CASE STUDIES</span>
          <h1>Real-world scenarios, simplified with legal clarity.</h1>
        </section>

        <section className="content-grid case-grid">
          {caseStudies.map((item) => (
            <article key={item.title} className="info-card case-card">
              <span className="chip">{item.tag}</span>
              <h2>{item.title}</h2>
              <p>{item.outcome}</p>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
