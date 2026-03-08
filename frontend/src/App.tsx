import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from './layouts/MainLayout'
import ProjectList from './pages/ProjectList'
import ProjectWorkbench from './pages/ProjectWorkbench'
import ProviderSettings from './pages/ProviderSettings'
const BatchTestDetail = lazy(() => import('./pages/BatchTestDetail'))

const ProjectConfig = lazy(() => import('./pages/ProjectConfig'))
const DialogTheater = lazy(() => import('./pages/DialogTheater'))

const PageLoading = () => <Spin style={{ display: 'block', margin: '100px auto' }} />

function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectWorkbench />} />
        <Route path="/projects/:id/config" element={<Suspense fallback={<PageLoading />}><ProjectConfig /></Suspense>} />
        <Route path="/projects/:id/batch-tests/:bid" element={<Suspense fallback={<PageLoading />}><BatchTestDetail /></Suspense>} />
        <Route path="/projects/:id/batch-tests/:bid/theater/:rid" element={<Suspense fallback={<PageLoading />}><DialogTheater /></Suspense>} />
        <Route path="/settings/providers" element={<ProviderSettings />} />
      </Route>
    </Routes>
  )
}

export default App
