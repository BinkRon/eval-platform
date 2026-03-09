import { Breadcrumb as AntBreadcrumb } from 'antd'
import { Link } from 'react-router-dom'

export interface BreadcrumbItem {
  title: string
  path?: string
}

interface BreadcrumbNavProps {
  items: BreadcrumbItem[]
}

export default function BreadcrumbNav({ items }: BreadcrumbNavProps) {
  return (
    <AntBreadcrumb
      style={{ marginBottom: 16 }}
      items={items.map((item, i) => {
        const isLast = i === items.length - 1
        return {
          title: isLast || !item.path ? (
            <span>{item.title}</span>
          ) : (
            <Link to={item.path}>{item.title}</Link>
          ),
        }
      })}
    />
  )
}
