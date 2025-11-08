import { Card, Tag, Typography, Button, Space } from 'antd'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { useState } from 'react'
import QuestionDetailDrawer from './QuestionDetailDrawer'

const { Text } = Typography

export default function QuestionCard({ item, query }: { item: any; query: string }) {
  const [open, setOpen] = useState(false)
  const options = item.options_json || {}
  return (
    <Card className="w-full">
      <div className="flex items-start justify-between">
        <Space>
          <Tag color="blue">{item.qtype || 'unknown'}</Tag>
          {typeof item.difficulty !== 'undefined' && <Tag>难度 {item.difficulty}</Tag>}
          {typeof item.score !== 'undefined' && <Tag color="geekblue">score {Number(item.score || 0).toFixed(2)}</Tag>}
        </Space>
        <Text type="secondary">{item.source_file}</Text>
      </div>
      <div className="prose max-w-none mt-2">
        <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
          {item.stem_md || ''}
        </ReactMarkdown>
      </div>
      {options && Object.keys(options).length > 0 && (
        <div className="prose max-w-none">
          <ul>
            {Object.entries(options).map(([k, v]: any) => (
              <li key={k}>
                <strong>{k}.</strong>{' '}
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    p: ({ children }) => <>{children}</>,
                    ul: ({ children }) => <>{children}</>,
                    li: ({ children }) => <>{children}</>
                  }}
                >
                  {String(v) || ''}
                </ReactMarkdown>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="mt-3 flex gap-2">
        <Button size="small" type="primary" onClick={() => setOpen(true)}>查看详情</Button>
      </div>
      <QuestionDetailDrawer open={open} qid={item.qid} onClose={() => setOpen(false)} />
    </Card>
  )
}


