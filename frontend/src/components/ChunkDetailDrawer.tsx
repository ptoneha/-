import { Drawer, Descriptions, Spin, Typography, Button, Space, message } from 'antd'
import React, { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { getChunk } from '../lib/api'

const { Text } = Typography

type Props = {
  open: boolean
  chunkId?: number
  onClose: () => void
}

export default function ChunkDetailDrawer({ open, chunkId, onClose }: Props) {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any | null>(null)

  useEffect(() => {
    if (!open || !chunkId) return
    setLoading(true)
    getChunk(chunkId)
      .then((res) => setData(res))
      .catch((e) => message.error(e?.response?.data?.detail || e?.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [open, chunkId])

  const copyLatex = async () => {
    if (!data) return
    await navigator.clipboard.writeText(data.content_md || '')
    message.success('已复制')
  }

  return (
    <Drawer open={open} onClose={onClose} width={720} title={<span>分片详情 #{chunkId}</span>}>
      {loading ? (
        <div className="w-full flex justify-center py-10"><Spin /></div>
      ) : data ? (
        <div className="space-y-4">
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="类别">{data.kind}</Descriptions.Item>
            <Descriptions.Item label="节标题(H1)">{data.h1}</Descriptions.Item>
            <Descriptions.Item label="小节标题(H2)">{data.h2}</Descriptions.Item>
            <Descriptions.Item label="节号">{data.section}</Descriptions.Item>
            <Descriptions.Item label="锚点">{data.anchor}</Descriptions.Item>
            <Descriptions.Item label="tokens">{data.tokens}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{data.created_at}</Descriptions.Item>
          </Descriptions>
          <div className="prose max-w-none">
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {data.content_md || ''}
            </ReactMarkdown>
          </div>
          <Space>
            <Button onClick={copyLatex}>复制 LaTeX</Button>
          </Space>
        </div>
      ) : (
        <Text type="secondary">未找到数据</Text>
      )}
    </Drawer>
  )
}


