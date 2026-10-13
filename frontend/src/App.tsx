import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './lib/store';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { AnomalyPage } from './pages/AnomalyPage';
import { BehaviorPage } from './pages/BehaviorPage';
import { RiskPage } from './pages/RiskPage';
import { SecurityPage } from './pages/SecurityPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { CryptoLabPage } from './pages/CryptoLabPage';
import { VisualCryptoPage } from './pages/VisualCryptoPage';
import { SteganographyPage } from './pages/SteganographyPage';
import { AuditPage } from './pages/AuditPage';
import { SimulationLabPage } from './pages/SimulationLabPage';
import { AuthPage } from './pages/AuthPage';

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center text-slate-400 font-mono text-xs">
        Initializing PRIVASEC Session...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Dashboard & Operations Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="api-security" element={<SecurityPage />} />
          <Route path="privacy" element={<PrivacyPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="anomalies" element={<AnomalyPage />} />
          <Route path="behavior" element={<BehaviorPage />} />
          <Route path="risk" element={<RiskPage />} />
          <Route path="crypto" element={<CryptoLabPage />} />
          <Route path="visual-crypto" element={<VisualCryptoPage />} />
          <Route path="steganography" element={<SteganographyPage />} />
          <Route path="authentication" element={<AuthPage />} />
          <Route path="simulation" element={<SimulationLabPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
