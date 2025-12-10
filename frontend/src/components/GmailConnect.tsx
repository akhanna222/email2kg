import React, { useState, useEffect } from 'react';
import { getGoogleAuthUrl, syncGmail } from '../services/api';

const GmailConnect: React.FC = () => {
  const [connected, setConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Check for OAuth callback result
    const urlParams = new URLSearchParams(window.location.search);
    const gmailConnected = urlParams.get('gmail_connected');
    const gmailError = urlParams.get('gmail_error');

    if (gmailConnected === 'true') {
      setConnected(true);
      setMessage('Successfully connected to Gmail!');
      // Clear the query params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (gmailError) {
      const errorMessages: Record<string, string> = {
        'access_denied': 'You denied access to Gmail. Please try again and approve the permissions.',
        'no_code': 'No authorization code received from Google.',
        'no_user_id': 'User session not found. Please log in again.',
        'user_not_found': 'User account not found. Please log in again.',
        'invalid_state': 'Invalid OAuth state. Please try again.',
      };
      const displayError = errorMessages[gmailError] || `Connection failed: ${gmailError}`;
      setMessage(displayError);
      // Clear the query params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

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
          <li>ALL emails from last 3 months (no limits)</li>
          <li>Email subject, sender, receiver, timestamp</li>
          <li>Email body text (used for smart classification)</li>
          <li>PDF and image attachments (JPG, PNG, TIFF, etc.)</li>
          <li>OCR text extraction from all attachments</li>
          <li>Smart document classification using email context</li>
        </ul>
        <h3>How does classification work?</h3>
        <ol>
          <li>Email subject is analyzed for keywords (invoice, receipt, etc.)</li>
          <li>Email body is checked for additional context</li>
          <li>OCR extracts text from PDF/image attachments</li>
          <li>AI classifies into: invoice, receipt, statement, contract, etc.</li>
        </ol>
      </div>
    </div>
  );
};

export default GmailConnect;
