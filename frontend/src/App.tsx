import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@/components/ThemeProvider'
import { ToastProvider } from '@/components/Toast'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { MainLayout } from '@/layouts/MainLayout'
import { AuthProvider } from '@/contexts/AuthContext'
import { HomePage } from '@/pages/HomePage'

const UploadPage = lazy(() => import('@/pages/UploadPage').then(m => ({ default: m.UploadPage })))
const AnalysisPage = lazy(() => import('@/pages/AnalysisPage').then(m => ({ default: m.AnalysisPage })))
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(m => ({ default: m.DashboardPage })))
const JobMatchPage = lazy(() => import('@/pages/JobMatchPage').then(m => ({ default: m.JobMatchPage })))
const LoginPage = lazy(() => import('@/pages/LoginPage').then(m => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('@/pages/RegisterPage').then(m => ({ default: m.RegisterPage })))

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <Suspense fallback={null}>
              <Routes>
                <Route element={<MainLayout />}>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
                  <Route path="/analysis" element={<ProtectedRoute><AnalysisPage /></ProtectedRoute>} />
                  <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                  <Route path="/match-job" element={<ProtectedRoute><JobMatchPage /></ProtectedRoute>} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
              </Routes>
            </Suspense>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
