import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE || 'http://localhost:8787'
const http = axios.create({ baseURL })

export async function ingest(file: File, chapter: number, section: number, source?: string) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('chapter', String(chapter))
  fd.append('section_number', String(section))
  if (source) fd.append('source', source)
  const { data } = await http.post('/ingest', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function ingestQBank(file: File, tags?: string, defaultDifficulty?: number) {
  const fd = new FormData()
  fd.append('file', file)
  if (tags) fd.append('tags', tags)
  if (typeof defaultDifficulty !== 'undefined') fd.append('default_difficulty', String(defaultDifficulty))
  const { data } = await http.post('/api/qbank/ingest', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function search(params: { q?: string; kind?: string; section?: number; limit?: number; offset?: number; neighbor?: 0 | 1 }) {
  const { data } = await http.get('/search', { params })
  return data
}

export async function getChunk(id: number) {
  const { data } = await http.get(`/chunks/${id}`)
  return data
}

export async function getSectionsMeta() {
  const { data } = await http.get('/meta/sections')
  return data
}

// 题库检索
export async function searchQ(params: { q?: string; limit?: number; offset?: number }) {
  const { data } = await http.get('/api/qbank/search', { params })
  return data
}

export async function getQuestion(qid: number) {
  const { data } = await http.get(`/api/qbank/detail/${qid}`)
  return data
}

// ============= 管理功能 API =============

// 统计
export async function getDashboard() {
  const { data } = await http.get('/admin/stats/dashboard')
  return data
}

export async function getSystemStats() {
  const { data } = await http.get('/admin/stats/system')
  return data
}

// 文档管理
export async function listDocs(params?: { source?: string; search?: string; limit?: number; offset?: number }) {
  const { data } = await http.get('/admin/docs', { params })
  return data
}

export async function getDocDetail(docId: number) {
  const { data } = await http.get(`/admin/docs/${docId}`)
  return data
}

export async function deleteDoc(docId: number, hardDelete = false) {
  const { data } = await http.delete(`/admin/docs/${docId}`, { params: { hard_delete: hardDelete } })
  return data
}

export async function updateDoc(docId: number, updates: any) {
  const { data } = await http.put(`/admin/docs/${docId}`, updates)
  return data
}

// 分片管理
export async function listChunks(params?: { doc_id?: number; kind?: string; search?: string; limit?: number; offset?: number }) {
  const { data } = await http.get('/admin/chunks', { params })
  return data
}

export async function getChunkDetail(chunkId: number) {
  const { data } = await http.get(`/admin/chunks/${chunkId}`)
  return data
}

export async function deleteChunk(chunkId: number, hardDelete = false) {
  const { data } = await http.delete(`/admin/chunks/${chunkId}`, { params: { hard_delete: hardDelete } })
  return data
}

export async function updateChunk(chunkId: number, updates: any) {
  const { data } = await http.put(`/admin/chunks/${chunkId}`, updates)
  return data
}

export async function batchVerifyChunks(chunkIds: number[], verified = true) {
  const { data } = await http.post('/admin/chunks/batch-verify', { chunk_ids: chunkIds, verified })
  return data
}

// 题目管理
export async function listQuestions(params?: { qtype?: string; difficulty?: number; search?: string; limit?: number; offset?: number }) {
  const { data } = await http.get('/admin/questions', { params })
  return data
}

export async function deleteQuestion(qid: number, hardDelete = false) {
  const { data } = await http.delete(`/admin/questions/${qid}`, { params: { hard_delete: hardDelete } })
  return data
}

// 审计日志
export async function getAuditLogs(params?: { user_id?: number; action?: string; limit?: number; offset?: number }) {
  const { data } = await http.get('/admin/audit/logs', { params })
  return data
}

