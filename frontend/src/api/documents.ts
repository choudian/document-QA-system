import client from './client'

export interface Folder {
  id: string
  tenant_id: string
  user_id: string
  parent_id: string | null
  name: string
  path: string
  level: number
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  name: string
  original_name: string
  file_type: string
  file_size: number
  status: string
  title: string | null
  page_count: number | null
  folder_id: string | null
  created_at: string
  updated_at: string
}

export interface DocumentDetail extends Document {
  tenant_id: string
  user_id: string
  mime_type: string
  file_hash: string
  version: string
  summary: string | null
  config?: DocumentConfig
}

export interface DocumentConfig {
  chunk_size: number
  chunk_overlap: number
  split_method: string
  split_keyword: string | null
}

export interface DocumentVersion {
  id: string
  document_id: string
  version: string
  operator_id: string
  remark: string | null
  is_current: boolean
  created_at: string
}

export interface Tag {
  id: string
  name: string
  created_at: string
}

export interface FolderCreate {
  name: string
  parent_id?: string | null
}

export interface FolderUpdate {
  name: string
}

export interface DocumentUploadRequest {
  folder_id?: string | null
  chunk_size?: number
  chunk_overlap?: number
  split_method?: string
  split_keyword?: string | null
}

export interface CheckDuplicateRequest {
  filename: string
  folder_id?: string | null
}

export interface CheckDuplicateResponse {
  exists: boolean
  document_id?: string
  version?: string
}

export const documentApi = {
  // 文件夹相关
  // 创建文件夹
  createFolder: async (data: FolderCreate) => {
    const response = await client.post<Folder>('/documents/folders', data)
    return response.data
  },

  // 获取文件夹列表
  getFolders: async (parentId?: string | null) => {
    const response = await client.get<Folder[]>('/documents/folders', {
      params: { parent_id: parentId },
    })
    return response.data
  },

  // 获取文件夹详情
  getFolder: async (id: string) => {
    const response = await client.get<Folder>(`/documents/folders/${id}`)
    return response.data
  },

  // 更新文件夹（重命名）
  updateFolder: async (id: string, data: FolderUpdate) => {
    const response = await client.put<Folder>(`/documents/folders/${id}`, data)
    return response.data
  },

  // 删除文件夹
  deleteFolder: async (id: string, confirmText: string) => {
    const formData = new URLSearchParams()
    formData.append('confirm_text', confirmText)
    await client.delete(`/documents/folders/${id}`, {
      data: formData,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  // 文档相关
  // 检查同名文件
  checkDuplicate: async (data: CheckDuplicateRequest) => {
    const response = await client.post<CheckDuplicateResponse>('/documents/check-duplicate', data)
    return response.data
  },

  // 上传文档
  uploadDocument: async (file: File, config?: DocumentUploadRequest) => {
    const formData = new FormData()
    formData.append('file', file)
    if (config) {
      if (config.folder_id) formData.append('folder_id', config.folder_id)
      if (config.chunk_size) formData.append('chunk_size', config.chunk_size.toString())
      if (config.chunk_overlap) formData.append('chunk_overlap', config.chunk_overlap.toString())
      if (config.split_method) formData.append('split_method', config.split_method)
      if (config.split_keyword) formData.append('split_keyword', config.split_keyword)
    }

    const response = await client.post<Document>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // 获取文档列表（兼容旧接口名）
  getDocuments: async (params?: {
    folder_id?: string | null
    status?: string
    tag?: string
    skip?: number
    limit?: number
  }) => {
    const response = await client.get<Document[]>('/documents', { params })
    return response.data
  },

  // 获取文档列表（新接口名，支持标签筛选）
  listDocuments: async (params?: {
    folder_id?: string | null
    status?: string
    tag?: string
    skip?: number
    limit?: number
  }) => {
    const response = await client.get<Document[]>('/documents', { params })
    return response.data
  },

  // 获取文档详情
  getDocument: async (id: string) => {
    const response = await client.get<DocumentDetail>(`/documents/${id}`)
    return response.data
  },

  // 删除文档
  deleteDocument: async (id: string) => {
    await client.delete(`/documents/${id}`)
  },

  // 获取文档版本历史
  getDocumentVersions: async (id: string) => {
    const response = await client.get<DocumentVersion[]>(`/documents/${id}/versions`)
    return response.data
  },

  // 标签相关
  // 获取标签列表（用于自动补全）
  getTags: async (search?: string) => {
    const response = await client.get<Tag[]>('/documents/tags', {
      params: { search },
    })
    return response.data
  },

  // 为文档添加标签（支持tagId或tagName）
  addTagToDocument: async (documentId: string, tagId?: string, tagName?: string) => {
    const payload: any = {}
    if (tagId) {
      payload.tag_id = tagId
    } else if (tagName) {
      payload.tag_name = tagName
    } else {
      throw new Error('必须提供tagId或tagName')
    }
    await client.post(`/documents/${documentId}/tags`, payload)
  },

  // 从文档移除标签
  removeTagFromDocument: async (documentId: string, tagId: string) => {
    await client.delete(`/documents/${documentId}/tags/${tagId}`)
  },

  // 获取文档的所有标签
  getDocumentTags: async (documentId: string) => {
    const response = await client.get<{ tags: Tag[] }>(`/documents/${documentId}/tags`)
    return response.data.tags
  },

  // 删除文档
  deleteDocument: async (documentId: string) => {
    await client.delete(`/documents/${documentId}`)
  },

  // 恢复文档
  restoreDocument: async (documentId: string) => {
    const response = await client.post<DocumentDetail>(`/documents/${documentId}/restore`)
    return response.data
  },

  // 获取回收站文档列表
  getTrashDocuments: async (skip = 0, limit = 100) => {
    const response = await client.get<Document[]>(`/documents/trash`, {
      params: { skip, limit },
    })
    return response.data
  },

  // 获取文档版本历史
  getDocumentVersions: async (documentId: string) => {
    const response = await client.get<DocumentVersion[]>(`/documents/${documentId}/versions`)
    return response.data
  },

  // 删除文档版本
  deleteDocumentVersion: async (documentId: string, versionId: string) => {
    await client.delete(`/documents/${documentId}/versions/${versionId}`)
  },

  // 下载文档
  downloadDocument: async (documentId: string) => {
    const response = await client.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    })
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    // 从Content-Disposition头获取文件名，如果没有则使用documentId
    const contentDisposition = response.headers['content-disposition']
    let filename = documentId
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  // 获取最近使用的配置
  getRecentConfig: async () => {
    const response = await client.get<DocumentConfig>(`/documents/config/recent`)
    return response.data
  },
}

