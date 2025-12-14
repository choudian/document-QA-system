import { useState, useEffect, useRef } from 'react'
import {
  Layout,
  Card,
  Input,
  Button,
  List,
  Avatar,
  Space,
  Typography,
  Spin,
  Empty,
  Modal,
  Form,
  Select,
  InputNumber,
  Switch,
  Tag,
  Popconfirm,
  message,
  Divider,
} from 'antd'
import {
  SendOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  MessageOutlined,
  RobotOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { qaApi, Conversation, Message, ChatRequest } from '@/api/qa'
import { documentApi, Folder } from '@/api/documents'
import dayjs from 'dayjs'

const { Content, Sider } = Layout
const { TextArea } = Input
const { Title, Text, Paragraph } = Typography

const QAPage = () => {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [query, setQuery] = useState('')
  const [folders, setFolders] = useState<Folder[]>([])
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<string[]>([])
  
  const [conversationModalVisible, setConversationModalVisible] = useState(false)
  const [conversationForm] = Form.useForm()
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const [configForm] = Form.useForm()
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [streamingContent, setStreamingContent] = useState('')

  // 加载会话列表
  useEffect(() => {
    fetchConversations()
    fetchFolders()
  }, [])

  // 加载当前会话的消息
  useEffect(() => {
    if (currentConversation) {
      fetchMessages(currentConversation.id)
    } else {
      setMessages([])
    }
  }, [currentConversation])

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const fetchConversations = async () => {
    try {
      setLoading(true)
      const data = await qaApi.getConversations('active')
      setConversations(data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取会话列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchMessages = async (conversationId: string) => {
    try {
      setLoading(true)
      const data = await qaApi.getMessages(conversationId)
      setMessages(data.messages)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取消息列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchFolders = async () => {
    try {
      const data = await documentApi.getFolders()
      setFolders(data)
    } catch (error: any) {
      // 忽略错误
    }
  }

  const handleCreateConversation = async () => {
    try {
      const values = await conversationForm.validateFields()
      const conversation = await qaApi.createConversation({
        title: values.title,
        knowledge_base_ids: values.knowledge_base_ids,
        top_k: values.top_k,
        similarity_threshold: values.similarity_threshold,
        use_rerank: values.use_rerank,
        rerank_top_n: values.rerank_top_n,
      })
      setConversations([conversation, ...conversations])
      setCurrentConversation(conversation)
      setConversationModalVisible(false)
      conversationForm.resetFields()
      message.success('会话创建成功')
    } catch (error: any) {
      if (error.errorFields) {
        return // 表单验证错误
      }
      message.error(error.response?.data?.detail || '创建会话失败')
    }
  }

  const handleSelectConversation = async (conversation: Conversation) => {
    setCurrentConversation(conversation)
    setStreamingContent('')
  }

  const handleSendMessage = async () => {
    if (!query.trim() || !currentConversation) {
      return
    }

    const userMessage = query
    setQuery('')
    setSending(true)
    setStreamingContent('')

    // 添加用户消息到列表（临时显示）
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversation.id,
      role: 'user',
      content: userMessage,
      references: null,
      prompt_tokens: null,
      completion_tokens: null,
      total_tokens: null,
      sequence: messages.length + 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    setMessages([...messages, tempUserMessage])

    try {
      // 使用流式接口
      let fullContent = ''
      let references: any[] = []

      await qaApi.chatStream(
        currentConversation.id,
        {
          query: userMessage,
          knowledge_base_ids: selectedKnowledgeBases.length > 0 ? selectedKnowledgeBases : undefined,
        },
        (chunk: string) => {
          try {
            const data = JSON.parse(chunk)
            
            // 处理引用信息
            if (data.type === 'references' && data.references) {
              references = data.references
              return
            }

            // 处理流式内容
            if (data.choices && data.choices[0]?.delta?.content) {
              fullContent += data.choices[0].delta.content
              setStreamingContent(fullContent)
            }
          } catch (e) {
            // 忽略解析错误
          }
        },
        async () => {
          // 流式完成，保存消息
          const tempAssistantMessage: Message = {
            id: `temp-assistant-${Date.now()}`,
            conversation_id: currentConversation.id,
            role: 'assistant',
            content: fullContent,
            references: references,
            prompt_tokens: null,
            completion_tokens: null,
            total_tokens: null,
            sequence: messages.length + 2,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          setMessages([...messages, tempUserMessage, tempAssistantMessage])
          setStreamingContent('')
          
          // 重新获取消息列表（获取真实的消息ID）
          await fetchMessages(currentConversation.id)
        },
        (error: Error) => {
          message.error(error.message || '发送消息失败')
          setSending(false)
          setStreamingContent('')
        }
      )
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发送消息失败')
    } finally {
      setSending(false)
    }
  }

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await qaApi.deleteConversation(conversationId)
      setConversations(conversations.filter(c => c.id !== conversationId))
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null)
        setMessages([])
      }
      message.success('删除成功')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleUpdateConfig = async () => {
    if (!currentConversation) return

    try {
      const values = await configForm.validateFields()
      const updated = await qaApi.updateConversation(currentConversation.id, {
        knowledge_base_ids: values.knowledge_base_ids,
        top_k: values.top_k,
        similarity_threshold: values.similarity_threshold,
        use_rerank: values.use_rerank,
        rerank_top_n: values.rerank_top_n,
      })
      setCurrentConversation(updated)
      setConfigModalVisible(false)
      message.success('配置更新成功')
    } catch (error: any) {
      if (error.errorFields) {
        return
      }
      message.error(error.response?.data?.detail || '更新配置失败')
    }
  }

  const buildFolderTree = (folders: Folder[], parentId: string | null = null): any[] => {
    return folders
      .filter(f => f.parent_id === parentId)
      .map(folder => ({
        label: folder.name,
        value: folder.id,
        key: folder.id,
        children: buildFolderTree(folders, folder.id),
      }))
  }

  return (
    <Layout style={{ height: 'calc(100vh - 48px)' }}>
      <Sider width={300} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={async () => {
              // 确保文件夹列表已加载
              if (folders.length === 0) {
                await fetchFolders()
              }
              conversationForm.resetFields()
              setConversationModalVisible(true)
            }}
          >
            新建会话
          </Button>
        </div>
        <List
          dataSource={conversations}
          loading={loading}
          style={{ height: 'calc(100vh - 120px)', overflow: 'auto' }}
          renderItem={(conversation) => (
            <List.Item
              style={{
                cursor: 'pointer',
                backgroundColor: currentConversation?.id === conversation.id ? '#e6f7ff' : 'transparent',
              }}
              onClick={() => handleSelectConversation(conversation)}
              actions={[
                <Popconfirm
                  title="确定删除这个会话吗？"
                  onConfirm={() => handleDeleteConversation(conversation.id)}
                  key="delete"
                >
                  <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar icon={<MessageOutlined />} />}
                title={conversation.title || '新会话'}
                description={dayjs(conversation.updated_at).format('YYYY-MM-DD HH:mm')}
              />
            </List.Item>
          )}
        />
      </Sider>

      <Content style={{ display: 'flex', flexDirection: 'column', background: '#fff' }}>
        {currentConversation ? (
          <>
            <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={4} style={{ margin: 0 }}>
                {currentConversation.title || '新会话'}
              </Title>
              <Button
                icon={<EditOutlined />}
                onClick={async () => {
                  // 确保文件夹列表已加载
                  if (folders.length === 0) {
                    await fetchFolders()
                  }
                  configForm.setFieldsValue({
                    knowledge_base_ids: currentConversation.config?.knowledge_base_ids || [],
                    top_k: currentConversation.config?.top_k || 5,
                    similarity_threshold: currentConversation.config?.similarity_threshold,
                    use_rerank: currentConversation.config?.use_rerank || false,
                    rerank_top_n: currentConversation.config?.rerank_top_n,
                  })
                  setConfigModalVisible(true)
                }}
              >
                配置
              </Button>
            </div>

            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
              {messages.length === 0 && !streamingContent && (
                <Empty description="开始对话吧" />
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    marginBottom: '16px',
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <Card
                    style={{
                      maxWidth: '70%',
                      backgroundColor: msg.role === 'user' ? '#1890ff' : '#f5f5f5',
                      color: msg.role === 'user' ? '#fff' : '#000',
                    }}
                    size="small"
                  >
                    <Space>
                      <Avatar
                        icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                        style={{
                          backgroundColor: msg.role === 'user' ? '#fff' : '#1890ff',
                          color: msg.role === 'user' ? '#1890ff' : '#fff',
                        }}
                      />
                      <div>
                        <Paragraph
                          style={{
                            margin: 0,
                            color: msg.role === 'user' ? '#fff' : '#000',
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {msg.content}
                        </Paragraph>
                        {msg.references && msg.references.length > 0 && (
                          <div style={{ marginTop: '8px', fontSize: '12px', opacity: 0.8 }}>
                            <Text strong>引用来源：</Text>
                            {msg.references.map((ref, idx) => {
                              // 尝试从多个位置获取文档名称
                              // 优先使用metadata中的文档信息
                              const docName = 
                                (ref.metadata && ref.metadata.document_name) || 
                                (ref.metadata && ref.metadata.document_original_name) || 
                                (ref.metadata && ref.metadata.document_title) ||
                                ref.document_id
                              return (
                                <Tag key={idx} style={{ marginTop: '4px' }}>
                                  {docName} (相似度: {(ref.similarity * 100).toFixed(1)}%)
                                </Tag>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    </Space>
                  </Card>
                </div>
              ))}
              {streamingContent && (
                <div
                  style={{
                    marginBottom: '16px',
                    display: 'flex',
                    justifyContent: 'flex-start',
                  }}
                >
                  <Card style={{ maxWidth: '70%', backgroundColor: '#f5f5f5' }} size="small">
                    <Space>
                      <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
                      <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {streamingContent}
                        <Spin size="small" style={{ marginLeft: '8px' }} />
                      </Paragraph>
                    </Space>
                  </Card>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0' }}>
              <Space.Compact style={{ width: '100%' }}>
                <TextArea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onPressEnter={(e) => {
                    if (!e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="输入问题... (Shift+Enter 换行)"
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  disabled={sending}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  loading={sending}
                  onClick={handleSendMessage}
                  disabled={!query.trim()}
                >
                  发送
                </Button>
              </Space.Compact>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Empty description="选择一个会话或创建新会话开始对话" />
          </div>
        )}
      </Content>

      {/* 创建会话弹窗 */}
      <Modal
        title="创建会话"
        open={conversationModalVisible}
        onOk={handleCreateConversation}
        onCancel={() => {
          setConversationModalVisible(false)
          conversationForm.resetFields()
        }}
      >
        <Form form={conversationForm} layout="vertical">
          <Form.Item name="title" label="会话标题（可选）">
            <Input placeholder="留空将使用第一条消息作为标题" />
          </Form.Item>
          <Form.Item name="knowledge_base_ids" label="知识库（文件夹）">
            <Select
              mode="multiple"
              placeholder="选择知识库，留空则搜索所有文档"
              options={buildFolderTree(folders)}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
          <Form.Item name="top_k" label="Top K" initialValue={5}>
            <InputNumber min={1} max={200} />
          </Form.Item>
          <Form.Item name="similarity_threshold" label="相似度阈值">
            <InputNumber min={0} max={1} step={0.1} />
          </Form.Item>
          <Form.Item name="use_rerank" label="使用重排序" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.use_rerank !== currentValues.use_rerank}
          >
            {({ getFieldValue }) =>
              getFieldValue('use_rerank') ? (
                <Form.Item name="rerank_top_n" label="重排序 Top N">
                  <InputNumber min={1} max={50} />
                </Form.Item>
              ) : null
            }
          </Form.Item>
        </Form>
      </Modal>

      {/* 配置弹窗 */}
      <Modal
        title="会话配置"
        open={configModalVisible}
        onOk={handleUpdateConfig}
        onCancel={() => {
          setConfigModalVisible(false)
          configForm.resetFields()
        }}
      >
        <Form form={configForm} layout="vertical">
          <Form.Item name="knowledge_base_ids" label="知识库（文件夹）">
            <Select
              mode="multiple"
              placeholder="选择知识库，留空则搜索所有文档"
              options={buildFolderTree(folders)}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            />
          </Form.Item>
          <Form.Item name="top_k" label="Top K">
            <InputNumber min={1} max={200} />
          </Form.Item>
          <Form.Item name="similarity_threshold" label="相似度阈值">
            <InputNumber min={0} max={1} step={0.1} />
          </Form.Item>
          <Form.Item name="use_rerank" label="使用重排序" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.use_rerank !== currentValues.use_rerank}
          >
            {({ getFieldValue }) =>
              getFieldValue('use_rerank') ? (
                <Form.Item name="rerank_top_n" label="重排序 Top N">
                  <InputNumber min={1} max={50} />
                </Form.Item>
              ) : null
            }
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  )
}

export default QAPage
