import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './layouts/ProtectedRoute'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Cases from './pages/Cases'
import CaseDetail from './pages/CaseDetail'
import Entities from './pages/Entities'
import EntityDetail from './pages/EntityDetail'
import NetworkAnalysis from './pages/NetworkAnalysis'
import Timeline from './pages/Timeline'
import MapView from './pages/MapView'
import Alerts from './pages/Alerts'
import SearchPage from './pages/SearchPage'
import Reports from './pages/Reports'
import AuditLogPage from './pages/AuditLogPage'
import Settings from './pages/Settings'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/entities/:entityId" element={<EntityDetail />} />
          <Route path="/network" element={<NetworkAnalysis />} />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/audit" element={<AuditLogPage />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  )
}
