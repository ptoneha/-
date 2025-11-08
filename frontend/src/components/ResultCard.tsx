import { Card, Tag, Typography, Space, Button } from 'antd'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { useState } from 'react'
import ChunkDetailDrawer from './ChunkDetailDrawer'

const { Text } = Typography

function Breadcrumb({ h1, h2 }: { h1?: string; h2?: string }) {
  return (
    <div className="text-gray-500 text-sm mb-2">
      {h1 && <span>{h1}</span>} {h1 && h2 && <span> → </span>} {h2 && <span>{h2}</span>}
    </div>
  )
}

function Highlighter({ text, query }: { text: string; query: string }) {
  if (!query) return <span>{text}</span>
  const parts = text.split(new RegExp(`(${escapeRegExp(query)})`, 'ig'))
  return (
    <span>
      {parts.map((p, i) => (
        <span key={i} className={p.toLowerCase() === query.toLowerCase() ? 'bg-yellow-200' : ''}>{p}</span>
      ))}
    </span>
  )
}

function escapeRegExp(string: string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export default function ResultCard({ item, query }: { item: any; query: string }) {
  const [open, setOpen] = useState(false)
  const copyLatex = async () => {
    await navigator.clipboard.writeText(item.content_md || '')
  }
  return (
    <Card className="w-full">
      <div className="flex items-start justify-between">
        <Breadcrumb h1={item.h1} h2={item.h2} />
        <Space>
          <Tag>{item.kind}</Tag>
          <Tag color="blue">score {Number(item.score || 0).toFixed(2)}</Tag>
        </Space>
      </div>
      <div className="prose max-w-none">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {item.content_md || ''}
        </ReactMarkdown>
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="small" onClick={copyLatex}>复制 LaTeX</Button>
        <Button size="small" type="primary" onClick={() => setOpen(true)}>查看详情</Button>
      </div>
      {item.neighbors && (item.neighbors.prev || item.neighbors.next) && (
        <div className="mt-4 space-y-2">
          {item.neighbors.prev && (
            <div>
              <Text type="secondary">上文：</Text>
              <div className="prose max-w-none">
                <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                  {item.neighbors.prev.content_md || ''}
                </ReactMarkdown>
              </div>
            </div>
          )}
          {item.neighbors.next && (
            <div>
              <Text type="secondary">下文：</Text>
              <div className="prose max-w-none">
                <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                  {item.neighbors.next.content_md || ''}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
      <ChunkDetailDrawer open={open} onClose={() => setOpen(false)} chunkId={item.chunk_id} />
    </Card>
  )
}


