import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard.jsx';
import AdminLogin from '../pages/AdminLogin.jsx';
import AdminDashboard from '../pages/AdminDashboard.jsx';
import { useAuth } from '../context/AuthContext.jsx';

/**
 * RequireAuth — wraps a route that needs a logged-in admin.
 * Redirects to /admin/login if unauthenticated.
 */
const RequireAuth = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    // Still resolving session — render nothing to avoid flash
    return null;
  }

  if (!user) {
    return <Navigate to="/admin/login" replace />;
  }

  return children;
};

const AppRouter = () => (
  <Router>
    <Routes>
      {/* ── Public: user ticket submission portal ── */}
      <Route path="/" element={<Dashboard />} />

      {/* ── Admin auth ── */}
      <Route path="/admin/login" element={<AdminLogin />} />

      {/* ── Protected: role-based ticket dashboard ── */}
      <Route
        path="/admin/dashboard"
        element={
          <RequireAuth>
            <AdminDashboard />
          </RequireAuth>
        }
      />

      {/* ── Catch-all ── */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </Router>
);

export default AppRouter;
