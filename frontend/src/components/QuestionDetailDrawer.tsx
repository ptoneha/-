import { Drawer, Descriptions, Spin, Typography, message } from 'antd'
import React, { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'

import { getQuestion } from '../lib/api'

const { Text } = Typography

type Props = {
  open: boolean
  qid?: number
  onClose: () => void
}

export default function QuestionDetailDrawer({ open, qid, onClose }: Props) {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any | null>(null)

  useEffect(() => {
    if (!open || !qid) return
    setLoading(true)
    getQuestion(qid)
      .then(setData)
      .catch((e) => message.error(e?.response?.data?.detail || e?.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [open, qid])

  return (
    <Drawer open={open} onClose={onClose} width={680} title={<span>题目详情 #{qid}</span>}>
      {loading ? (
        <div className="w-full flex justify-center py-10"><Spin /></div>
      ) : data ? (
        <div className="space-y-4">
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label="题型">{data.qtype}</Descriptions.Item>
            <Descriptions.Item label="难度">{data.difficulty}</Descriptions.Item>
            <Descriptions.Item label="标签">{(data.tags || []).join(', ')}</Descriptions.Item>
            <Descriptions.Item label="来源文件">{data.source_file}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{data.created_at}</Descriptions.Item>
          </Descriptions>
          <div className="prose max-w-none">
            <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
              {data.stem_md || ''}
            </ReactMarkdown>
          </div>
          {data.options_json && (
            <div className="prose max-w-none">
              <ul>
                {Object.entries(data.options_json || {}).map(([k, v]: any) => (
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
          {data.answer_text && (
            <div className="prose max-w-none">
              <Text>答案：</Text> <Text strong>{data.answer_text}</Text>
            </div>
          )}
          {data.explanation_md && (
            <div className="prose max-w-none">
              <Text type="secondary">解析：</Text>
              <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                {data.explanation_md || ''}
              </ReactMarkdown>
            </div>
          )}
        </div>
      ) : (
        <Text type="secondary">未找到数据</Text>
      )}
    </Drawer>
  )
}


