import { Link } from 'react-router-dom';

const heroImage = '/images/hero-statue-transparent.png';
const heroAlt = 'Nyaya Setu — Lady Justice statue';

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
						<Link to="/">Home</Link>
						<Link to="/dashboard">Ask Nyaya</Link>
						<Link to="/upload">Know Your Rights</Link>
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
							<span className="eyebrow">BRIDGE TO JUSTICE</span>
							<h1>
								Know Your Rights
								<br />
								Know Your Next Step
							</h1>
							<p>In your language. In one place.</p>

							<div className="cta-row">
								<Link to="/dashboard" className="primary-button">Ask Nyaya Setu</Link>
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

				<section className="trust-line-section">
					<div className="max-shell trust-line">
						<span>AI-Powered</span>
						<span className="trust-dot">·</span>
						<span>Multilingual</span>
						<span className="trust-dot">·</span>
						<span>For Every Citizen</span>
					</div>
				</section>
			</main>

			<footer className="footer-simple">
				<div className="max-shell footer-simple-inner">
					<Link to="/" className="brand-mark">
						<span className="brand-icon">NS</span>
						<span className="brand-word">Nyaya Setu</span>
					</Link>

					<nav className="footer-nav" aria-label="Footer navigation">
						<Link to="/">Home</Link>
						<Link to="/dashboard">Ask Nyaya</Link>
						<Link to="/upload">Know Your Rights</Link>
						<Link to="/login">Login</Link>
					</nav>
				</div>
			</footer>
		</div>
	);
}
