import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import TransactionList from './components/TransactionList';
import DocumentViewer from './components/DocumentViewer';
import EmailViewer from './components/EmailViewer';
import Upload from './components/Upload';
import Query from './components/Query';
import GmailConnect from './components/GmailConnect';
import KnowledgeGraph from './components/KnowledgeGraph';
import Login from './components/Login';
import Register from './components/Register';
import './App.css';

/**
 * Protected Route wrapper - redirects to login if not authenticated
 */
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

/**
 * Main navigation bar with authentication support
 */
const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <h2>Email2KG</h2>
      </div>
      <ul className="nav-links">
        <li>
          <Link to="/dashboard">Dashboard</Link>
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
          <button
            onClick={logout}
            className="nav-logout"
            title={`Signed in as ${user?.email}`}
          >
            Sign Out
          </button>
        </li>
      </ul>
    </nav>
  );
};

/**
 * Home Route - Shows Landing Page if not authenticated, Dashboard if authenticated
 */
const HomeRoute: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />;
};

/**
 * App content with routing
 */
const AppContent: React.FC = () => {
  return (
    <div className="App">
      <Navbar />
      <div className="container">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomeRoute />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/transactions"
            element={
              <ProtectedRoute>
                <TransactionList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/graph"
            element={
              <ProtectedRoute>
                <KnowledgeGraph />
              </ProtectedRoute>
            }
          />
          <Route
            path="/document/:id"
            element={
              <ProtectedRoute>
                <DocumentViewer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/email/:id"
            element={
              <ProtectedRoute>
                <EmailViewer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <Upload />
              </ProtectedRoute>
            }
          />
          <Route
            path="/query"
            element={
              <ProtectedRoute>
                <Query />
              </ProtectedRoute>
            }
          />
          <Route
            path="/gmail"
            element={
              <ProtectedRoute>
                <GmailConnect />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </div>
  );
};

/**
 * Main App component with AuthProvider
 */
function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
