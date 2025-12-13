import { useState, useEffect } from 'react'
import {
  Table,
  Card,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Descriptions,
  Typography,
} from 'antd'
import { SearchOutlined, EyeOutlined } from '@ant-design/icons'
import { auditApi, AuditLog, AuditLogQueryParams } from '@/api/audit'
import { useCurrentUser } from '@/hooks/useCurrentUser'
import dayjs, { Dayjs } from 'dayjs'

const { Option } = Select
const { Text, Paragraph } = Typography
const { RangePicker } = DatePicker

const AuditLogPage = () => {
  const [form] = Form.useForm()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)
  const currentUser = useCurrentUser()

  const fetchLogs = async (params?: AuditLogQueryParams) => {
    setLoading(true)
    try {
      const queryParams: AuditLogQueryParams = {
        page,
        page_size: pageSize,
        ...params,
      }
      
      // 租户管理员只能查看自己租户的日志
      if (currentUser?.is_tenant_admin && !currentUser?.is_system_admin) {
        queryParams.tenant_id = currentUser.tenant_id
      }
      
      const data = await auditApi.getList(queryParams)
      setLogs(data.items || [])
      setTotal(data.total || 0)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取审计日志失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, currentUser])

  const handleSearch = () => {
    const values = form.getFieldsValue()
    const params: AuditLogQueryParams = {}
    
    if (values.method) {
      params.method = values.method
    }
    if (values.path) {
      params.path = values.path
    }
    if (values.user_id) {
      params.user_id = values.user_id
    }
    if (values.tenant_id && currentUser?.is_system_admin) {
      params.tenant_id = values.tenant_id
    }
    if (values.timeRange && values.timeRange.length === 2) {
      params.start_time = values.timeRange[0].toISOString()
      params.end_time = values.timeRange[1].toISOString()
    }
    
    setPage(1)
    fetchLogs(params)
  }

  const handleReset = () => {
    form.resetFields()
    setPage(1)
    fetchLogs()
  }

  const handleViewDetail = async (log: AuditLog) => {
    try {
      const detail = await auditApi.getById(log.id)
      setSelectedLog(detail)
      setDetailModalVisible(true)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取日志详情失败')
    }
  }

  const getStatusColor = (status: number) => {
    if (status >= 200 && status < 300) return 'green'
    if (status >= 400 && status < 500) return 'orange'
    if (status >= 500) return 'red'
    return 'default'
  }

  const getMethodColor = (method: string) => {
    const colors: Record<string, string> = {
      GET: 'blue',
      POST: 'green',
      PUT: 'orange',
      DELETE: 'red',
      PATCH: 'purple',
    }
    return colors[method] || 'default'
  }

  const formatJson = (jsonStr: string | undefined) => {
    if (!jsonStr) return null
    try {
      const obj = JSON.parse(jsonStr)
      return JSON.stringify(obj, null, 2)
    } catch {
      return jsonStr
    }
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 80,
      render: (method: string) => (
        <Tag color={getMethodColor(method)}>{method}</Tag>
      ),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
    },
    {
      title: '状态码',
      dataIndex: 'response_status',
      key: 'response_status',
      width: 100,
      render: (status: number) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      ),
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (ms: number) => `${ms}ms`,
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      ellipsis: true,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 130,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: AuditLog) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record)}
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Card>
        <Form form={form} layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item name="method" label="HTTP方法">
            <Select placeholder="全部" allowClear style={{ width: 120 }}>
              <Option value="GET">GET</Option>
              <Option value="POST">POST</Option>
              <Option value="PUT">PUT</Option>
              <Option value="DELETE">DELETE</Option>
              <Option value="PATCH">PATCH</Option>
            </Select>
          </Form.Item>
          <Form.Item name="path" label="路径">
            <Input placeholder="路径关键字" style={{ width: 200 }} allowClear />
          </Form.Item>
          {currentUser?.is_system_admin && (
            <Form.Item name="tenant_id" label="租户ID">
              <Input placeholder="租户ID" style={{ width: 200 }} allowClear />
            </Form.Item>
          )}
          <Form.Item name="user_id" label="用户ID">
            <Input placeholder="用户ID" style={{ width: 200 }} allowClear />
          </Form.Item>
          <Form.Item name="timeRange" label="时间范围">
            <RangePicker
              showTime
              format="YYYY-MM-DD HH:mm:ss"
              style={{ width: 400 }}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                查询
              </Button>
              <Button onClick={handleReset}>重置</Button>
            </Space>
          </Form.Item>
        </Form>

        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPage(page)
              setPageSize(pageSize)
            },
          }}
        />
      </Card>

      <Modal
        title="审计日志详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedLog && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="日志ID">{selectedLog.id}</Descriptions.Item>
            <Descriptions.Item label="时间">
              {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="HTTP方法">
              <Tag color={getMethodColor(selectedLog.method)}>{selectedLog.method}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="请求路径">{selectedLog.path}</Descriptions.Item>
            <Descriptions.Item label="响应状态码">
              <Tag color={getStatusColor(selectedLog.response_status)}>
                {selectedLog.response_status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="耗时">{selectedLog.duration_ms}ms</Descriptions.Item>
            <Descriptions.Item label="用户ID">{selectedLog.user_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="租户ID">{selectedLog.tenant_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="IP地址">{selectedLog.ip_address || '-'}</Descriptions.Item>
            <Descriptions.Item label="User Agent">{selectedLog.user_agent || '-'}</Descriptions.Item>
            <Descriptions.Item label="请求大小">
              {selectedLog.request_size ? `${(selectedLog.request_size / 1024).toFixed(2)} KB` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="响应大小">
              {selectedLog.response_size ? `${(selectedLog.response_size / 1024).toFixed(2)} KB` : '-'}
            </Descriptions.Item>
            {selectedLog.query_params && (
              <Descriptions.Item label="查询参数">
                <Paragraph
                  copyable
                  style={{
                    margin: 0,
                    maxHeight: '150px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                  }}
                >
                  {formatJson(selectedLog.query_params) || selectedLog.query_params}
                </Paragraph>
              </Descriptions.Item>
            )}
            {selectedLog.request_body && (
              <Descriptions.Item label="请求体">
                <Paragraph
                  copyable
                  style={{
                    margin: 0,
                    maxHeight: '200px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                  }}
                >
                  {formatJson(selectedLog.request_body) || selectedLog.request_body}
                </Paragraph>
              </Descriptions.Item>
            )}
            {selectedLog.response_body && (
              <Descriptions.Item label="响应体">
                <Paragraph
                  copyable
                  style={{
                    margin: 0,
                    maxHeight: '300px',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                  }}
                >
                  {formatJson(selectedLog.response_body) || selectedLog.response_body}
                </Paragraph>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default AuditLogPage

