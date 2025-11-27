import React, { useState, useEffect } from 'react';
import { getGoogleAuthUrl, handleOAuthCallback, syncGmail } from '../services/api';

const GmailConnect: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
      handleCallback(code);
    }
  }, []);

  const handleCallback = async (code: string) => {
    try {
      await handleOAuthCallback(code);
      setConnected(true);
      setMessage('Successfully connected to Gmail!');

      // Clear the code from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error: any) {
      setMessage(`Connection failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleConnect = async () => {
    try {
      const authUrl = await getGoogleAuthUrl();
      window.location.href = authUrl;
    } catch (error: any) {
      setMessage(`Failed to initiate OAuth: ${error.message}`);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setMessage('');

    try {
      const result = await syncGmail();
      setMessage(`Synced ${result.new_emails} new emails (${result.total_fetched} fetched)`);
    } catch (error: any) {
      setMessage(`Sync failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="gmail-connect">
      <h1>Gmail Connection</h1>

      {!connected ? (
        <div className="connect-box">
          <p>Connect your Gmail account to automatically sync emails and attachments.</p>
          <button onClick={handleConnect} className="connect-button">
            Connect Gmail
          </button>
        </div>
      ) : (
        <div className="sync-box">
          <p className="success">Gmail is connected!</p>
          <button onClick={handleSync} disabled={syncing}>
            {syncing ? 'Syncing...' : 'Sync Emails'}
          </button>
        </div>
      )}

      {message && (
        <div className={`message ${message.includes('failed') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="info">
        <h3>What will be synced?</h3>
        <ul>
          <li>Last 3 months of emails</li>
          <li>Email subject, sender, receiver, timestamp</li>
          <li>Email body text (plain text only)</li>
          <li>PDF attachments only</li>
        </ul>
      </div>
    </div>
  );
};

export default GmailConnect;
