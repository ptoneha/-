import { useState } from 'react'
import { Alert, Form, InputNumber, Upload, message, Progress, Card, Typography, Input, Space, Divider } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { ingestQBank } from '../lib/api'

const { Dragger } = Upload
const { Paragraph } = Typography

export default function UploadQBPage() {
  const [form] = Form.useForm()
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<{ questions: number } | null>(null)

  const props = {
    name: 'file',
    multiple: false,
    maxCount: 1,
    accept: '.docx',
    beforeUpload: (file: File) => {
      const name = file.name.toLowerCase()
      const isAllowed = name.endsWith('.docx')
      if (!isAllowed) {
        message.error('题库仅支持 .docx 文件')
        return Upload.LIST_IGNORE
      }
      if (file.size > 10 * 1024 * 1024) {
        message.error('文件大小超过 10MB')
        return Upload.LIST_IGNORE
      }
      return true
    },
    customRequest: async (options: any) => {
      const { file, onSuccess, onError } = options
      try {
        const values = await form.validateFields()
        setUploading(true)
        setProgress(10)
        const res = await ingestQBank(file as File, values.tags, values.defaultDifficulty)
        setProgress(90)
        setResult({ questions: res.questions })
        setProgress(100)
        onSuccess(res)
      } catch (e: any) {
        onError?.(e)
        message.error(e?.response?.data?.detail || e?.message || '上传失败')
      } finally {
        setUploading(false)
        setTimeout(() => setProgress(0), 800)
      }
    },
  }

  return (
    <div className="space-y-4">
      <Card className="glass-card">
        <Space direction="vertical" size={12} style={{ width: '100%' }}>
          <Typography.Title level={4} style={{ margin: 0 }}>题库上传</Typography.Title>
          <Paragraph type="secondary" style={{ margin: 0 }}>仅支持 .docx 文件；可附加默认标签与难度，便于分类管理。</Paragraph>
        </Space>
        <Divider style={{ marginTop: 16, marginBottom: 16 }} />
        <Form layout="inline" form={form} initialValues={{ chapter: 1, section: 1, defaultDifficulty: 2 }}>
          <Form.Item label="章号" name="chapter" rules={[{ required: true, type: 'number' }]}> 
            <InputNumber min={1} max={50} />
          </Form.Item>
          <Form.Item label="节号" name="section" rules={[{ required: true, type: 'number' }]}> 
            <InputNumber min={1} max={50} />
          </Form.Item>
          <Form.Item label="标签" name="tags">
            <Input allowClear placeholder="如：期末, 微积分（逗号分隔）" style={{ width: 260 }} />
          </Form.Item>
          <Form.Item label="默认难度" name="defaultDifficulty">
            <InputNumber min={1} max={5} />
          </Form.Item>
        </Form>
        <Dragger {...props} disabled={uploading} className="mt-4">
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">点击或拖拽 .docx 题库文档到此处</p>
          <p className="ant-upload-hint">单文件 ≤ 10MB；建议每次上传一份题库</p>
        </Dragger>
        {uploading && <div className="mt-4"><Progress percent={progress} /></div>}
        {result && (
          <Alert className="mt-4" type="success" showIcon message={`上传成功：本次题目 ${result.questions} 条`} />
        )}
      </Card>
    </div>
  )
}


