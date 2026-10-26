// ============================================================
// SMART CAMPUS SHIELD — Root Application
// Interface: Security Operations Center with 4 Looping Feeds
// ============================================================
import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth, LoginPage } from './components/Auth';
import { AuthProvider } from './components/Auth';
import { Layout, Page } from './components/Layout';
import { DashboardPage } from './components/Dashboard';
import { CamerasPage } from './components/Cameras';
import { IncidentsPage } from './components/Incidents';
import { IncidentReports } from './components/IncidentReports';
import { AnalyticsPage } from './components/Analytics';
import { DemoPage } from './components/DemoControl';
import { AboutPage } from './components/About';
import { LandingPage } from './components/LandingPage';
import { EmergencyToast } from './components/EmergencyToast';
import { store } from './services/store';
import type { Incident } from './types';

export default function App() {
  const { user, logout } = useAuth();
  const [activePage, setActivePage] = useState<Page>('dashboard');
  const [detectionMode, setDetectionMode] = useState<'LIVE_AI' | 'DEMO'>('DEMO');
  const [incidents, setIncidents] = useState<Incident[]>(() => store.getIncidents());

  useEffect(() => {
    return store.subscribeToIncidents((updated) => setIncidents(updated));
  }, []);

  const activeCount = incidents.filter((i) => i.status === 'ACTIVE').length;

  // Show login if not authenticated
  if (!user) {
    return <LoginPage onLogin={() => {}} />;
  }

  if (activePage === 'landing') {
    return <LandingPage onEnterDashboard={() => setActivePage('dashboard')} />;
  }

  return (
    <Layout
      activePage={activePage}
      onNavigate={setActivePage}
      detectionMode={detectionMode}
      onToggleMode={() => setDetectionMode((m) => (m === 'DEMO' ? 'LIVE_AI' : 'DEMO'))}
      activeIncidentCount={activeCount}
    >
      {activePage === 'dashboard' && <DashboardPage onNavigate={(p) => setActivePage(p as Page)} />}
      {activePage === 'cameras' && <CamerasPage />}
      {activePage === 'incidents' && <IncidentsPage />}
      {activePage === 'reports' && (
        <IncidentReports onNavigate={(screen) => setActivePage(screen as Page)} />
      )}
      {activePage === 'analytics' && <AnalyticsPage />}
      {activePage === 'demo' && <DemoPage />}
      {activePage === 'about' && <AboutPage />}
    </Layout>
  );
}
