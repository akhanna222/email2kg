import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { authService } from '../services/authService';

interface Email {
  id: number;
  gmail_id: string;
  subject: string;
  sender: string;
  receiver: string;
  timestamp: string;
  body_text: string;
}

const EmailViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [email, setEmail] = useState<Email | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEmail();
  }, [id]);

  const loadEmail = async () => {
    try {
      const token = authService.getToken();
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/emails/${id}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      setEmail(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load email');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading email...
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <h2>Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!email) {
    return (
      <div className="error">
        <h2>Email Not Found</h2>
      </div>
    );
  }

  return (
    <div className="email-viewer" style={{ padding: '2em', maxWidth: '900px', margin: '0 auto' }}>
      <h1>Email Details</h1>

      <div style={{ background: '#f8f9fa', padding: '1.5em', borderRadius: '8px', marginBottom: '1em' }}>
        <div style={{ marginBottom: '1em' }}>
          <strong>From:</strong> {email.sender}
        </div>
        <div style={{ marginBottom: '1em' }}>
          <strong>To:</strong> {email.receiver}
        </div>
        <div style={{ marginBottom: '1em' }}>
          <strong>Date:</strong> {new Date(email.timestamp).toLocaleString()}
        </div>
        <div>
          <strong>Subject:</strong> {email.subject}
        </div>
      </div>

      <div style={{ background: 'white', padding: '1.5em', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h3>Message</h3>
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
          {email.body_text || 'No message content'}
        </div>
      </div>

      <div style={{ marginTop: '2em' }}>
        <button
          onClick={() => window.history.back()}
          style={{
            padding: '0.75em 1.5em',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          ← Back to Transactions
        </button>
      </div>
    </div>
  );
};

export default EmailViewer;
