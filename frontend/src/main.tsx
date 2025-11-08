import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider, Layout, Menu, Typography } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import UploadPage from './pages/Upload'
import UploadQBPage from './pages/UploadQB'
import SearchPage from './pages/Search'
import './styles/index.css'

const { Header, Content } = Layout

function App() {
  const [activeKey, setActiveKey] = useState<'upload' | 'qb' | 'search'>('upload')

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#635bff',
          borderRadius: 10,
          fontSize: 14,
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Header className="app-header">
          <div className="mx-auto max-w-6xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="brand-badge" />
              <div>
                <div className="brand-title">分片知识库</div>
                <div className="brand-sub">上传 · 题库 · 检索</div>
              </div>
            </div>
            <Menu
              mode="horizontal"
              selectedKeys={[activeKey]}
              onClick={(e) => setActiveKey(e.key as any)}
              items={[
                { key: 'upload', label: '上传' },
                { key: 'qb', label: '题库上传' },
                { key: 'search', label: '检索' },
              ]}
            />
          </div>
        </Header>
        <Content>
          <div className="mx-auto max-w-6xl p-4 content-area">
            {activeKey === 'upload' ? <UploadPage /> : activeKey === 'qb' ? <UploadQBPage /> : <SearchPage />}
          </div>
        </Content>
      </Layout>
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)


