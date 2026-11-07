import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from '../features/auth/LoginPage'
import { ProtectedRoute } from '../features/auth/ProtectedRoute'
import { DashboardLayout } from '../features/dashboard/DashboardLayout'
import { HomePage } from '../features/home/HomePage'
import { defaultPath } from '../features/dashboard/menu'
import { WorkspaceLayout } from '../features/dashboard/WorkspaceLayout'
import { AppIndexRedirect, WorkspacePage } from '../features/dashboard/WorkspacePage'
import { SiteLayout } from './layout/SiteLayout'

export function AppRoutes() {
  return (
    <Routes>
      {/* public site */}
      <Route element={<SiteLayout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
      </Route>

      {/* protected dashboard */}
      <Route
        path="dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to={defaultPath} replace />} />
        <Route path=":appId" element={<WorkspaceLayout />}>
          <Route index element={<AppIndexRedirect />} />
          <Route path=":pageId" element={<WorkspacePage />} />
        </Route>
        {/* old URLs */}
        <Route path="rag-chat" element={<Navigate to={defaultPath} replace />} />
        <Route path="upload" element={<Navigate to={defaultPath} replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
