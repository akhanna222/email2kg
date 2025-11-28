import React, { useEffect, useState } from 'react';
import { getTransactions, getFilters } from '../services/api';
import { Transaction, Filters } from '../types';
import { format } from 'date-fns';

const TransactionList: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filters, setFilters] = useState<Filters | null>(null);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Filter states
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [vendor, setVendor] = useState('');
  const [docType, setDocType] = useState('');

  useEffect(() => {
    loadFilters();
    loadTransactions();
  }, []);

  const loadFilters = async () => {
    try {
      const data = await getFilters();
      setFilters(data);
    } catch (error) {
      console.error('Failed to load filters:', error);
    }
  };

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (vendor) params.vendor = vendor;
      if (docType) params.doc_type = docType;

      const data = await getTransactions(params);
      setTransactions(data.transactions);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = () => {
    loadTransactions();
  };

  const clearFilters = () => {
    setDateFrom('');
    setDateTo('');
    setVendor('');
    setDocType('');
    setTimeout(loadTransactions, 0);
  };

  return (
    <div className="transaction-list">
      <h1>Transactions</h1>

      <div className="filters">
        <div className="filter-group">
          <label>Date From:</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Date To:</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Vendor:</label>
          <select value={vendor} onChange={(e) => setVendor(e.target.value)}>
            <option value="">All Vendors</option>
            {filters?.vendors.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Document Type:</label>
          <select value={docType} onChange={(e) => setDocType(e.target.value)}>
            <option value="">All Types</option>
            {filters?.document_types.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <button onClick={handleFilterChange}>Apply Filters</button>
        <button onClick={clearFilters}>Clear Filters</button>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          Loading transactions...
        </div>
      ) : (
        <>
          <p className="total-count">Total: {total} transactions</p>

          <table className="transaction-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Vendor</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.id}>
                  <td>
                    {txn.date
                      ? format(new Date(txn.date), 'MMM dd, yyyy')
                      : '-'}
                  </td>
                  <td>{txn.vendor || '-'}</td>
                  <td>
                    <span className={`badge badge-${txn.type}`}>
                      {txn.type}
                    </span>
                  </td>
                  <td className="amount">
                    ${txn.amount.toFixed(2)} {txn.currency}
                  </td>
                  <td>{txn.description}</td>
                  <td>
                    {txn.document_id && (
                      <a href={`/document/${txn.document_id}`}>View Doc</a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {transactions.length === 0 && (
            <p className="no-data">No transactions found</p>
          )}
        </>
      )}
    </div>
  );
};

export default TransactionList;
