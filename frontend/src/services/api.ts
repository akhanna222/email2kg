import axios from 'axios';
import { Transaction, Document, Filters, Stats, QueryResult } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth
export const getGoogleAuthUrl = async (): Promise<string> => {
  const response = await api.get('/auth/google');
  return response.data.auth_url;
};

export const handleOAuthCallback = async (code: string) => {
  const response = await api.post('/auth/callback', { code });
  return response.data;
};

// Email Sync
export const syncGmail = async () => {
  const response = await api.post('/sync/gmail');
  return response.data;
};

// Upload
export const uploadPDF = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload/pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Transactions
export const getTransactions = async (params?: {
  date_from?: string;
  date_to?: string;
  vendor?: string;
  doc_type?: string;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; transactions: Transaction[] }> => {
  const response = await api.get('/transactions', { params });
  return response.data;
};

// Documents
export const getDocument = async (id: number): Promise<Document> => {
  const response = await api.get(`/documents/${id}`);
  return response.data;
};

// Query
export const query = async (queryType: string, params: any): Promise<QueryResult> => {
  const response = await api.post('/query', {
    query_type: queryType,
    params,
  });
  return response.data;
};

// Filters
export const getFilters = async (): Promise<Filters> => {
  const response = await api.get('/filters');
  return response.data;
};

// Stats
export const getStats = async (): Promise<Stats> => {
  const response = await api.get('/stats');
  return response.data;
};
