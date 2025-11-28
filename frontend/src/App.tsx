import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import TransactionList from './components/TransactionList';
import DocumentViewer from './components/DocumentViewer';
import Upload from './components/Upload';
import Query from './components/Query';
import GmailConnect from './components/GmailConnect';
import KnowledgeGraph from './components/KnowledgeGraph';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-brand">
            <h2>Email2KG</h2>
          </div>
          <ul className="nav-links">
            <li>
              <Link to="/">Dashboard</Link>
            </li>
            <li>
              <Link to="/transactions">Transactions</Link>
            </li>
            <li>
              <Link to="/graph">Knowledge Graph</Link>
            </li>
            <li>
              <Link to="/upload">Upload PDF</Link>
            </li>
            <li>
              <Link to="/query">Ask Question</Link>
            </li>
            <li>
              <Link to="/gmail">Gmail</Link>
            </li>
          </ul>
        </nav>

        <div className="container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<TransactionList />} />
            <Route path="/graph" element={<KnowledgeGraph />} />
            <Route path="/document/:id" element={<DocumentViewer />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/query" element={<Query />} />
            <Route path="/gmail" element={<GmailConnect />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
