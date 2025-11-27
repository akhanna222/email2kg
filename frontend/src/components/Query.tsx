import React, { useState } from 'react';
import { query } from '../services/api';
import { QueryResult } from '../types';

const Query: React.FC = () => {
  const [queryType, setQueryType] = useState('total_spend');
  const [params, setParams] = useState<any>({ months: 1 });
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleQueryTypeChange = (type: string) => {
    setQueryType(type);
    setResult(null);

    // Set default params based on query type
    if (type === 'total_spend') {
      setParams({ months: 1 });
    } else if (type === 'top_vendors') {
      setParams({ limit: 10 });
    } else if (type === 'invoices_above') {
      setParams({ amount: 100 });
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const data = await query(queryType, params);
      setResult(data);
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="query">
      <h1>Ask a Question</h1>

      <div className="query-form">
        <div className="form-group">
          <label>Select Query Type:</label>
          <select
            value={queryType}
            onChange={(e) => handleQueryTypeChange(e.target.value)}
          >
            <option value="total_spend">Total Spend (Last X Months)</option>
            <option value="top_vendors">Top Vendors by Amount</option>
            <option value="invoices_above">Invoices/Receipts Above Amount</option>
          </select>
        </div>

        {queryType === 'total_spend' && (
          <div className="form-group">
            <label>Number of Months:</label>
            <input
              type="number"
              min="1"
              max="12"
              value={params.months}
              onChange={(e) =>
                setParams({ ...params, months: parseInt(e.target.value) })
              }
            />
          </div>
        )}

        {queryType === 'top_vendors' && (
          <div className="form-group">
            <label>Number of Vendors:</label>
            <input
              type="number"
              min="1"
              max="50"
              value={params.limit}
              onChange={(e) =>
                setParams({ ...params, limit: parseInt(e.target.value) })
              }
            />
          </div>
        )}

        {queryType === 'invoices_above' && (
          <div className="form-group">
            <label>Minimum Amount ($):</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={params.amount}
              onChange={(e) =>
                setParams({ ...params, amount: parseFloat(e.target.value) })
              }
            />
          </div>
        )}

        <button onClick={handleSubmit} disabled={loading}>
          {loading ? 'Processing...' : 'Run Query'}
        </button>
      </div>

      {result && (
        <div className="query-result">
          <h2>Result</h2>
          <h3>{result.query}</h3>

          {queryType === 'total_spend' && (
            <div className="total-spend-result">
              <div className="total">
                <strong>Total Spend:</strong> ${result.total} {result.currency}
              </div>

              {result.breakdown_by_type && (
                <div className="breakdown">
                  <h4>Breakdown by Type:</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.breakdown_by_type.map((item: any, idx: number) => (
                        <tr key={idx}>
                          <td>{item.type}</td>
                          <td>${item.amount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {result.breakdown_by_month && (
                <div className="breakdown">
                  <h4>Breakdown by Month:</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Month</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.breakdown_by_month.map((item: any, idx: number) => (
                        <tr key={idx}>
                          <td>{item.month}</td>
                          <td>${item.amount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {queryType === 'top_vendors' && (
            <div className="top-vendors-result">
              <table>
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>Total Amount</th>
                    <th>Transactions</th>
                  </tr>
                </thead>
                <tbody>
                  {result.vendors.map((vendor: any, idx: number) => (
                    <tr key={idx}>
                      <td>{vendor.name}</td>
                      <td>${vendor.total_amount}</td>
                      <td>{vendor.transaction_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {queryType === 'invoices_above' && (
            <div className="invoices-above-result">
              <p>
                <strong>Count:</strong> {result.count} transactions
              </p>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Vendor</th>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Document</th>
                  </tr>
                </thead>
                <tbody>
                  {result.transactions.map((txn: any) => (
                    <tr key={txn.id}>
                      <td>{txn.date ? new Date(txn.date).toLocaleDateString() : '-'}</td>
                      <td>{txn.vendor || '-'}</td>
                      <td>{txn.type}</td>
                      <td>
                        ${txn.amount} {txn.currency}
                      </td>
                      <td>
                        {txn.document_id && (
                          <a href={`/document/${txn.document_id}`}>
                            {txn.document_filename}
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Query;
