import React, { useState } from 'react';
import { uploadPDF } from '../services/api';

const Upload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file');
      return;
    }

    setUploading(true);
    setMessage('');

    try {
      const result = await uploadPDF(file);
      setMessage(`Successfully uploaded: ${result.filename}`);
      setFile(null);

      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (error: any) {
      setMessage(`Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload">
      <h1>Upload PDF</h1>

      <div className="upload-box">
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
        />

        {file && (
          <div className="file-info">
            <p>
              <strong>Selected:</strong> {file.name}
            </p>
            <p>
              <strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB
            </p>
          </div>
        )}

        <button onClick={handleUpload} disabled={!file || uploading}>
          {uploading ? 'Uploading...' : 'Upload'}
        </button>

        {message && (
          <div className={`message ${message.includes('failed') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}
      </div>

      <div className="upload-help">
        <h3>Instructions</h3>
        <ul>
          <li>Only PDF files are supported</li>
          <li>Maximum file size: 10 MB</li>
          <li>Documents will be automatically processed</li>
          <li>Processing includes text extraction and data extraction</li>
        </ul>
      </div>
    </div>
  );
};

export default Upload;
