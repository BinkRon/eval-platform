import { Button, List, Popconfirm, Popover, Upload, Empty, message } from 'antd'
import { UploadOutlined, DeleteOutlined, FolderOutlined } from '@ant-design/icons'
import { useProjectFiles, useUploadFile, useDeleteFile } from '../../hooks/useProjectFiles'
import type { RcFile } from 'antd/es/upload'

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md', '.xlsx', '.csv']
const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

interface ProjectFileManagerProps {
  projectId: string
}

export default function ProjectFileManager({ projectId }: ProjectFileManagerProps) {
  const { data: files = [], isLoading } = useProjectFiles(projectId)
  const uploadMutation = useUploadFile(projectId)
  const deleteMutation = useDeleteFile(projectId)

  const handleBeforeUpload = (file: RcFile) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      message.error(`不支持的文件类型，仅支持 ${ALLOWED_EXTENSIONS.join('、')}`)
      return false
    }
    if (file.size > MAX_FILE_SIZE) {
      message.error('文件大小不能超过 20MB')
      return false
    }
    uploadMutation.mutate(file)
    return false // prevent default upload
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()}`
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
  }

  const content = (
    <div style={{ width: 320 }}>
      <div style={{ marginBottom: 8, textAlign: 'right' }}>
        <Upload
          showUploadList={false}
          beforeUpload={handleBeforeUpload}
          accept={ALLOWED_EXTENSIONS.join(',')}
        >
          <Button
            size="small"
            icon={<UploadOutlined />}
            loading={uploadMutation.isPending}
          >
            上传
          </Button>
        </Upload>
      </div>
      {files.length === 0 && !isLoading ? (
        <Empty description="暂无文件" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          size="small"
          loading={isLoading}
          dataSource={files}
          renderItem={(file) => (
            <List.Item
              style={{ padding: '4px 0' }}
              actions={[
                <Popconfirm
                  key="delete"
                  title="确认删除此文件？"
                  onConfirm={() => deleteMutation.mutate(file.id)}
                  okText="删除"
                  cancelText="取消"
                >
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    loading={deleteMutation.isPending && deleteMutation.variables === file.id}
                  />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={
                  <span style={{ fontSize: 13 }} title={file.filename}>
                    {file.filename}
                  </span>
                }
                description={
                  <span style={{ fontSize: 12, color: '#999' }}>
                    {formatSize(file.file_size)} · {formatDate(file.created_at)}
                  </span>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  )

  return (
    <Popover
      content={content}
      title="项目文件"
      trigger="click"
      placement="bottomRight"
    >
      <Button type="text" size="small" icon={<FolderOutlined />} />
    </Popover>
  )
}
