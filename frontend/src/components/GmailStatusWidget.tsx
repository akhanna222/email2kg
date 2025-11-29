/**
 * Gmail Connection Status Widget
 * Shows connection status and provides quick connect/sync actions
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGoogleAuthUrl, syncGmail } from '../services/api';
import './GmailStatusWidget.css';

interface GmailStatusWidgetProps {
  compact?: boolean;
}

const GmailStatusWidget: React.FC<GmailStatusWidgetProps> = ({ compact = false }) => {
  const navigate = useNavigate();
  const [connected, setConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      // Try to get status from localStorage or API
      const status = localStorage.getItem('gmail_connected');
      const lastSyncTime = localStorage.getItem('gmail_last_sync');

      setConnected(status === 'true');
      setLastSync(lastSyncTime);
    } catch (err) {
      console.error('Failed to check Gmail status:', err);
    }
  };

  const handleConnect = async () => {
    try {
      setError(null);
      const authUrl = await getGoogleAuthUrl();
      // Store return path
      localStorage.setItem('gmail_return_path', window.location.pathname);
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
      const result = await syncGmail();
      const now = new Date().toISOString();
      setLastSync(now);
      localStorage.setItem('gmail_last_sync', now);

      // Show success message briefly
      setTimeout(() => {
        checkConnectionStatus();
      }, 2000);
    } catch (err: any) {
      setError('Sync failed. Please try again.');
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  const handleViewDetails = () => {
    navigate('/gmail');
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

              <button onClick={handleViewDetails} className="btn btn-secondary">
                View Details
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

              <button onClick={handleViewDetails} className="btn btn-link">
                Learn More
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
