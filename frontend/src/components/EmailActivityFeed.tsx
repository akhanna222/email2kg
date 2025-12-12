/**
 * Email Activity Feed - Shows recent email sync activity
 * Displays which emails were qualified/rejected and why (chat-bot style)
 */
import React, { useState, useEffect, useRef } from 'react';
import { getRecentEmailActivity } from '../services/api';
import './EmailActivityFeed.css';

interface EmailActivity {
  id: number;
  subject: string;
  sender: string;
  timestamp: string;
  created_at: string;
  is_qualified: boolean | null;
  qualification_stage: string | null;
  qualification_confidence: number | null;
  qualification_reason: string | null;
  qualified_at: string | null;
  attached_documents: number;
}

interface EmailActivityFeedProps {
  refreshTrigger?: number; // Change this to trigger refresh
}

const EmailActivityFeed: React.FC<EmailActivityFeedProps> = ({ refreshTrigger }) => {
  const [activities, setActivities] = useState<EmailActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const feedEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadActivity();
  }, [refreshTrigger]);

  const loadActivity = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecentEmailActivity(20);
      setActivities(data.emails || []);
    } catch (err: any) {
      console.error('Failed to load email activity:', err);
      setError('Failed to load activity');
    } finally {
      setLoading(false);
    }
  };

  // Auto-scroll to bottom on new activities
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activities]);

  const getStatusIcon = (activity: EmailActivity) => {
    if (activity.is_qualified === null) {
      return '⏳';
    }
    return activity.is_qualified ? '✅' : '❌';
  };

  const getStatusColor = (activity: EmailActivity) => {
    if (activity.is_qualified === null) {
      return 'pending';
    }
    return activity.is_qualified ? 'qualified' : 'rejected';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getSenderName = (sender: string) => {
    // Extract name from email format "Name <email@domain.com>"
    const match = sender.match(/^([^<]+)/);
    return match ? match[1].trim() : sender;
  };

  if (loading && activities.length === 0) {
    return (
      <div className="email-activity-feed">
        <div className="feed-header">
          <h3>📧 Sync Activity</h3>
        </div>
        <div className="feed-body">
          <div className="loading-state">
            <div className="spinner-small"></div>
            <p>Loading activity...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="email-activity-feed">
        <div className="feed-header">
          <h3>📧 Sync Activity</h3>
        </div>
        <div className="feed-body">
          <div className="error-state">
            <p>⚠️ {error}</p>
            <button onClick={loadActivity} className="retry-btn">Retry</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="email-activity-feed">
      <div className="feed-header">
        <h3>📧 Sync Activity</h3>
        <button onClick={loadActivity} className="refresh-btn" title="Refresh">
          🔄
        </button>
      </div>

      <div className="feed-body">
        {activities.length === 0 ? (
          <div className="empty-state">
            <p>No recent activity</p>
            <small>Sync emails to see activity here</small>
          </div>
        ) : (
          <div className="activity-list">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className={`activity-item ${getStatusColor(activity)}`}
              >
                <div className="activity-icon">
                  {getStatusIcon(activity)}
                </div>
                <div className="activity-content">
                  <div className="activity-header">
                    <span className="sender-name">
                      {getSenderName(activity.sender)}
                    </span>
                    <span className="activity-time">
                      {formatTimestamp(activity.created_at)}
                    </span>
                  </div>
                  <div className="activity-subject">
                    {activity.subject || '(No subject)'}
                  </div>
                  {activity.qualification_reason && (
                    <div className="activity-reason">
                      <strong>
                        {activity.is_qualified ? '✓' : '✗'}
                        {activity.is_qualified ? ' Qualified: ' : ' Rejected: '}
                      </strong>
                      {activity.qualification_reason}
                    </div>
                  )}
                  {activity.is_qualified && activity.qualification_stage && (
                    <div className="activity-meta">
                      <span className="stage-badge">
                        {activity.qualification_stage === 'subject' ? '📝 Subject' : '📄 Body'}
                      </span>
                      {activity.qualification_confidence !== null && (
                        <span className="confidence-badge">
                          {Math.round(activity.qualification_confidence * 100)}% confident
                        </span>
                      )}
                      {activity.attached_documents > 0 && (
                        <span className="docs-badge">
                          📎 {activity.attached_documents} doc{activity.attached_documents !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={feedEndRef} />
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailActivityFeed;
