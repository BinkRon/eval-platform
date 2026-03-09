import { lazy, Suspense } from 'react'
import { Navigate, createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from './layouts/MainLayout'
import ProjectList from './pages/ProjectList'
import ProjectWorkbench from './pages/ProjectWorkbench'
import ProviderSettings from './pages/ProviderSettings'
const BatchTestDetail = lazy(() => import('./pages/BatchTestDetail'))

const ProjectConfig = lazy(() => import('./pages/ProjectConfig'))
const DialogTheater = lazy(() => import('./pages/DialogTheater'))

const PageLoading = () => <Spin style={{ display: 'block', margin: '100px auto' }} />

const router = createBrowserRouter([
  {
    element: <MainLayout />,
    children: [
      { path: '/', element: <Navigate to="/projects" replace /> },
      { path: '/projects', element: <ProjectList /> },
      { path: '/projects/:id', element: <ProjectWorkbench /> },
      { path: '/projects/:id/config', element: <Suspense fallback={<PageLoading />}><ProjectConfig /></Suspense> },
      { path: '/projects/:id/batch-tests/:bid', element: <Suspense fallback={<PageLoading />}><BatchTestDetail /></Suspense> },
      { path: '/projects/:id/batch-tests/:bid/theater/:rid', element: <Suspense fallback={<PageLoading />}><DialogTheater /></Suspense> },
      { path: '/settings/providers', element: <ProviderSettings /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
