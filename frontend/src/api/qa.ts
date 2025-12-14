import client from './client'

export interface Conversation {
  id: string
  tenant_id: string
  user_id: string
  title: string | null
  status: string
  config: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  conversation_id: string
  role: string
  content: string
  references: Array<{
    document_id: string
    chunk_index: number
    content: string
    similarity: number
    metadata?: any
  }> | null
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  sequence: number
  created_at: string
  updated_at: string
}

export interface ChatRequest {
  query: string
  knowledge_base_ids?: string[]
  top_k?: number
  similarity_threshold?: number
  use_rerank?: boolean
  rerank_top_n?: number
}

export interface ChatResponse {
  message_id: string
  content: string
  references: Array<{
    document_id: string
    chunk_index: number
    content: string
    similarity: number
    metadata?: any
  }>
  usage: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
}

export const qaApi = {
  // 会话管理
  async getConversations(status?: string): Promise<Conversation[]> {
    const params = status ? { status_filter: status } : {}
    const response = await client.get('/qa/conversations', { params })
    return response.data
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await client.get(`/qa/conversations/${conversationId}`)
    return response.data
  },

  async createConversation(data: {
    title?: string
    knowledge_base_ids?: string[]
    top_k?: number
    similarity_threshold?: number
    use_rerank?: boolean
    rerank_top_n?: number
  }): Promise<Conversation> {
    const response = await client.post('/qa/conversations', data)
    return response.data
  },

  async updateConversation(
    conversationId: string,
    data: {
      title?: string
      knowledge_base_ids?: string[]
      top_k?: number
      similarity_threshold?: number
      use_rerank?: boolean
      rerank_top_n?: number
    }
  ): Promise<Conversation> {
    const response = await client.put(`/qa/conversations/${conversationId}`, data)
    return response.data
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await client.delete(`/qa/conversations/${conversationId}`)
  },

  async archiveConversation(conversationId: string): Promise<Conversation> {
    const response = await client.post(`/qa/conversations/${conversationId}/archive`)
    return response.data
  },

  // 消息管理
  async getMessages(conversationId: string, skip = 0, limit = 100): Promise<{
    messages: Message[]
    total: number
  }> {
    const response = await client.get(`/qa/conversations/${conversationId}/messages`, {
      params: { skip, limit }
    })
    return response.data
  },

  async getMessage(messageId: string): Promise<Message> {
    const response = await client.get(`/qa/messages/${messageId}`)
    return response.data
  },

  async deleteMessage(messageId: string): Promise<void> {
    await client.delete(`/qa/messages/${messageId}`)
  },

  // 对话
  async chat(conversationId: string, data: ChatRequest): Promise<ChatResponse> {
    const response = await client.post(`/qa/conversations/${conversationId}/chat`, data)
    return response.data
  },

  async chatStream(
    conversationId: string,
    data: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete?: () => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    try {
      const token = localStorage.getItem('token')
      const baseURL = client.defaults.baseURL || '/api/v1'
      const url = `${baseURL}/qa/conversations/${conversationId}/chat/stream`
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP error! status: ${response.status}, ${errorText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        
        // 保留最后一个不完整的行
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            const dataStr = line.trim().slice(6)
            if (dataStr === '[DONE]') {
              onComplete?.()
              return
            }
            if (dataStr) {
              onChunk(dataStr)
            }
          }
        }
      }
      
      // 处理剩余的buffer
      if (buffer.trim().startsWith('data: ')) {
        const dataStr = buffer.trim().slice(6)
        if (dataStr && dataStr !== '[DONE]') {
          onChunk(dataStr)
        }
      }
      
      onComplete?.()
    } catch (error) {
      onError?.(error as Error)
    }
  }
}
