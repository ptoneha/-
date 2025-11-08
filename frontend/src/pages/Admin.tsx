import { useEffect, useState } from 'react'
import { Card, Statistic, Row, Col, Tabs, Table, Button, Space, Tag, message, Popconfirm, Input } from 'antd'
import { DeleteOutlined, ReloadOutlined, CheckOutlined, SearchOutlined } from '@ant-design/icons'
import { 
  getDashboard, 
  listDocs, 
  deleteDoc, 
  listChunks, 
  deleteChunk, 
  batchVerifyChunks,
  listQuestions,
  deleteQuestion,
  getAuditLogs
} from '../lib/api'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('dashboard')
  
  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 24 }}>管理后台</h1>
      
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          { key: 'dashboard', label: '📊 仪表板', children: <Dashboard /> },
          { key: 'docs', label: '📁 文档管理', children: <DocsManager /> },
          { key: 'chunks', label: '📝 分片管理', children: <ChunksManager /> },
          { key: 'questions', label: '❓ 题库管理', children: <QuestionsManager /> },
          { key: 'logs', label: '📋 操作日志', children: <AuditLogs /> },
        ]}
      />
    </div>
  )
}

// 仪表板
function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>({})
  
  const loadStats = async () => {
    try {
      setLoading(true)
      const data = await getDashboard()
      setStats(data)
    } catch (e: any) {
      console.error('加载统计失败:', e)
      message.error(`加载统计数据失败: ${e?.response?.data?.detail || e?.message || '未知错误'}`)
      // 设置默认值避免一直加载
      setStats({
        system_stats: {
          total_docs: 0,
          total_chunks: 0,
          total_questions: 0,
          logs_24h: 0
        },
        recent_uploads: []
      })
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadStats()
  }, [])
  
  const systemStats = stats.system_stats || {}
  
  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="文档总数" value={systemStats.total_docs || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="分片总数" value={systemStats.total_chunks || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="题目总数" value={systemStats.total_questions || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="24小时操作" value={systemStats.logs_24h || 0} />
          </Card>
        </Col>
      </Row>
      
      <Card title="最近上传" loading={loading}>
        <Table
          size="small"
          dataSource={stats.recent_uploads || []}
          rowKey="doc_id"
          columns={[
            { title: 'ID', dataIndex: 'doc_id', width: 80 },
            { title: '标题', dataIndex: 'title' },
            { title: '来源', dataIndex: 'source', width: 100, render: (v) => <Tag>{v}</Tag> },
            { title: '创建时间', dataIndex: 'created_at', width: 180, render: (v) => new Date(v).toLocaleString() },
          ]}
          pagination={false}
        />
      </Card>
    </div>
  )
}

// 文档管理
function DocsManager() {
  const [loading, setLoading] = useState(false)
  const [docs, setDocs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [search, setSearch] = useState('')
  
  const loadDocs = async () => {
    try {
      setLoading(true)
      const data = await listDocs({ 
        search: search || undefined, 
        limit: pageSize, 
        offset: (page - 1) * pageSize 
      })
      setDocs(data.data || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      message.error('加载文档列表失败')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadDocs()
  }, [page, pageSize])
  
  const handleDelete = async (docId: number) => {
    try {
      await deleteDoc(docId)
      message.success('删除成功')
      loadDocs()
    } catch (e: any) {
      message.error('删除失败')
    }
  }
  
  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索文档标题"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onSearch={loadDocs}
          style={{ width: 300 }}
        />
        <Button icon={<ReloadOutlined />} onClick={loadDocs}>刷新</Button>
      </Space>
      
      <Table
        loading={loading}
        dataSource={docs}
        rowKey="doc_id"
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p) => setPage(p),
          showTotal: (t) => `共 ${t} 条`,
        }}
        columns={[
          { title: 'ID', dataIndex: 'doc_id', width: 80 },
          { title: '标题', dataIndex: 'title', ellipsis: true },
          { title: '章节', dataIndex: 'chapter', width: 80 },
          { title: '节号', dataIndex: 'section_number', width: 80 },
          { title: '来源', dataIndex: 'source', width: 100, render: (v) => <Tag color={v === 'kb' ? 'blue' : 'green'}>{v}</Tag> },
          { title: '分片数', dataIndex: 'chunk_count', width: 100 },
          { title: '创建时间', dataIndex: 'created_at', width: 160, render: (v) => v ? new Date(v).toLocaleString() : '-' },
          {
            title: '操作',
            width: 120,
            render: (_, record) => (
              <Space>
                <Popconfirm
                  title="确定删除？"
                  onConfirm={() => handleDelete(record.doc_id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />
    </div>
  )
}

// 分片管理
function ChunksManager() {
  const [loading, setLoading] = useState(false)
  const [chunks, setChunks] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<any[]>([])
  
  const loadChunks = async () => {
    try {
      setLoading(true)
      const data = await listChunks({ 
        search: search || undefined, 
        limit: pageSize, 
        offset: (page - 1) * pageSize 
      })
      setChunks(data.data || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      message.error('加载分片列表失败')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadChunks()
  }, [page])
  
  const handleDelete = async (chunkId: number) => {
    try {
      await deleteChunk(chunkId)
      message.success('删除成功')
      loadChunks()
    } catch (e: any) {
      message.error('删除失败')
    }
  }
  
  const handleBatchVerify = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要审核的分片')
      return
    }
    try {
      await batchVerifyChunks(selectedRowKeys, true)
      message.success(`已审核 ${selectedRowKeys.length} 条分片`)
      setSelectedRowKeys([])
      loadChunks()
    } catch (e: any) {
      message.error('批量审核失败')
    }
  }
  
  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索分片内容"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onSearch={loadChunks}
          style={{ width: 300 }}
        />
        <Button icon={<ReloadOutlined />} onClick={loadChunks}>刷新</Button>
        <Button 
          type="primary" 
          icon={<CheckOutlined />} 
          onClick={handleBatchVerify}
          disabled={selectedRowKeys.length === 0}
        >
          批量审核 ({selectedRowKeys.length})
        </Button>
      </Space>
      
      <Table
        loading={loading}
        dataSource={chunks}
        rowKey="chunk_id"
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p) => setPage(p),
          showTotal: (t) => `共 ${t} 条`,
        }}
        columns={[
          { title: 'ID', dataIndex: 'chunk_id', width: 80 },
          { title: '文档', dataIndex: 'doc_title', ellipsis: true, width: 200 },
          { title: '类型', dataIndex: 'kind', width: 100, render: (v) => <Tag>{v}</Tag> },
          { title: 'H1', dataIndex: 'heading_h1', ellipsis: true, width: 150 },
          { title: 'H2', dataIndex: 'heading_h2', ellipsis: true, width: 150 },
          { title: '已审核', dataIndex: 'is_verified', width: 80, render: (v) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
          { title: '质量分', dataIndex: 'quality_score', width: 80 },
          {
            title: '操作',
            width: 100,
            render: (_, record) => (
              <Popconfirm
                title="确定删除？"
                onConfirm={() => handleDelete(record.chunk_id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
              </Popconfirm>
            ),
          },
        ]}
      />
    </div>
  )
}

// 题库管理
function QuestionsManager() {
  const [loading, setLoading] = useState(false)
  const [questions, setQuestions] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  
  const loadQuestions = async () => {
    try {
      setLoading(true)
      const data = await listQuestions({ limit: pageSize, offset: (page - 1) * pageSize })
      setQuestions(data.data || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      message.error('加载题目列表失败')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadQuestions()
  }, [page])
  
  const handleDelete = async (qid: number) => {
    try {
      await deleteQuestion(qid)
      message.success('删除成功')
      loadQuestions()
    } catch (e: any) {
      message.error('删除失败')
    }
  }
  
  return (
    <div>
      <Button icon={<ReloadOutlined />} onClick={loadQuestions} style={{ marginBottom: 16 }}>
        刷新
      </Button>
      
      <Table
        loading={loading}
        dataSource={questions}
        rowKey="qid"
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p) => setPage(p),
          showTotal: (t) => `共 ${t} 条`,
        }}
        columns={[
          { title: 'ID', dataIndex: 'qid', width: 80 },
          { title: '题干', dataIndex: 'stem_md', ellipsis: true },
          { title: '类型', dataIndex: 'qtype', width: 100, render: (v) => <Tag>{v}</Tag> },
          { title: '难度', dataIndex: 'difficulty', width: 80, render: (v) => '★'.repeat(v || 0) },
          { title: '使用次数', dataIndex: 'usage_count', width: 100 },
          {
            title: '操作',
            width: 100,
            render: (_, record) => (
              <Popconfirm
                title="确定删除？"
                onConfirm={() => handleDelete(record.qid)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
              </Popconfirm>
            ),
          },
        ]}
      />
    </div>
  )
}

// 操作日志
function AuditLogs() {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  
  const loadLogs = async () => {
    try {
      setLoading(true)
      const data = await getAuditLogs({ limit: pageSize, offset: (page - 1) * pageSize })
      setLogs(data.data || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      message.error('加载日志失败')
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadLogs()
  }, [page])
  
  return (
    <div>
      <Button icon={<ReloadOutlined />} onClick={loadLogs} style={{ marginBottom: 16 }}>
        刷新
      </Button>
      
      <Table
        loading={loading}
        dataSource={logs}
        rowKey="log_id"
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p) => setPage(p),
          showTotal: (t) => `共 ${t} 条`,
        }}
        columns={[
          { title: 'ID', dataIndex: 'log_id', width: 80 },
          { title: '用户', dataIndex: 'username', width: 100 },
          { title: '操作', dataIndex: 'action', width: 120, render: (v) => <Tag color="blue">{v}</Tag> },
          { title: '资源类型', dataIndex: 'resource_type', width: 100 },
          { title: '资源ID', dataIndex: 'resource_id', width: 100 },
          { title: 'IP地址', dataIndex: 'ip_address', width: 140 },
          { title: '时间', dataIndex: 'created_at', width: 180, render: (v) => new Date(v).toLocaleString() },
        ]}
      />
    </div>
  )
}

