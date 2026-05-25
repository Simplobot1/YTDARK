import { getToken } from './auth'
import type { Video, CanalCandidato, ChannelDNA, CanalConfig, Keyword } from './types'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers as Record<string, string> || {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail: string }).detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const login = (email: string, senha: string) =>
  request<{ token: string; email: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha }),
  })

export const getCanais = () => request<{ canais: string[] }>('/canais/')
export const getCanalConfig = (id: string) => request<CanalConfig>(`/canais/${id}/config`)
export const getCanalDna = (id: string) => request<ChannelDNA>(`/canais/${id}/dna`)
export const updateCanalDna = (id: string, dna: ChannelDNA) =>
  request<{ ok: boolean }>(`/canais/${id}/dna`, { method: 'PUT', body: JSON.stringify(dna) })

export const descobrirCanais = (body: object) =>
  request<CanalCandidato[]>('/descobrir-canais', { method: 'POST', body: JSON.stringify(body) })
export const keywordResearch = (canalId: string, nicho: string, idioma: string) =>
  request<{ keywords: Keyword[] }>(`/canais/${canalId}/keywords`, {
    method: 'POST',
    body: JSON.stringify({ nicho, idioma }),
  })

export const minerar = (canalId: string) =>
  request<{ minerados: number; videos: Video[] }>(`/canais/${canalId}/minerar`, { method: 'POST' })
export const getCandidatos = (canalId: string, page = 1, limit = 20) =>
  request<{ videos: Video[]; total: number; page: number; pages: number }>(
    `/canais/${canalId}/candidatos?page=${page}&limit=${limit}`
  )
export const aprovarVideo = (canalId: string, videoId: string) =>
  request<{ ok: boolean }>(`/canais/${canalId}/aprovar/${videoId}`, { method: 'POST' })

export const analisarVideo = (canalId: string, videoId: string) =>
  request<{ analise: object }>(`/canais/${canalId}/analisar/${videoId}`, { method: 'POST' })
export const getAnalisados = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/analisados`)

export const produzirVideo = (canalId: string, videoId: string) =>
  request<{ mp4_url: string }>(`/canais/${canalId}/produzir/${videoId}`, { method: 'POST' })
export const getFila = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/fila`)

export const publicarVideo = (canalId: string, videoId: string) =>
  request<{ yt_link: string }>(`/canais/${canalId}/publicar/${videoId}`, { method: 'POST' })
export const getPublicados = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/publicados`)
