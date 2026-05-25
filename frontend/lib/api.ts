import { getToken } from './auth'
import type { Video, CanalCandidato, CanalInfo, ChannelDNA, CanalConfig, RemodelarStatus } from './types'

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

export const getCanais = () => request<{ canais: CanalInfo[] }>('/canais/')
export const getCanalConfig = (id: string) => request<CanalConfig>(`/canais/${id}/config`)
export const getCanalDna = (id: string) => request<ChannelDNA>(`/canais/${id}/dna`)
export const updateCanalDna = (id: string, dna: ChannelDNA) =>
  request<{ ok: boolean }>(`/canais/${id}/dna`, { method: 'PUT', body: JSON.stringify(dna) })

export const listarFontes = (canalId: string) =>
  request<{ fontes: string[] }>(`/canais/${canalId}/fontes`)
export const adicionarFonte = (canalId: string, handle: string) =>
  request<{ ok: boolean; fontes: string[] }>(`/canais/${canalId}/fontes`, {
    method: 'POST', body: JSON.stringify({ handle }),
  })
export const removerFonte = (canalId: string, handle: string) =>
  request<{ ok: boolean; fontes: string[] }>(`/canais/${canalId}/fontes/${encodeURIComponent(handle)}`, {
    method: 'DELETE',
  })

export const descobrirCanais = (body: object) =>
  request<CanalCandidato[]>('/descobrir-canais', { method: 'POST', body: JSON.stringify(body) })

export const salvarCanaisDescobertos = (canalId: string, canais: CanalCandidato[]) =>
  request<{ salvos: number }>(`/descobrir-canais/salvar/${canalId}`, {
    method: 'POST',
    body: JSON.stringify({ canais }),
  })

export const listarCanaisSalvos = (canalId: string) =>
  request<CanalCandidato[]>(`/descobrir-canais/salvos/${canalId}`)

export const minerar = (canalId: string) =>
  request<{ minerados: number; videos: Video[] }>(`/canais/${canalId}/minerar`, { method: 'POST' })
export const getCandidatos = (canalId: string, page = 1, limit = 20) =>
  request<{ videos: Video[]; total: number; page: number; pages: number }>(
    `/canais/${canalId}/candidatos?page=${page}&limit=${limit}`
  )
export const aprovarVideo = (canalId: string, videoId: string) =>
  request<{ ok: boolean }>(`/canais/${canalId}/aprovar/${videoId}`, { method: 'POST' })

export const getFila = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/fila`)
export const getPublicados = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/publicados`)

// ─── Remodelação ────────────────────────────────────────────────────────────

export const getStatusRemodelacao = (canalId: string, videoId: string) =>
  request<RemodelarStatus>(`/canais/${canalId}/remodelar/${videoId}/status`)

export const transcreverVideo = (canalId: string, videoId: string, force = false) =>
  request<{ transcricao: string; char_count: number; cached: boolean }>(
    `/canais/${canalId}/remodelar/${videoId}/transcrever`,
    { method: 'POST', body: JSON.stringify({ force }) }
  )

export const analisarVideo = (canalId: string, videoId: string, force = false) =>
  request<{ prompt_titulo: string; estrutura_video: string; estrutura_thumb: string; cached: boolean }>(
    `/canais/${canalId}/remodelar/${videoId}/analisar`,
    { method: 'POST', body: JSON.stringify({ force }) }
  )

export const narrarVideo = (canalId: string, videoId: string, voiceId?: string, force = false) =>
  request<{ audio_url: string; duracao_sec: number; cached: boolean }>(
    `/canais/${canalId}/remodelar/${videoId}/narrar`,
    { method: 'POST', body: JSON.stringify({ voice_id: voiceId, force }) }
  )

export const gerarThumbnail = (canalId: string, videoId: string, provider = 'together', force = false) =>
  request<{ thumbnail_url: string; provider_used: string; cached: boolean }>(
    `/canais/${canalId}/remodelar/${videoId}/thumbnail`,
    { method: 'POST', body: JSON.stringify({ image_provider: provider, force }) }
  )

export const gerarSeo = (canalId: string, videoId: string, idioma = 'en') =>
  request<{ descricao: string; tags: string[] }>(
    `/canais/${canalId}/remodelar/${videoId}/gerar-seo`,
    { method: 'POST', body: JSON.stringify({ idioma }) }
  )

export const publicarVideo = (
  canalId: string, videoId: string, titulo: string,
  descricao: string, tags: string[], privacy = 'private'
) =>
  request<{ yt_link: string; status: string }>(
    `/canais/${canalId}/remodelar/${videoId}/publicar`,
    { method: 'POST', body: JSON.stringify({ titulo, descricao, tags, privacy }) }
  )

// ─── SSE helper ─────────────────────────────────────────────────────────────

export async function streamSSE<T>(
  path: string,
  body: object,
  onEvent: (event: string, data: T) => void,
): Promise<void> {
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  if (!res.ok || !res.body) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail: string }).detail || `SSE failed: HTTP ${res.status}`)
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''
    for (const block of blocks) {
      const eventMatch = block.match(/^event:\s*(\w+)/m)
      const dataMatch = block.match(/^data:\s*(.+)$/m)
      if (eventMatch && dataMatch) {
        try {
          onEvent(eventMatch[1], JSON.parse(dataMatch[1]) as T)
        } catch {
          // skip malformed event
        }
      }
    }
  }
}
