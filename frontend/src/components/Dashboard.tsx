import React, { useEffect, useState } from 'react';
import { getStats } from '../services/api';
import { Stats } from '../types';
import GmailStatusWidget from './GmailStatusWidget';
import EmailActivityFeed from './EmailActivityFeed';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [gmailMessage, setGmailMessage] = useState<string>('');
  const [activityRefresh, setActivityRefresh] = useState(0);

  useEffect(() => {
    loadStats();

    // Check for OAuth callback result
    const urlParams = new URLSearchParams(window.location.search);
    const gmailConnected = urlParams.get('gmail_connected');
    const gmailError = urlParams.get('gmail_error');

    if (gmailConnected === 'true') {
      setGmailMessage('Gmail successfully connected!');
      // Clear the query params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (gmailError) {
      const errorMessages: Record<string, string> = {
        'access_denied': 'Gmail connection denied. Please try again.',
        'no_code': 'No authorization code received.',
        'no_user_id': 'Session not found. Please log in again.',
        'user_not_found': 'User not found. Please log in again.',
        'invalid_state': 'Invalid session. Please try again.',
      };
      setGmailMessage(errorMessages[gmailError] || `Error: ${gmailError}`);
      // Clear the query params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading dashboard...
      </div>
    );
  }

  const handleSyncComplete = () => {
    // Refresh activity feed when sync completes
    setActivityRefresh(prev => prev + 1);
    loadStats();
  };

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      {gmailMessage && (
        <div className={`alert ${gmailMessage.includes('Error') || gmailMessage.includes('denied') ? 'alert-error' : 'alert-success'}`}>
          {gmailMessage}
        </div>
      )}

      {/* Main content with sidebar layout */}
      <div className="dashboard-content">
        <div className="dashboard-main">
          {/* Gmail Connection Status */}
          <GmailStatusWidget onSyncComplete={handleSyncComplete} />

          <div className="stats-grid">
            <div className="stat-card">
              <h3>Total Transactions</h3>
              <p className="stat-value">{stats?.total_transactions || 0}</p>
            </div>

            <div className="stat-card">
              <h3>Total Documents</h3>
              <p className="stat-value">{stats?.total_documents || 0}</p>
            </div>

            <div className="stat-card">
              <h3>Total Emails</h3>
              <p className="stat-value">{stats?.total_emails || 0}</p>
            </div>

            <div className="stat-card">
              <h3>Total Amount</h3>
              <p className="stat-value">
                {stats?.total_amount.toFixed(2) || '0.00'} {stats?.currency}
              </p>
            </div>
          </div>
        </div>

        {/* Activity Feed Sidebar */}
        <div className="dashboard-sidebar">
          <EmailActivityFeed refreshTrigger={activityRefresh} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
