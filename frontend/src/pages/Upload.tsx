import { useState } from 'react'
import { Alert, Button, Form, InputNumber, Upload, message, Progress, Card, Select, Typography, Space, Divider, Input } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { ingest, ingestQBank } from '../lib/api'

const { Dragger } = Upload

export default function UploadPage() {
  const [form] = Form.useForm()
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<{ mode: 'knowledge' | 'qbank'; count: number } | null>(null)

  const props = {
    name: 'file',
    multiple: false,
    maxCount: 1,
    accept: '.docx',
    beforeUpload: (file: File) => {
      const name = file.name.toLowerCase()
      const isAllowed = name.endsWith('.docx')
      if (!isAllowed) {
        message.error('仅支持 .docx 文件')
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
        let res: any
        if (values.uploadType === 'qbank') {
          res = await ingestQBank(file as File, values.tags, values.defaultDifficulty)
          setResult({ mode: 'qbank', count: res.questions })
        } else {
          res = await ingest(file as File, values.chapter, values.section)
          setResult({ mode: 'knowledge', count: res.chunks })
        }
        setProgress(90)
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
          <Typography.Title level={4} style={{ margin: 0 }}>上传文档</Typography.Title>
          <Typography.Text type="secondary">仅支持 .docx 文件；根据"上传类型"自动路由到对应解析。</Typography.Text>
        </Space>
        <Divider style={{ marginTop: 16, marginBottom: 16 }} />
        <Form layout="inline" form={form} initialValues={{ uploadType: 'knowledge', chapter: 1, section: 1, defaultDifficulty: 2 }}>
          <Form.Item label="上传类型" name="uploadType" rules={[{ required: true }]}> 
            <Select style={{ width: 160 }}
              options={[
                { value: 'knowledge', label: '知识点文档' },
                { value: 'qbank', label: '题库文档' },
              ]}
            />
          </Form.Item>
          <Form.Item label="章号" name="chapter" rules={[{ required: true, type: 'number' }]}> 
            <InputNumber min={1} max={50} />
          </Form.Item>
          <Form.Item label="节号" name="section" rules={[{ required: true, type: 'number' }]}> 
            <InputNumber min={1} max={50} />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.uploadType !== curr.uploadType}>
            {({ getFieldValue }) => getFieldValue('uploadType') === 'qbank' && (
              <>
                <Form.Item label="标签" name="tags">
                  <Input allowClear placeholder="如：期末, 微积分（逗号分隔）" style={{ width: 260 }} />
                </Form.Item>
                <Form.Item label="默认难度" name="defaultDifficulty">
                  <InputNumber min={1} max={5} />
                </Form.Item>
              </>
            )}
          </Form.Item>
        </Form>
        <Dragger {...props} disabled={uploading} className="mt-4">
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">点击或拖拽 .docx 文件到此处</p>
          <p className="ant-upload-hint">单文件 ≤ 10MB；推荐一次仅上传一份文档</p>
        </Dragger>
        {uploading && <div className="mt-4"><Progress percent={progress} /></div>}
        {result && (
          <Alert className="mt-4" type="success" showIcon message={result.mode === 'qbank' ? `上传成功：本次题目 ${result.count} 条` : `上传成功：本次分片 ${result.count} 条`} />
        )}
      </Card>
    </div>
  )
}


