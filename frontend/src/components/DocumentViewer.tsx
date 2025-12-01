import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getDocument } from '../services/api';
import { Document } from '../types';
import { format } from 'date-fns';

const API_BASE_URL = process.env.REACT_APP_API_URL?.replace('/api', '') || 'http://localhost:8000';

const DocumentViewer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadDocument(parseInt(id));
    }
  }, [id]);

  const loadDocument = async (docId: number) => {
    try {
      const data = await getDocument(docId);
      setDocument(data);
    } catch (error) {
      console.error('Failed to load document:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        Loading document...
      </div>
    );
  }

  if (!document) {
    return <div className="error">Document not found</div>;
  }

  return (
    <div className="document-viewer">
      <h1>Document Details</h1>

      <div className="document-info">
        <div className="info-row">
          <strong>Filename:</strong> {document.filename}
        </div>
        <div className="info-row">
          <strong>Status:</strong>{' '}
          <span className={`badge badge-${document.processing_status}`}>
            {document.processing_status}
          </span>
        </div>
        <div className="info-row">
          <strong>Type:</strong> {document.document_type || 'Unknown'}
        </div>
        <div className="info-row">
          <strong>Size:</strong> {(document.file_size / 1024).toFixed(2)} KB
        </div>
        <div className="info-row">
          <strong>Uploaded:</strong>{' '}
          {format(new Date(document.uploaded_at), 'MMM dd, yyyy HH:mm')}
        </div>
        {document.processed_at && (
          <div className="info-row">
            <strong>Processed:</strong>{' '}
            {format(new Date(document.processed_at), 'MMM dd, yyyy HH:mm')}
          </div>
        )}
      </div>

      {document.extracted_data && (
        <div className="extracted-data">
          <h2>Extracted Data</h2>
          <div className="data-grid">
            {document.extracted_data.amount && (
              <div className="data-item">
                <strong>Amount:</strong> ${document.extracted_data.amount}{' '}
                {document.extracted_data.currency}
              </div>
            )}
            {document.extracted_data.date && (
              <div className="data-item">
                <strong>Date:</strong> {document.extracted_data.date}
              </div>
            )}
            {document.extracted_data.merchant && (
              <div className="data-item">
                <strong>Merchant:</strong> {document.extracted_data.merchant}
              </div>
            )}
            {document.extracted_data.vendor && (
              <div className="data-item">
                <strong>Vendor:</strong> {document.extracted_data.vendor}
              </div>
            )}
            {document.extracted_data.invoice_number && (
              <div className="data-item">
                <strong>Invoice #:</strong>{' '}
                {document.extracted_data.invoice_number}
              </div>
            )}
          </div>

          {document.extracted_data.items &&
            document.extracted_data.items.length > 0 && (
              <div className="items">
                <h3>Items</h3>
                <ul>
                  {document.extracted_data.items.map(
                    (item: any, idx: number) => (
                      <li key={idx}>{JSON.stringify(item)}</li>
                    )
                  )}
                </ul>
              </div>
            )}
        </div>
      )}

      {document.extracted_text && (
        <div className="extracted-text">
          <h2>Extracted Text</h2>
          <pre>{document.extracted_text}</pre>
        </div>
      )}

      <div className="actions">
        <a
          href={`${API_BASE_URL}${document.file_path.replace('.', '')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="button"
        >
          View PDF
        </a>
      </div>
    </div>
  );
};

export default DocumentViewer;
