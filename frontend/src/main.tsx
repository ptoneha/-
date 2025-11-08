import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider, Layout, Tabs } from 'antd'
import { UploadOutlined, BookOutlined, SearchOutlined, SettingOutlined } from '@ant-design/icons'
import zhCN from 'antd/locale/zh_CN'
import UploadPage from './pages/Upload'
import UploadQBPage from './pages/UploadQB'
import SearchPage from './pages/Search'
import AdminPage from './pages/Admin'
import './styles/index.css'

const { Header, Content } = Layout

function App() {
  const [activeKey, setActiveKey] = useState<string>('upload')

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
      <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}>
          <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ 
                width: 40, 
                height: 40, 
                borderRadius: 10,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 20,
                fontWeight: 'bold'
              }}>知</div>
              <div>
                <div style={{ fontSize: 18, fontWeight: 600, color: '#262626' }}>分片知识库</div>
                <div style={{ fontSize: 12, color: '#8c8c8c' }}>智能文档管理系统</div>
              </div>
            </div>
          </div>
        </Header>
        <Content style={{ padding: '24px' }}>
          <div style={{ maxWidth: 1400, margin: '0 auto' }}>
            <Tabs
              activeKey={activeKey}
              onChange={setActiveKey}
              size="large"
              tabBarStyle={{ 
                background: '#fff',
                padding: '8px 24px 0',
                borderRadius: '10px 10px 0 0',
                marginBottom: 0
              }}
              items={[
                {
                  key: 'upload',
                  label: (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
                      <UploadOutlined />
                      文档上传
                    </span>
                  ),
                  children: <div style={{ background: '#fff', padding: 24, borderRadius: '0 0 10px 10px', minHeight: 'calc(100vh - 200px)' }}><UploadPage /></div>
                },
                {
                  key: 'qb',
                  label: (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
                      <BookOutlined />
                      题库上传
                    </span>
                  ),
                  children: <div style={{ background: '#fff', padding: 24, borderRadius: '0 0 10px 10px', minHeight: 'calc(100vh - 200px)' }}><UploadQBPage /></div>
                },
                {
                  key: 'search',
                  label: (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
                      <SearchOutlined />
                      知识检索
                    </span>
                  ),
                  children: <div style={{ background: '#fff', padding: 24, borderRadius: '0 0 10px 10px', minHeight: 'calc(100vh - 200px)' }}><SearchPage /></div>
                },
                {
                  key: 'admin',
                  label: (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15 }}>
                      <SettingOutlined />
                      系统管理
                    </span>
                  ),
                  children: <div style={{ background: '#fff', padding: 24, borderRadius: '0 0 10px 10px', minHeight: 'calc(100vh - 200px)' }}><AdminPage /></div>
                },
              ]}
            />
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


