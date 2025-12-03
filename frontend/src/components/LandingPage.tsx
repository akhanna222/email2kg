import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            📧 Email2KG
            <span className="gradient-text"> Knowledge Graph Platform</span>
          </h1>
          <p className="hero-subtitle">
            Transform your emails and documents into actionable intelligence with AI-powered knowledge graphs
          </p>
          <div className="hero-buttons">
            <button
              className="cta-primary"
              onClick={() => navigate('/register')}
            >
              Get Started Free
            </button>
            <button
              className="cta-secondary"
              onClick={() => navigate('/login')}
            >
              Sign In
            </button>
          </div>
        </div>
      </section>

      {/* What It Does Section */}
      <section className="features-section">
        <div className="container">
          <h2 className="section-title">What Does Email2KG Do?</h2>
          <p className="section-subtitle">
            Automatically extract, analyze, and connect information from your documents into an intelligent knowledge graph
          </p>

          <div className="features-grid">
            {/* Feature 1 */}
            <div className="feature-card">
              <div className="feature-icon">📨</div>
              <h3>Connect Your Email</h3>
              <p>
                Seamlessly integrate Gmail, Outlook, or any IMAP email provider.
                Your invoices, receipts, and documents are automatically synced.
              </p>
              <ul className="feature-list">
                <li>✓ Gmail & Outlook OAuth</li>
                <li>✓ Automatic syncing</li>
                <li>✓ Secure access</li>
              </ul>
            </div>

            {/* Feature 2 */}
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI Extracts Everything</h3>
              <p>
                GPT-4 Vision reads your documents with 98-99% accuracy.
                Extracts vendors, amounts, dates, line items - everything automatically.
              </p>
              <ul className="feature-list">
                <li>✓ Invoices & receipts</li>
                <li>✓ Contracts & tickets</li>
                <li>✓ Any document type</li>
              </ul>
            </div>

            {/* Feature 3 */}
            <div className="feature-card">
              <div className="feature-icon">🕸️</div>
              <h3>Build Knowledge Graph</h3>
              <p>
                Automatically connects documents → transactions → parties.
                Discover hidden patterns and relationships in your data.
              </p>
              <ul className="feature-list">
                <li>✓ Auto relationships</li>
                <li>✓ Visual exploration</li>
                <li>✓ Smart queries</li>
              </ul>
            </div>

            {/* Feature 4 */}
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Get Insights</h3>
              <p>
                Search, filter, and analyze your data. Track spending,
                monitor vendors, and never miss important information.
              </p>
              <ul className="feature-list">
                <li>✓ Advanced analytics</li>
                <li>✓ Full-text search</li>
                <li>✓ Custom filters</li>
              </ul>
            </div>

            {/* Feature 5 */}
            <div className="feature-card">
              <div className="feature-icon">💬</div>
              <h3>Human-in-the-Loop</h3>
              <p>
                Review and correct extractions with one click.
                The system learns from your feedback and improves over time.
              </p>
              <ul className="feature-list">
                <li>✓ Easy corrections</li>
                <li>✓ Confidence scores</li>
                <li>✓ Continuous learning</li>
              </ul>
            </div>

            {/* Feature 6 */}
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Secure & Private</h3>
              <p>
                Enterprise-grade security with JWT authentication, encrypted storage,
                and complete data privacy.
              </p>
              <ul className="feature-list">
                <li>✓ End-to-end encryption</li>
                <li>✓ Multi-tenant isolation</li>
                <li>✓ Your data stays yours</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          <div className="steps-grid">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Connect</h3>
              <p>Link your Gmail or upload documents directly</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">2</div>
              <h3>Extract</h3>
              <p>AI automatically reads and extracts data</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">3</div>
              <h3>Connect</h3>
              <p>Knowledge graph builds relationships</p>
            </div>
            <div className="step-arrow">→</div>
            <div className="step">
              <div className="step-number">4</div>
              <h3>Analyze</h3>
              <p>Search, filter, and get insights</p>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="use-cases">
        <div className="container">
          <h2 className="section-title">Perfect For</h2>
          <div className="use-cases-grid">
            <div className="use-case">
              <h3>💼 Businesses</h3>
              <p>Track expenses, manage vendors, organize receipts</p>
            </div>
            <div className="use-case">
              <h3>🏠 Freelancers</h3>
              <p>Invoice tracking, client management, tax prep</p>
            </div>
            <div className="use-case">
              <h3>📚 Individuals</h3>
              <p>Personal finance, travel receipts, warranties</p>
            </div>
            <div className="use-case">
              <h3>🏢 Teams</h3>
              <p>Shared knowledge base, approval workflows</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <h2>Ready to Transform Your Documents?</h2>
          <p>Start building your intelligent knowledge graph today</p>
          <button
            className="cta-primary large"
            onClick={() => navigate('/register')}
          >
            Get Started Free
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <p>© 2024 Email2KG - AI-Powered Document Intelligence Platform</p>
          <div className="footer-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#docs">Documentation</a>
            <a href="#contact">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
