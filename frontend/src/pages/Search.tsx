import { useEffect, useMemo, useState } from 'react'
import { Card, Input, Select, Switch, List, Tag, Space, Typography, message, Pagination, Divider } from 'antd'
import { search as apiSearch, getSectionsMeta, searchQ } from '../lib/api'
import ResultCard from '../components/ResultCard'
import QuestionCard from '../components/QuestionCard'

const { Text } = Typography

const KIND_OPTIONS = [
  { label: '全部', value: '' },
  { label: '定义', value: 'definition' },
  { label: '定理', value: 'theorem' },
  { label: '公式', value: 'formula' },
  { label: '性质', value: 'property' },
  { label: '例题', value: 'example' },
]

export default function SearchPage() {
  const [q, setQ] = useState('')
  const [kind, setKind] = useState('')
  const [section, setSection] = useState<number | undefined>(undefined)
  const [neighbor, setNeighbor] = useState(true)
  const [dataset, setDataset] = useState<'kb' | 'qbank'>('kb')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [sectionOptions, setSectionOptions] = useState<{label: any, value: any}[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(8)
  const [total, setTotal] = useState(0)

  const doSearch = async () => {
    try {
      setLoading(true)
      if (dataset === 'kb') {
        const res = await apiSearch({ q: q || undefined, kind: kind || undefined, section, limit: pageSize, offset: (page - 1) * pageSize, neighbor: neighbor ? 1 : 0 })
        setResults(res.results)
        setTotal(res.total || 0)
      } else {
        const res = await searchQ({ q: q || undefined, limit: pageSize, offset: (page - 1) * pageSize })
        setResults(res.results)
        setTotal(res.total || 0)
      }
    } catch (e: any) {
      message.error(e?.response?.data?.detail || e?.message || '搜索失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // 初次进入页面自动加载最新分片
    (async () => {
      try {
        if (dataset === 'kb') {
          const meta = await getSectionsMeta()
          const opts = (meta.sections || []).map((s: any) => ({ label: `${s.section}（${s.count}）`, value: s.section }))
          setSectionOptions(opts)
        } else {
          setSectionOptions([])
        }
      } catch {}
      await doSearch()
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset])

  useEffect(() => {
    // 当筛选条件变更时，重置到第 1 页
    setPage(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, section, neighbor, dataset])

  useEffect(() => {
    doSearch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, q, kind, section, neighbor, dataset])

  return (
    <div className="space-y-4">
      <Card className="glass-card">
        <div className="flex flex-col md:flex-row gap-3 items-center">
          <Input.Search
            placeholder={dataset === 'kb' ? '输入关键词，如：两个重要极限、sinx/x、夹逼准则' : '输入题干关键词，如：泰勒、极限、导数'}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onSearch={() => setPage(1)}
            enterButton
            className="flex-1"
          />
          <Space wrap>
            <Select
              style={{ width: 140 }}
              value={dataset}
              onChange={(v) => setDataset(v)}
              options={[{ label: '知识点', value: 'kb' }, { label: '题库', value: 'qbank' }]}
            />
            {dataset === 'kb' && (
              <>
                <Select
                  placeholder="类别"
                  value={kind}
                  onChange={setKind}
                  style={{ width: 120 }}
                  options={KIND_OPTIONS}
                />
                <Select
                  allowClear
                  placeholder="节号"
                  style={{ width: 120 }}
                  value={section as any}
                  onChange={(v) => setSection(v)}
                  options={sectionOptions.length ? sectionOptions : Array.from({ length: 20 }).map((_, i) => ({ label: i + 1, value: i + 1 }))}
                />
                <div className="flex items-center gap-2">
                  <Text>展开上下文</Text>
                  <Switch checked={neighbor} onChange={setNeighbor} />
                </div>
              </>
            )}
          </Space>
        </div>
      </Card>

      <List
        loading={loading}
        dataSource={results}
        renderItem={(item) => (
          <List.Item>
            {dataset === 'kb' ? (
              <ResultCard item={item} query={q} />
            ) : (
              <QuestionCard item={item} query={q} />
            )}
          </List.Item>
        )}
      />
      <div className="flex justify-center py-4">
        <Pagination
          current={page}
          pageSize={pageSize}
          total={total}
          showSizeChanger
          pageSizeOptions={[8, 12, 20] as any}
          onChange={(p, s) => { setPage(p); setPageSize(s) }}
        />
      </div>
    </div>
  )
}


