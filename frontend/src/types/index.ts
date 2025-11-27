export interface Transaction {
  id: number;
  amount: number;
  currency: string;
  date: string | null;
  type: string;
  vendor: string | null;
  document_id: number | null;
  description: string;
}

export interface Document {
  id: number;
  filename: string;
  file_path: string;
  file_size: number;
  processing_status: string;
  document_type: string | null;
  extracted_text: string;
  extracted_data: any;
  uploaded_at: string;
  processed_at: string | null;
}

export interface Filters {
  vendors: string[];
  document_types: string[];
  date_range: {
    min: string | null;
    max: string | null;
  };
}

export interface Stats {
  total_transactions: number;
  total_documents: number;
  total_emails: number;
  total_amount: number;
  currency: string;
}

export interface QueryResult {
  query: string;
  [key: string]: any;
}
