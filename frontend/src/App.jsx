import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Login';
import DashboardOverview from './pages/DashboardOverview';
import LiveEvents from './pages/LiveEvents';
import ThreatDetection from './pages/ThreatDetection';
import SecurityAlerts from './pages/SecurityAlerts';
import IncidentManagement from './pages/IncidentManagement';
import IncidentInvestigation from './pages/IncidentInvestigation';
import NetworkAnalytics from './pages/NetworkAnalytics';
import EndpointMonitoring from './pages/EndpointMonitoring';
import MLAnalytics from './pages/MLAnalytics';
import DetectionRules from './pages/DetectionRules';
import ThreatIntelligence from './pages/ThreatIntelligence';
import ResponseManagement from './pages/ResponseManagement';
import AuditLogs from './pages/AuditLogs';
import UserManagement from './pages/UserManagement';
import Settings from './pages/Settings';

const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user, loading, isAdmin } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070a10] flex items-center justify-center font-mono text-cyan-400 text-sm">
        Initializing SentinelAI SOC Environment...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardOverview />} />
            <Route path="overview" element={<DashboardOverview />} />
            <Route path="events" element={<LiveEvents />} />
            <Route path="threats" element={<ThreatDetection />} />
            <Route path="alerts" element={<SecurityAlerts />} />
            <Route path="incidents" element={<IncidentManagement />} />
            <Route path="incidents/:id" element={<IncidentInvestigation />} />
            <Route path="network" element={<NetworkAnalytics />} />
            <Route path="endpoints" element={<EndpointMonitoring />} />
            <Route path="ml-analytics" element={<MLAnalytics />} />
            <Route path="rules" element={<DetectionRules />} />
            <Route path="threat-intel" element={<ThreatIntelligence />} />
            <Route path="response" element={<ResponseManagement />} />
            <Route path="audit" element={<AuditLogs />} />
            <Route
              path="users"
              element={
                <ProtectedRoute requireAdmin={true}>
                  <UserManagement />
                </ProtectedRoute>
              }
            />
            <Route path="settings" element={<Settings />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
