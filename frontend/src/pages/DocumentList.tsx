import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Input,
  Tree,
  Upload,
  Form,
  InputNumber,
  Select,
  Popconfirm,
  Card,
  Breadcrumb,
} from 'antd'
import {
  PlusOutlined,
  UploadOutlined,
  FolderOutlined,
  FileOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  TagOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import { documentApi, Document, Folder, DocumentDetail, Tag as DocumentTag, DocumentConfig } from '@/api/documents'
import dayjs from 'dayjs'
import type { DataNode } from 'antd/es/tree'

const { Search } = Input
const { TextArea } = Input

const DocumentList = () => {
  const [documents, setDocuments] = useState<Document[]>([])
  const [allFolders, setAllFolders] = useState<Folder[]>([]) // 所有文件夹（用于构建树）
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [folderPath, setFolderPath] = useState<Folder[]>([])
  const [loading, setLoading] = useState(false)
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]) // 展开的节点
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [uploadForm] = Form.useForm()
  const [folderModalVisible, setFolderModalVisible] = useState(false)
  const [folderForm] = Form.useForm()
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(null)
  const [tags, setTags] = useState<DocumentTag[]>([])
  const [documentTags, setDocumentTags] = useState<DocumentTag[]>([])
  const [tagModalVisible, setTagModalVisible] = useState(false)
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [tagFilter, setTagFilter] = useState<string | undefined>(undefined)

  // 初始化时加载根目录文件夹
  useEffect(() => {
    const initFolders = async () => {
      try {
        const rootFolders = await documentApi.getFolders(undefined)
        setAllFolders(rootFolders)
      } catch (error: any) {
        message.error(error.response?.data?.detail || '获取文件夹列表失败')
      }
    }
    initFolders()
  }, [])

  useEffect(() => {
    fetchDocuments()
    fetchTags()
  }, [currentFolderId])
  
  // 当展开节点变化时，懒加载子文件夹
  useEffect(() => {
    const loadChildren = async () => {
      const newFolders: Folder[] = []
      for (const expandedKey of expandedKeys) {
        try {
          const children = await documentApi.getFolders(expandedKey as string)
          for (const child of children) {
            if (!allFolders.find(f => f.id === child.id)) {
              newFolders.push(child)
            }
          }
        } catch (error: any) {
          // 忽略单个文件夹加载失败
        }
      }
      if (newFolders.length > 0) {
        setAllFolders([...allFolders, ...newFolders])
      }
    }
    if (expandedKeys.length > 0) {
      loadChildren()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expandedKeys])
  
  // 当选中文件夹变化时，确保该文件夹信息已加载
  useEffect(() => {
    if (currentFolderId) {
      const folder = allFolders.find(f => f.id === currentFolderId)
      if (!folder) {
        // 如果选中的文件夹不在列表中，加载它的信息
        documentApi.getFolder(currentFolderId).then(folderInfo => {
          if (!allFolders.find(f => f.id === folderInfo.id)) {
            setAllFolders([...allFolders, folderInfo])
          }
        }).catch(() => {
          // 忽略错误
        })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentFolderId])
  
  // 刷新文件夹列表（用于创建/删除后刷新）
  const refreshFolders = async () => {
    try {
      // 重新加载根目录文件夹
      const rootFolders = await documentApi.getFolders(undefined)
      const allFoldersList: Folder[] = [...rootFolders]
      
      // 加载已展开节点的子文件夹
      for (const expandedKey of expandedKeys) {
        try {
          const children = await documentApi.getFolders(expandedKey as string)
          for (const child of children) {
            if (!allFoldersList.find(f => f.id === child.id)) {
              allFoldersList.push(child)
            }
          }
        } catch (error: any) {
          // 忽略单个文件夹加载失败
        }
      }
      
      setAllFolders(allFoldersList)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取文件夹列表失败')
    }
  }

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      const data = await documentApi.listDocuments({
        folder_id: currentFolderId || undefined,
        status: statusFilter || undefined,
        tag: tagFilter,
        skip: 0,
        limit: 100,
      })
      setDocuments(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取文档列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchTags = async () => {
    try {
      const data = await documentApi.getTags()
      setTags(data)
    } catch (error: any) {
      // 忽略错误，标签获取失败不影响主流程
    }
  }

  const handleUpload = async (values: any) => {
    try {
      const fileList = uploadForm.getFieldValue('file')
      if (!fileList || !Array.isArray(fileList) || fileList.length === 0) {
        message.error('请选择文件')
        return
      }
      const file = fileList[0]
      if (!file || !file.originFileObj) {
        message.error('请选择文件')
        return
      }

      const config: any = {}
      if (values.chunk_size) config.chunk_size = values.chunk_size
      if (values.chunk_overlap) config.chunk_overlap = values.chunk_overlap
      if (values.split_method) config.split_method = values.split_method
      if (values.split_keyword) config.split_keyword = values.split_keyword
      if (currentFolderId) config.folder_id = currentFolderId

      // 先检查同名文件
      const duplicateCheck = await documentApi.checkDuplicate({
        filename: file.originFileObj.name,
        folder_id: currentFolderId || undefined,
      })

      if (duplicateCheck.exists) {
        Modal.confirm({
          title: '文件已存在',
          content: `文件 "${file.originFileObj.name}" 已存在（版本：${duplicateCheck.version}），是否覆盖上传新版本？`,
          onOk: async () => {
            await documentApi.uploadDocument(file.originFileObj, config)
            message.success('上传成功')
            setUploadModalVisible(false)
            uploadForm.resetFields()
            fetchDocuments()
          },
        })
        return
      }

      await documentApi.uploadDocument(file.originFileObj, config)
      message.success('上传成功')
      setUploadModalVisible(false)
      uploadForm.resetFields()
      fetchDocuments()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '上传失败')
    }
  }

  const handleCreateFolder = async (values: { name: string }) => {
    try {
      await documentApi.createFolder({
        name: values.name,
        parent_id: currentFolderId || null,
      })
      message.success('创建成功')
      setFolderModalVisible(false)
      folderForm.resetFields()
      // 刷新文件夹树
      await refreshFolders()
      // 如果是在某个文件夹下创建子文件夹，自动展开该文件夹
      if (currentFolderId) {
        setExpandedKeys([...expandedKeys, currentFolderId])
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建失败')
    }
  }
  
  // 检查是否可以创建子文件夹
  // 根目录（level 0）可以建1级文件夹（level 1）
  // 1级文件夹（level 1）不能再建了
  const canCreateSubFolder = (): boolean => {
    if (!currentFolderId) {
      // 根目录（level 0）下可以创建1级文件夹（level 1）
      return true
    }
    const currentFolder = allFolders.find(f => f.id === currentFolderId)
    // 如果找不到文件夹信息，保守处理：返回 false（避免在不确定的情况下允许创建）
    if (!currentFolder) {
      return false
    }
    // level < 1 的文件夹可以创建子文件夹（只有根目录可以建）
    return currentFolder.level < 1
  }

  const handleDeleteDocument = async (id: string) => {
    try {
      await documentApi.deleteDocument(id)
      message.success('文档已删除')
      fetchDocuments()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除文档失败')
    }
  }

  const handleDownloadDocument = async (id: string) => {
    try {
      await documentApi.downloadDocument(id)
      message.success('文档下载中')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '下载文档失败')
    }
  }

  const handleTagFilter = (tag: string | undefined) => {
    setTagFilter(tag)
    // 重新获取文档列表时会自动应用标签筛选
  }

  const handleDeleteFolder = async (id: string, name: string) => {
    const confirmText = `我确认删除${name}文件夹`
    
    return new Promise<void>((resolve, reject) => {
      let inputValue = ''
      Modal.confirm({
        title: '确认删除文件夹',
        content: (
          <div>
            <p>删除文件夹将同时删除其中的所有文档和子文件夹。</p>
            <p>请输入确认文字：<strong>{confirmText}</strong></p>
            <Input
              placeholder={confirmText}
              style={{ marginTop: 8 }}
              onChange={(e) => {
                inputValue = e.target.value
              }}
            />
          </div>
        ),
        okText: '确认删除',
        okButtonProps: { danger: true },
        onOk: async () => {
          if (inputValue !== confirmText) {
            message.error('确认文字不正确')
            reject(new Error('确认文字不正确'))
            return
          }
          try {
            await documentApi.deleteFolder(id, confirmText)
            message.success('删除成功')
            if (currentFolderId === id) {
              setCurrentFolderId(null)
            }
            await refreshFolders()
            fetchDocuments()
            resolve()
          } catch (error: any) {
            message.error(error.response?.data?.detail || '删除失败')
            reject(error)
          }
        },
        onCancel: () => {
          reject(new Error('取消删除'))
        },
      })
    })
  }

  const handleViewDetail = async (id: string) => {
    try {
      const detail = await documentApi.getDocument(id)
      setSelectedDocument(detail)
      setDetailModalVisible(true)
      // 获取文档标签
      const docTags = await documentApi.getDocumentTags(id)
      setDocumentTags(docTags)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取详情失败')
    }
  }

  const handleManageTags = (id: string) => {
    setSelectedDocumentId(id)
    setTagModalVisible(true)
    // 获取文档标签
    documentApi.getDocumentTags(id).then((docTags) => {
      setDocumentTags(docTags)
    })
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      uploading: { color: 'processing', text: '上传中' },
      uploaded: { color: 'default', text: '已上传' },
      parsing: { color: 'processing', text: '解析中' },
      vectorizing: { color: 'processing', text: '向量化中' },
      completed: { color: 'success', text: '已完成' },
      upload_failed: { color: 'error', text: '上传失败' },
      parse_failed: { color: 'error', text: '解析失败' },
      vectorize_failed: { color: 'error', text: '向量化失败' },
      uploading: { color: 'processing', text: '上传中' },
      uploaded: { color: 'default', text: '已上传' },
      parsing: { color: 'processing', text: '解析中' },
      completed: { color: 'success', text: '已完成' },
      upload_failed: { color: 'error', text: '上传失败' },
      parse_failed: { color: 'error', text: '解析失败' },
    }
    const config = statusMap[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  const columns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Document) => (
        <Space>
          <FileOutlined />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string | null) => text || '-',
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '页数',
      dataIndex: 'page_count',
      key: 'page_count',
      render: (count: number | null) => count || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Document) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<TagOutlined />}
            onClick={() => handleManageTags(record.id)}
          >
            标签
          </Button>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadDocument(record.id)}
          >
            下载
          </Button>
          <Popconfirm
            title="确定要删除这个文档吗？"
            onConfirm={() => handleDeleteDocument(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 构建文件夹树结构
  const buildFolderTree = (parentId: string | null = null): DataNode[] => {
    return allFolders
      .filter((folder) => folder.parent_id === parentId)
      .map((folder) => {
        const children = buildFolderTree(folder.id)
        return {
          title: (
            <Space>
              <FolderOutlined />
              <span
                onClick={() => setCurrentFolderId(folder.id)}
                style={{ cursor: 'pointer', flex: 1 }}
              >
                {folder.name}
              </span>
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteFolder(folder.id, folder.name)
                }}
              />
            </Space>
          ),
          key: folder.id,
          children: children.length > 0 ? children : undefined,
          isLeaf: folder.level >= 1, // 最多2层（根目录/1级），level 1不能再建子文件夹
        }
      })
  }

  const folderTreeData: DataNode[] = buildFolderTree()

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setFolderModalVisible(true)}
              disabled={!canCreateSubFolder()}
            >
              新建文件夹
            </Button>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传文档
            </Button>
          </Space>
        </Space>

        <div style={{ display: 'flex', gap: 16 }}>
          <div style={{ width: 300, border: '1px solid #d9d9d9', borderRadius: 4, padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3 style={{ margin: 0 }}>文件夹</h3>
              <Button
                type="link"
                size="small"
                onClick={() => setCurrentFolderId(null)}
                style={{ padding: 0 }}
              >
                全部
              </Button>
            </div>
            <Tree
              treeData={folderTreeData}
              expandedKeys={expandedKeys}
              onExpand={setExpandedKeys}
              onSelect={(selectedKeys) => {
                if (selectedKeys.length > 0) {
                  const folderId = selectedKeys[0] as string
                  setCurrentFolderId(folderId)
                  // 自动展开选中的文件夹
                  if (!expandedKeys.includes(folderId)) {
                    setExpandedKeys([...expandedKeys, folderId])
                  }
                } else {
                  setCurrentFolderId(null)
                }
              }}
              selectedKeys={currentFolderId ? [currentFolderId] : []}
            />
          </div>

          <div style={{ flex: 1 }}>
            <Table
              columns={columns}
              dataSource={documents}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 条`,
              }}
            />
          </div>
        </div>
      </Card>

      {/* 上传文档弹窗 */}
      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => {
          setUploadModalVisible(false)
          uploadForm.resetFields()
        }}
        onOk={() => uploadForm.submit()}
        width={600}
      >
        <Form
          form={uploadForm}
          onFinish={handleUpload}
          layout="vertical"
        >
          <Form.Item
            name="file"
            label="选择文件"
            valuePropName="fileList"
            getValueFromEvent={(e) => {
              if (Array.isArray(e)) {
                return e
              }
              return e?.fileList
            }}
            rules={[{ required: true, message: '请选择文件' }]}
          >
            <Upload
              beforeUpload={() => false}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>

          <Form.Item label="文本切分配置（可选）">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Form.Item name="chunk_size" label="切分块大小">
                <InputNumber min={1} max={5000} style={{ width: '100%' }} placeholder="默认400" />
              </Form.Item>
              <Form.Item name="chunk_overlap" label="重叠大小">
                <InputNumber min={0} max={4000} style={{ width: '100%' }} placeholder="默认100" />
              </Form.Item>
              <Form.Item name="split_method" label="切分方法">
                <Select placeholder="默认length">
                  <Select.Option value="length">按长度切分</Select.Option>
                  <Select.Option value="paragraph">按段落切分</Select.Option>
                  <Select.Option value="keyword">按关键字切分</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.split_method !== currentValues.split_method
                }
              >
                {({ getFieldValue }) => {
                  const splitMethod = getFieldValue('split_method')
                  if (splitMethod === 'keyword') {
                    return (
                      <Form.Item
                        name="split_keyword"
                        label="切分关键字"
                        rules={[
                          {
                            required: true,
                            message: '当切分方法为关键字时，请输入切分关键字',
                          },
                        ]}
                      >
                        <Input placeholder="输入关键字" />
                      </Form.Item>
                    )
                  }
                  return null
                }}
              </Form.Item>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建文件夹弹窗 */}
      <Modal
        title="创建文件夹"
        open={folderModalVisible}
        onCancel={() => {
          setFolderModalVisible(false)
          folderForm.resetFields()
        }}
        onOk={() => folderForm.submit()}
      >
        <Form form={folderForm} onFinish={handleCreateFolder} layout="vertical">
          <Form.Item
            name="name"
            label="文件夹名称"
            rules={[{ required: true, message: '请输入文件夹名称' }]}
          >
            <Input placeholder="请输入文件夹名称" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 文档详情弹窗 */}
      <Modal
        title="文档详情"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false)
          setSelectedDocument(null)
        }}
        footer={null}
        width={800}
      >
        {selectedDocument && (
          <div>
            <p><strong>文件名：</strong>{selectedDocument.name}</p>
            <p><strong>原始文件名：</strong>{selectedDocument.original_name}</p>
            <p><strong>文件类型：</strong>{selectedDocument.file_type}</p>
            <p><strong>文件大小：</strong>{formatFileSize(selectedDocument.file_size)}</p>
            <p><strong>状态：</strong>{getStatusTag(selectedDocument.status)}</p>
            <p><strong>版本：</strong>{selectedDocument.version}</p>
            {selectedDocument.title && <p><strong>标题：</strong>{selectedDocument.title}</p>}
            {selectedDocument.summary && (
              <p><strong>摘要：</strong>{selectedDocument.summary}</p>
            )}
            {selectedDocument.config && (
              <div>
                <p><strong>文本切分配置：</strong></p>
                <ul>
                  <li>切分块大小：{selectedDocument.config.chunk_size}</li>
                  <li>重叠大小：{selectedDocument.config.chunk_overlap}</li>
                  <li>切分方法：{selectedDocument.config.split_method}</li>
                  {selectedDocument.config.split_keyword && (
                    <li>切分关键字：{selectedDocument.config.split_keyword}</li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* 标签管理弹窗 */}
      <Modal
        title="管理标签"
        open={tagModalVisible}
        onCancel={() => {
          setTagModalVisible(false)
          setSelectedDocumentId(null)
          setDocumentTags([])
        }}
        onOk={() => {
          setTagModalVisible(false)
        }}
      >
        {selectedDocumentId && (
          <TagManager
            documentId={selectedDocumentId}
            tags={tags}
            documentTags={documentTags}
            onTagsChange={(newTags) => {
              setDocumentTags(newTags)
            }}
            onTagsListChange={() => {
              fetchTags()
            }}
          />
        )}
      </Modal>
    </div>
  )
}

// 标签管理组件
const TagManager = ({
  documentId,
  tags,
  documentTags,
  onTagsChange,
  onTagsListChange,
}: {
  documentId: string
  tags: DocumentTag[]
  documentTags: DocumentTag[]
  onTagsChange: (tags: DocumentTag[]) => void
  onTagsListChange?: () => void
}) => {
  const [newTagName, setNewTagName] = useState('')
  const [searchValue, setSearchValue] = useState('')

  const filteredTags = tags.filter((tag) =>
    tag.name.toLowerCase().includes(searchValue.toLowerCase())
  )

  const handleAddTag = async (tagId: string) => {
    try {
      await documentApi.addTagToDocument(documentId, tagId)
      message.success('标签已添加')
      const updatedTags = await documentApi.getDocumentTags(documentId)
      onTagsChange(updatedTags)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '添加标签失败')
    }
  }

  const handleRemoveTag = async (tagId: string) => {
    try {
      await documentApi.removeTagFromDocument(documentId, tagId)
      message.success('标签已移除')
      const updatedTags = await documentApi.getDocumentTags(documentId)
      onTagsChange(updatedTags)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '移除标签失败')
    }
  }

  const handleCreateTag = async () => {
    if (!newTagName.trim()) {
      message.error('请输入标签名称')
      return
    }
    if (newTagName.length > 20) {
      message.error('标签名称不能超过20个字符')
      return
    }

    try {
      // 查找现有标签
      const existingTag = tags.find((t) => t.name === newTagName.trim())
      if (existingTag) {
        // 如果标签已存在，直接添加
        await handleAddTag(existingTag.id)
      } else {
        // 创建新标签（通过添加标签接口，使用tag_name）
        await documentApi.addTagToDocument(documentId, undefined, newTagName.trim())
        message.success('标签已创建并添加')
        // 刷新标签列表和文档标签
        if (onTagsListChange) {
          onTagsListChange()
        }
        const updatedDocumentTags = await documentApi.getDocumentTags(documentId)
        onTagsChange(updatedDocumentTags)
      }
      setNewTagName('')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建标签失败')
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h4>当前标签</h4>
        <Space wrap>
          {documentTags.map((tag) => (
            <Tag
              key={tag.id}
              closable
              onClose={() => handleRemoveTag(tag.id)}
            >
              {tag.name}
            </Tag>
          ))}
          {documentTags.length === 0 && <span style={{ color: '#999' }}>暂无标签</span>}
        </Space>
      </div>

      <div>
        <h4>添加标签</h4>
        <Search
          placeholder="搜索标签"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          style={{ marginBottom: 8 }}
        />
        <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 8 }}>
          {filteredTags
            .filter((tag) => !documentTags.some((dt) => dt.id === tag.id))
            .map((tag) => (
              <Tag
                key={tag.id}
                style={{ cursor: 'pointer', marginBottom: 4 }}
                onClick={() => handleAddTag(tag.id)}
              >
                + {tag.name}
              </Tag>
            ))}
        </div>
        <Space>
          <Input
            placeholder="输入新标签名称（20字以内）"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            maxLength={20}
            style={{ width: 200 }}
          />
          <Button onClick={handleCreateTag}>创建并添加</Button>
        </Space>
      </div>
    </div>
  )
}

export default DocumentList

