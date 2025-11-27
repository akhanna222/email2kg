import React, { useEffect, useState } from 'react';
import { getStats } from '../services/api';
import { Stats } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
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
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

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
            ${stats?.total_amount.toFixed(2) || '0.00'} {stats?.currency}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
