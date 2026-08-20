import { Link } from 'react-router-dom';

const serviceGroups = [
  {
    title: 'Legal Guidance',
    copy: 'Understand rights, procedures, filing paths, and next steps in clear, everyday language.',
    bullets: ['Issue triage', 'Right-to-know resources', 'Procedural guidance'],
  },
  {
    title: 'Document Review',
    copy: 'Upload notices, summons, letters, and complaint drafts to get key legal issues surfaced quickly.',
    bullets: ['Notice analysis', 'Clause review', 'Risk summaries'],
  },
  {
    title: 'Voice & Multilingual Access',
    copy: 'Speak in your preferred language and ask legal questions in a natural, frictionless format.',
    bullets: ['Hindi / English / regional support', 'Quick voice prompts', 'Accessible assistance'],
  },
  {
    title: 'Drafting Support',
    copy: 'Prepare legal notices, letters, applications, and summaries with structure and clarity.',
    bullets: ['Draft templates', 'Structured responses', 'Prepared outlines'],
  },
];

export default function ServicesPage() {
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
          <span className="eyebrow">OUR SERVICES</span>
          <h1>Legal guidance that is practical, clear, and actionable.</h1>
          <p>
            From initial legal awareness to document review and drafting support, Nyaya Setu helps citizens move from uncertainty to informed action.
          </p>
        </section>

        <section className="content-grid two-up">
          {serviceGroups.map((service) => (
            <article key={service.title} className="info-card service-card-panel">
              <div className="info-card-head">
                <span className="chip">Service</span>
                <h2>{service.title}</h2>
              </div>
              <p>{service.copy}</p>
              <ul>
                {service.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
