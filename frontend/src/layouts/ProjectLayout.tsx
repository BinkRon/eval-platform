import { Outlet, useParams } from 'react-router-dom'
import FloatingButton from '../components/builder-agent/FloatingButton'

export default function ProjectLayout() {
  const { id } = useParams<{ id: string }>()

  return (
    <>
      <Outlet />
      {id && <FloatingButton projectId={id} />}
    </>
  )
}
