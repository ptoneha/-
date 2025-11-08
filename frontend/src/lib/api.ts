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

