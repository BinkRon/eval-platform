import { lazy, Suspense } from 'react'
import { Navigate, createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from './layouts/MainLayout'
import ProjectLayout from './layouts/ProjectLayout'
import AuthGuard from './components/shared/AuthGuard'
import ProjectList from './pages/ProjectList'
import ProjectWorkbench from './pages/ProjectWorkbench'
import ProviderSettings from './pages/ProviderSettings'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
const BatchTestDetail = lazy(() => import('./pages/BatchTestDetail'))

const ProjectConfig = lazy(() => import('./pages/ProjectConfig'))
const DialogTheater = lazy(() => import('./pages/DialogTheater'))

const PageLoading = () => <Spin style={{ display: 'block', margin: '100px auto' }} />

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: (
      <AuthGuard>
        <MainLayout />
      </AuthGuard>
    ),
    children: [
      { path: '/', element: <Navigate to="/projects" replace /> },
      { path: '/projects', element: <ProjectList /> },
      {
        element: <ProjectLayout />,
        children: [
          { path: '/projects/:id', element: <ProjectWorkbench /> },
          { path: '/projects/:id/config', element: <Suspense fallback={<PageLoading />}><ProjectConfig /></Suspense> },
          { path: '/projects/:id/batch-tests/:bid', element: <Suspense fallback={<PageLoading />}><BatchTestDetail /></Suspense> },
          { path: '/projects/:id/batch-tests/:bid/theater/:rid', element: <Suspense fallback={<PageLoading />}><DialogTheater /></Suspense> },
        ],
      },
      { path: '/settings/providers', element: <ProviderSettings /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
