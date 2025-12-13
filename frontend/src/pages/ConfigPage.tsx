import { useEffect, useState } from 'react'
import { Card, Form, Input, InputNumber, Select, Checkbox, Button, message, Spin, Collapse, FormItemProps } from 'antd'
import { configApi, ConfigDefinitionItem, FieldDefinition } from '@/api/config'
import { meApi } from '@/api/me'

const { Option } = Select

type FormValues = Record<string, Record<string, any>>

const ConfigPage = () => {
  const [form] = Form.useForm<FormValues>()
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [definitions, setDefinitions] = useState<ConfigDefinitionItem[]>([])
  const [isSystemAdmin, setIsSystemAdmin] = useState(false)
  const [isTenantAdmin, setIsTenantAdmin] = useState(false)

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const user = await meApi.getMe()
      setIsSystemAdmin(user.is_system_admin || false)
      setIsTenantAdmin(user.is_tenant_admin || false)
    } catch (e: any) {
      message.error(e?.message || '获取用户信息失败')
    }
  }

  // 获取配置定义
  const fetchDefinitions = async () => {
    try {
      const res = await configApi.getDefinitions()
      setDefinitions(res.definitions || [])
    } catch (e: any) {
      message.error(e?.message || '获取配置定义失败')
    }
  }

  // 获取配置值
  const fetchConfig = async () => {
    if (definitions.length === 0) return
    
    setLoading(true)
    try {
      const res = await configApi.getMyConfig()
      const cfg = res.configs || {}
      
      // 构建表单值
      const formValues: FormValues = {}
      for (const def of definitions) {
        const categoryKey = def.category === 'doc' ? `${def.category}_${def.key}` : def.category
        const configValue = cfg[def.category]?.[def.key]
        if (configValue) {
          formValues[categoryKey] = configValue
        }
      }
      
      form.setFieldsValue(formValues)
    } catch (e: any) {
      message.error(e?.message || '获取配置失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUserInfo()
  }, [])

  useEffect(() => {
    fetchDefinitions()
  }, [])

  useEffect(() => {
    if (definitions.length > 0) {
      fetchConfig()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [definitions])

  // 构建提交的配置项
  const buildItems = (values: FormValues) => {
    const items: any[] = []

    for (const def of definitions) {
      const categoryKey = def.category === 'doc' ? `${def.category}_${def.key}` : def.category
      const value = values[categoryKey]
      
      // 对于租户管理员，即使配置值为空也要提交（用于删除租户级配置）
      // 对于系统管理员，只提交非空配置
      if (isTenantAdmin) {
        // 租户管理员：提交所有配置项，包括空值（用于删除）
        items.push({
          category: def.category,
          key: def.key,
          value: value || {},
          status: true,
        })
      } else {
        // 系统管理员：只提交非空配置项
        if (value && Object.keys(value).length > 0) {
          items.push({
            category: def.category,
            key: def.key,
            value,
            status: true,
          })
        }
      }
    }

    return items
  }

  const onFinish = async (values: FormValues) => {
    // 检查敏感字段是否被脱敏（包含多个连续星号，表示是脱敏后的值）
    for (const def of definitions) {
      const categoryKey = def.category === 'doc' ? `${def.category}_${def.key}` : def.category
      const configValue = values[categoryKey]
      
      if (configValue) {
        for (const field of def.fields) {
          if (field.sensitive && configValue[field.name]) {
            const val = configValue[field.name]
            // 检查是否包含多个连续星号（脱敏格式：前4个字符 + 星号 + 后4个字符）
            if (typeof val === 'string' && (val.includes('****') || /\*{4,}/.test(val))) {
              message.error(`${field.label || field.name} 已脱敏，请重新填写真实值后再保存`)
              return
            }
          }
        }
      }
    }

    const items = buildItems(values)
    setSubmitting(true)
    try {
      await configApi.updateConfig({ items })
      message.success('保存成功')
      fetchConfig()
    } catch (e: any) {
      message.error(e?.message || '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 渲染单个字段
  const renderField = (def: ConfigDefinitionItem, field: FieldDefinition) => {
    const categoryKey = def.category === 'doc' ? `${def.category}_${def.key}` : def.category
    const fieldName = [categoryKey, field.name] as [string, string]
    
    const rules: FormItemProps['rules'] = []
    // 租户管理员允许提交空值（用于删除配置），所以不添加必填验证
    // 系统管理员需要必填验证
    if (field.required && !isTenantAdmin) {
      rules.push({ required: true, message: `请输入${field.label || field.name}` })
    }

    // 敏感字段使用密码输入框
    if (field.sensitive) {
      return (
        <Form.Item key={field.name} name={fieldName} label={field.label || field.name} rules={rules}>
          <Input.Password placeholder={field.placeholder || `请输入${field.label || field.name}`} />
        </Form.Item>
      )
    }

    // 根据类型渲染不同组件
    switch (field.type) {
      case 'number':
        return (
          <Form.Item key={field.name} name={fieldName} label={field.label || field.name} rules={rules}>
            <InputNumber
              min={field.min}
              max={field.max}
              step={field.name === 'temperature' || field.name === 'similarity_threshold' ? 0.01 : 1}
              style={{ width: '100%' }}
              placeholder={field.placeholder}
            />
          </Form.Item>
        )

      case 'array':
        // 如果有 allowed_values，使用 Checkbox.Group
        if (field.allowed_values && field.allowed_values.length > 0) {
          return (
            <Form.Item key={field.name} name={fieldName} label={field.label || field.name} rules={rules}>
              <Checkbox.Group
                options={field.allowed_values.map(val => ({ label: val, value: val }))}
              />
            </Form.Item>
          )
        }
        // 否则使用普通输入（数组可能需要特殊处理）
        return (
          <Form.Item key={field.name} name={fieldName} label={field.label || field.name} rules={rules}>
            <Input placeholder={field.placeholder} />
          </Form.Item>
        )

      case 'boolean':
        return (
          <Form.Item key={field.name} name={fieldName} label={field.label || field.name} valuePropName="checked" rules={rules}>
            <Checkbox />
          </Form.Item>
        )

      case 'string':
      default:
        // 如果有 allowed_values，使用 Select
        if (field.allowed_values && field.allowed_values.length > 0) {
          return (
            <Form.Item key={field.name} name={fieldName} label={field.label || field.name} rules={rules}>
              <Select placeholder={field.placeholder || `请选择${field.label || field.name}`}>
                {field.allowed_values.map(val => (
                  <Option key={val} value={val}>
                    {val}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )
        }
        // 否则使用普通输入
        return (
          <Form.Item key={field.name} name={fieldName} label={field.label || field.name} rules={rules}>
            <Input placeholder={field.placeholder || `请输入${field.label || field.name}`} />
          </Form.Item>
        )
    }
  }

  // 生成 Collapse 的 key
  const getCollapseKey = (def: ConfigDefinitionItem) => {
    return def.category === 'doc' ? `${def.category}_${def.key}` : def.category
  }

  if (loading && definitions.length === 0) {
    return <Spin />
  }

  // 生成默认展开的 key 列表
  const defaultActiveKeys = definitions.map(def => getCollapseKey(def))

  // 根据用户角色确定页面标题和按钮文本
  const pageTitle = isSystemAdmin ? '配置管理（系统级）' : isTenantAdmin ? '配置管理（租户级）' : '配置管理'
  const buttonText = isSystemAdmin ? '保存系统配置' : isTenantAdmin ? '保存租户配置' : '保存配置'

  // 如果既不是系统管理员也不是租户管理员，显示无权限提示
  if (!isSystemAdmin && !isTenantAdmin) {
    return (
      <Card title="配置管理" style={{ maxWidth: 900 }}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <p>您没有权限访问配置管理页面</p>
        </div>
      </Card>
    )
  }

  return (
    <Card title={pageTitle} style={{ maxWidth: 900 }}>
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Collapse defaultActiveKey={defaultActiveKeys} accordion={false} ghost>
          {definitions.map(def => {
            const collapseKey = getCollapseKey(def)
            return (
              <Collapse.Panel key={collapseKey} header={def.label}>
                {def.fields.map(field => renderField(def, field))}
              </Collapse.Panel>
            )
          })}
        </Collapse>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={submitting}>
            {buttonText}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default ConfigPage
