import { Link } from 'react-router-dom';

const heroImage = '/images/hero-statue-transparent.png';
const heroAlt = 'Nyaya Setu — Lady Justice statue';

const services = [
	{
		icon: '⚖️',
		title: 'Legal Awareness',
		description:
			'Understand your rights with simplified legal guidance grounded in official legal sources.',
	},
	{
		icon: '📄',
		title: 'Document Review',
		description:
			'Upload documents and extract key issues, obligations, and next steps with clarity.',
	},
	{
		icon: '🎧',
		title: 'Voice Assistance',
		description:
			'Ask in your preferred language through a multilingual, human-centred experience.',
	},
	{
		icon: '✍️',
		title: 'Drafting Support',
		description:
			'Create compliant notices, applications, and legal drafts with guided structure.',
	},
];

const values = [
	'Verified legal information from authoritative sources',
	'Plain-language explanations for complex legal questions',
	'AI-enabled drafting support for public-facing legal action',
	'Secure and confidential case handling',
];

const benefits = [
	{ title: 'Immediate Clarity', text: 'Get precise legal answers quickly and confidently.' },
	{ title: 'Structured Guidance', text: 'Progress from issue identification to informed action.' },
	{ title: 'Accessibility', text: 'Support across languages, documents, and voice interactions.' },
	{ title: 'Trust & Safety', text: 'Built around legal awareness, evidence, and professional escalation.' },
];

const handleBrokenImage = (event: React.SyntheticEvent<HTMLImageElement>) => {
	const target = event.currentTarget;
	target.style.display = 'none';
	const parent = target.parentElement;
	if (parent) {
		parent.classList.add('image-fallback');
	}
};

export default function LandingPage() {
	return (
		<div className="luxury-shell">
			<header className="topbar">
				<div className="max-shell nav-bar">
					<Link to="/" className="brand-mark">
						<span className="brand-icon">NS</span>
						<span className="brand-word">Nyaya Setu</span>
					</Link>

					<nav className="nav-links" aria-label="Main navigation">
						<a href="#home">Home</a>
						<a href="#about">About</a>
						<a href="#services">Services</a>
						<a href="#case-studies">Case Studies</a>
						<a href="#contact">Contact</a>
					</nav>

					<div className="nav-actions">
						<Link to="/login" className="ghost-link">Login</Link>
						<Link to="/signup" className="primary-button small">Get Started</Link>
					</div>
				</div>
			</header>

			<main id="home" className="landing-main">
				<section className="hero-panel">
					<div className="watermark-hero">JUSTICE</div>
					<div className="max-shell hero-grid">
						<div className="hero-copy">
							<span className="eyebrow">LEGAL EXCELLENCE</span>
							<h1>HIGH QUALITY LEGAL CONSULTANCY</h1>
							<p>
								Nyaya Setu makes legal help clear, accessible, and trustworthy—bringing
								authoritative guidance to everyday citizens with confidence.
							</p>

							<div className="cta-row">
								<Link to="/signup" className="primary-button">Start Your Journey</Link>
								<Link to="/login" className="secondary-button">Learn More</Link>
							</div>
						</div>

						<div className="hero-visual-wrap">
							<div className="hero-visual-card">
								<img
									src={heroImage}
									alt={heroAlt}
									onError={handleBrokenImage}
								/>
							</div>
						</div>
					</div>
				</section>

				<section id="services" className="content-section">
					<div className="max-shell">
						<div className="section-header">
							<span className="section-kicker">OUR CORE FOCUS</span>
							<h2>THE AREAS WHERE WE EXCEL</h2>
						</div>

						<div className="service-grid">
							{services.map((service) => (
								<article key={service.title} className="service-card">
									<div className="service-icon">{service.icon}</div>
									<h3>{service.title}</h3>
									<p>{service.description}</p>
								</article>
							))}
						</div>
					</div>
				</section>

				<section id="about" className="spotlight-section">
					<div className="max-shell spotlight-grid">
						<div className="spotlight-image-shell">
							<img
								src={heroImage}
								alt={heroAlt}
								onError={handleBrokenImage}
							/>
						</div>

						<div className="spotlight-copy">
							<span className="section-kicker">WHY CLIENTS CHOOSE US</span>
							<h2>TRUSTED, REFINED, AND BUILT FOR REAL-WORLD DECISIONS</h2>

							<div className="value-list">
								{values.map((item) => (
									<div key={item} className="value-row">
										<span className="checkmark">✓</span>
										<p>{item}</p>
									</div>
								))}
							</div>

							<Link to="/dashboard" className="primary-button">Explore Our Platform</Link>
						</div>
					</div>
				</section>

				<section className="dark-band" id="case-studies">
					<div className="max-shell dark-grid">
						<div>
							<span className="section-kicker light">WHAT YOU GAIN</span>
							<h2>WHAT BENEFITS WILL YOU GET FROM US?</h2>
						</div>

						<div className="benefit-list">
							{benefits.map((benefit) => (
								<div key={benefit.title} className="benefit-row">
									<h3>{benefit.title}</h3>
									<p>{benefit.text}</p>
								</div>
							))}
						</div>
					</div>
				</section>
			</main>

			<footer id="contact" className="footer-cta">
				<div className="max-shell footer-inner">
					<span className="section-kicker">LET'S TALK</span>
					<h2>LET'S TALK</h2>
					<p>
						Ready to get clear legal direction with a trusted partner by your side?
					</p>
					<div className="footer-actions">
						<a
							href="mailto:contact@nyayasetu.com"
							className="primary-button"
						>
							contact@nyayasetu.com
						</a>
						<Link to="/login" className="secondary-button">
							Schedule A Consultation
						</Link>
					</div>

					<div className="footer-nav">
						<a href="#home">Home</a>
						<a href="#about">About</a>
						<a href="#services">Services</a>
						<a href="#contact">Contact</a>
					</div>
				</div>
			</footer>
		</div>
	);
}
