/**
 * Gmail Connection Status Widget
 * Shows connection status and provides quick connect/sync actions
 */
import React, { useState, useEffect } from 'react';
import { getGoogleAuthUrl, syncGmail, getCurrentUser, updateUserPreferences, getProcessingMetrics } from '../services/api';
import './GmailStatusWidget.css';

interface GmailStatusWidgetProps {
  compact?: boolean;
}

interface ProcessingMetrics {
  total_emails: number;
  emails_with_documents: number;
  total_documents: number;
  total_pages_processed: number;
  total_characters_processed: number;
  avg_pages_per_document: number;
  avg_characters_per_document: number;
}

const GmailStatusWidget: React.FC<GmailStatusWidgetProps> = ({ compact = false }) => {
  const [connected, setConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [emailLimit, setEmailLimit] = useState<number | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [metrics, setMetrics] = useState<ProcessingMetrics | null>(null);
  const [showMetrics, setShowMetrics] = useState(false);

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      // Fetch current user data from API
      const user = await getCurrentUser();
      setConnected(user.gmail_connected);
      setLastSync(user.last_sync);
      setEmailLimit(user.preferences?.email_sync_limit || null);

      // Fetch processing metrics if connected
      if (user.gmail_connected) {
        await loadMetrics();
      }
    } catch (err) {
      console.error('Failed to check Gmail status:', err);
    }
  };

  const loadMetrics = async () => {
    try {
      const data = await getProcessingMetrics();
      setMetrics(data.summary);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    }
  };

  const handleEmailLimitChange = async (limit: number | null) => {
    try {
      setError(null);
      await updateUserPreferences({ email_sync_limit: limit || 0 }); // 0 = unlimited
      setEmailLimit(limit);
      setShowSettings(false);
    } catch (err: any) {
      setError('Failed to update email limit');
      console.error(err);
    }
  };

  const handleConnect = async () => {
    try {
      setError(null);
      const authUrl = await getGoogleAuthUrl();
      window.location.href = authUrl;
    } catch (err: any) {
      setError('Failed to initiate Gmail connection');
      console.error(err);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setError(null);

    try {
      await syncGmail();

      // Refresh connection status and metrics after sync
      setTimeout(() => {
        checkConnectionStatus();
        loadMetrics();
      }, 2000); // Wait a bit longer for background processing to start
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sync failed. Please try again.');
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const formatLastSync = (isoString: string | null) => {
    if (!isoString) return 'Never';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  if (compact) {
    return (
      <div className="gmail-widget-compact">
        {connected ? (
          <div className="compact-connected">
            <span className="status-dot connected"></span>
            <span>Gmail Connected</span>
            <button onClick={handleSync} disabled={syncing} className="btn-link">
              {syncing ? 'Syncing...' : 'Sync'}
            </button>
          </div>
        ) : (
          <div className="compact-not-connected">
            <span className="status-dot disconnected"></span>
            <span>Gmail Not Connected</span>
            <button onClick={handleConnect} className="btn-link">
              Connect
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="gmail-status-widget">
      <div className="widget-header">
        <h3>📧 Gmail Connection</h3>
      </div>

      <div className="widget-body">
        {connected ? (
          <div className="status-connected">
            <div className="status-indicator">
              <span className="status-dot connected"></span>
              <span className="status-text">Connected</span>
            </div>

            <div className="sync-info">
              <p className="last-sync">
                Last sync: <strong>{formatLastSync(lastSync)}</strong>
              </p>
              <p className="email-limit-info" style={{ fontSize: '0.9em', color: '#666', marginTop: '0.5em' }}>
                Email limit: <strong>{emailLimit ? `${emailLimit} emails` : 'Unlimited'}</strong>
                {' '}
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#007bff',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    fontSize: '0.9em'
                  }}
                >
                  {showSettings ? 'Hide' : 'Change'}
                </button>
              </p>

              {/* Processing Metrics */}
              {metrics && (
                <div style={{ marginTop: '1em' }}>
                  <button
                    onClick={() => setShowMetrics(!showMetrics)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#007bff',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                      fontSize: '0.9em',
                      padding: 0
                    }}
                  >
                    📊 {showMetrics ? 'Hide' : 'Show'} Processing Metrics
                  </button>
                  {showMetrics && (
                    <div style={{
                      marginTop: '0.5em',
                      padding: '1em',
                      background: '#f8f9fa',
                      borderRadius: '4px',
                      fontSize: '0.85em'
                    }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5em' }}>
                        <div>
                          <strong>Total Emails:</strong> {metrics.total_emails}
                        </div>
                        <div>
                          <strong>With Documents:</strong> {metrics.emails_with_documents}
                        </div>
                        <div>
                          <strong>Total Documents:</strong> {metrics.total_documents}
                        </div>
                        <div>
                          <strong>Total Pages:</strong> {metrics.total_pages_processed.toLocaleString()}
                        </div>
                        <div style={{ gridColumn: '1 / -1' }}>
                          <strong>Total Characters:</strong> {metrics.total_characters_processed.toLocaleString()}
                        </div>
                        <div>
                          <strong>Avg Pages/Doc:</strong> {metrics.avg_pages_per_document}
                        </div>
                        <div>
                          <strong>Avg Chars/Doc:</strong> {Math.round(metrics.avg_characters_per_document).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
              {showSettings && (
                <div style={{ marginTop: '1em', padding: '1em', background: '#f8f9fa', borderRadius: '4px' }}>
                  <p style={{ marginBottom: '0.5em', fontSize: '0.9em', fontWeight: 'bold' }}>Select email sync limit:</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5em' }}>
                    {[
                      { value: null, label: 'Unlimited (all emails)' },
                      { value: 100, label: '100 emails' },
                      { value: 500, label: '500 emails' },
                      { value: 1000, label: '1,000 emails' },
                      { value: 2000, label: '2,000 emails' }
                    ].map(option => (
                      <button
                        key={option.value || 'unlimited'}
                        onClick={() => handleEmailLimitChange(option.value)}
                        style={{
                          padding: '0.5em',
                          background: emailLimit === option.value ? '#007bff' : 'white',
                          color: emailLimit === option.value ? 'white' : '#333',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          textAlign: 'left'
                        }}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="widget-actions">
              <button
                onClick={handleSync}
                disabled={syncing}
                className="btn btn-primary"
              >
                {syncing ? (
                  <>
                    <span className="spinner-small"></span>
                    Syncing...
                  </>
                ) : (
                  <>
                    🔄 Sync Now
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="status-not-connected">
            <div className="status-indicator">
              <span className="status-dot disconnected"></span>
              <span className="status-text">Not Connected</span>
            </div>

            <p className="connect-description">
              Connect your Gmail to automatically sync emails and extract data from attachments.
            </p>

            <div className="widget-actions">
              <button onClick={handleConnect} className="btn btn-primary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c5.05-.5 9-4.76 9-9.95z" fill="currentColor"/>
                </svg>
                Connect Gmail
              </button>
            </div>

            <div className="benefits">
              <p className="benefits-title">What you'll get:</p>
              <ul>
                <li>✓ Auto-sync last 3 months of emails</li>
                <li>✓ Extract data from PDF attachments</li>
                <li>✓ Build knowledge graph from emails</li>
              </ul>
            </div>
          </div>
        )}

        {error && (
          <div className="widget-error">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default GmailStatusWidget;
