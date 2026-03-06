import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import ProjectList from './pages/ProjectList'
import ProjectWorkbench from './pages/ProjectWorkbench'
import ProviderSettings from './pages/ProviderSettings'
import BatchTestDetail from './pages/BatchTestDetail'

function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Navigate to="/projects" replace />} />
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectWorkbench />} />
        <Route path="/projects/:id/batch-tests/:bid" element={<BatchTestDetail />} />
        <Route path="/settings/providers" element={<ProviderSettings />} />
      </Route>
    </Routes>
  )
}

export default App
