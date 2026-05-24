# YTDARK Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js dashboard for YTDARK — painel de controle multi-canal com descoberta, pipeline de vídeos, editor de DNA e deploy no Cloudflare Pages.

**Architecture:** Next.js 14 App Router com client components para interatividade. `lib/api.ts` centraliza todas as chamadas ao FastAPI backend. Auth via JWT em cookie httpOnly. Deploy estático no Cloudflare Pages via GitHub Actions.

**Tech Stack:** Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui, js-cookie, react-hook-form, zod, @tanstack/react-query, Cloudflare Pages

**Prerequisite:** Backend rodando (plano `2026-05-24-ytdark-backend.md` concluído).

---

## File Structure

```
frontend/
├── app/
│   ├── layout.tsx               ← root layout + providers
│   ├── page.tsx                 ← redirect → /dashboard
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx         ← tela de login
│   ├── dashboard/
│   │   └── page.tsx             ← visão geral de todos os canais
│   ├── canais/
│   │   └── [canal]/
│   │       ├── page.tsx         ← pipeline do canal
│   │       └── dna/
│   │           └── page.tsx     ← editor de Channel DNA
│   └── descoberta/
│       └── page.tsx             ← descoberta de canais por métricas
├── components/
│   ├── ui/                      ← shadcn/ui components (gerados)
│   ├── CanalCard.tsx            ← card de resumo de canal
│   ├── VideoRow.tsx             ← linha de vídeo no pipeline
│   ├── PipelineActions.tsx      ← botões de ação por fase
│   ├── ScoreBadge.tsx           ← badge com score colorido
│   ├── DnaForm.tsx              ← formulário do Channel DNA
│   ├── DiscoveryForm.tsx        ← formulário de descoberta
│   └── CanalCandidatoRow.tsx    ← linha de candidato a canal fonte
├── lib/
│   ├── api.ts                   ← client do FastAPI (fetch + JWT)
│   ├── auth.ts                  ← helpers de auth (getToken, logout)
│   └── types.ts                 ← tipos TypeScript espelhando os modelos Python
├── hooks/
│   ├── useCanais.ts             ← hook: lista de canais
│   ├── useCandidatos.ts         ← hook: candidatos do canal
│   └── usePipeline.ts           ← hook: vídeos em produção
├── middleware.ts                ← protege rotas autenticadas
├── next.config.js               ← output: 'export' para Cloudflare Pages
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.local                   ← NEXT_PUBLIC_API_URL
```

---

### Task F1: Setup Next.js + Cloudflare Pages Config

**Files:**
- Create: `frontend/` (novo diretório)
- Create: `frontend/package.json`, `frontend/next.config.js`, `frontend/.env.local`

- [ ] **Step 1: Criar projeto Next.js dentro de frontend/**

```bash
cd "C:\Users\ricar\projetos\YT DARK"
npx create-next-app@14 frontend --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"
cd frontend
```

- [ ] **Step 2: Instalar dependências**

```bash
npm install js-cookie react-hook-form zod @hookform/resolvers @tanstack/react-query axios
npm install -D @types/js-cookie
npx shadcn-ui@latest init
```
Quando shadcn perguntar:
- Style: Default
- Base color: Slate
- CSS variables: Yes

- [ ] **Step 3: Instalar componentes shadcn necessários**

```bash
npx shadcn-ui@latest add button card input label badge table form toast dialog
```

- [ ] **Step 4: Configurar next.config.js para Cloudflare Pages**

```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
}
module.exports = nextConfig
```

- [ ] **Step 5: Criar frontend/.env.local**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 6: Testar build**

```bash
npm run build
```
Esperado: build sem erros, pasta `out/` criada.

- [ ] **Step 7: Commit**

```bash
cd "C:\Users\ricar\projetos\YT DARK"
git add frontend/
git commit -m "feat: setup Next.js 14 + Tailwind + shadcn + Cloudflare Pages config"
```

---

### Task F2: Tipos TypeScript + API Client

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/auth.ts`

- [ ] **Step 1: Criar frontend/lib/types.ts**

```typescript
// frontend/lib/types.ts

export type VideoStatus =
  | 'candidato' | 'aprovado' | 'minerado' | 'analisado'
  | 'roteiro_gerado' | 'audio_gerado' | 'video_pronto' | 'publicado'

export interface Video {
  video_id: string
  titulo: string
  canal_fonte: string
  views: number
  data_pub: string
  duracao_min: number
  tipo: string
  score: number
  status: VideoStatus
  transcricao?: string
  analise?: Record<string, unknown>
  roteiro_path?: string
  audio_path?: string
  thumbnail_path?: string
  video_path?: string
  drive_link?: string
  yt_link?: string
}

export interface MetricasCanal {
  subscribers: number
  avg_views: number
  engagement_rate: number
  upload_freq_mensal: number
  avg_duration_min: number
  momentum: 'crescendo' | 'estavel' | 'declinando'
}

export interface CanalCandidato {
  handle: string
  nome: string
  channel_id: string
  metricas: MetricasCanal
  score: number
  melhor_video_recente?: Record<string, unknown>
  adicionado: boolean
}

export interface ChannelDNA {
  estilo_visual: string
  tom_voz: string
  paleta_cores: string[]
  intro_max_sec: number
  hook_style: string
  num_pontos: number
  cta_style: string
  thumbnail_formula: string
  thumbnail_fonte: string
  titulo_formula: string
  duracao_alvo_min: number
}

export interface CanalConfig {
  canal_id: string
  youtube_handle: string
  idioma: string
  nicho_keywords: string[]
  canais_fonte: string[]
  tipo_video_padrao: string
  google_sheets_id: string
  google_drive_folder_id: string
}

export interface Keyword {
  termo: string
  volume: number
  competition: number
  seo_score: number
}
```

- [ ] **Step 2: Criar frontend/lib/auth.ts**

```typescript
// frontend/lib/auth.ts
import Cookies from 'js-cookie'

const TOKEN_KEY = 'ytdark_token'

export function getToken(): string | undefined {
  return Cookies.get(TOKEN_KEY)
}

export function setToken(token: string): void {
  Cookies.set(TOKEN_KEY, token, { expires: 1, sameSite: 'strict' })
}

export function removeToken(): void {
  Cookies.remove(TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  return !!getToken()
}
```

- [ ] **Step 3: Criar frontend/lib/api.ts**

```typescript
// frontend/lib/api.ts
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
      ...options.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// Auth
export const login = (email: string, senha: string) =>
  request<{ token: string; email: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha }),
  })

// Canais
export const getCanais = () => request<{ canais: string[] }>('/canais/')
export const getCanalConfig = (id: string) => request<CanalConfig>(`/canais/${id}/config`)
export const getCanalDna = (id: string) => request<ChannelDNA>(`/canais/${id}/dna`)
export const updateCanalDna = (id: string, dna: ChannelDNA) =>
  request<{ ok: boolean }>(`/canais/${id}/dna`, { method: 'PUT', body: JSON.stringify(dna) })

// Descoberta
export const descobrirCanais = (body: object) =>
  request<CanalCandidato[]>('/descobrir-canais', { method: 'POST', body: JSON.stringify(body) })
export const keywordResearch = (canalId: string, nicho: string, idioma: string) =>
  request<{ keywords: Keyword[] }>(`/canais/${canalId}/keywords`, {
    method: 'POST',
    body: JSON.stringify({ nicho, idioma }),
  })

// Mineração
export const minerar = (canalId: string) =>
  request<{ minerados: number; videos: Video[] }>(`/canais/${canalId}/minerar`, { method: 'POST' })
export const getCandidatos = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/candidatos`)
export const aprovarVideo = (canalId: string, videoId: string) =>
  request<{ ok: boolean }>(`/canais/${canalId}/aprovar/${videoId}`, { method: 'POST' })

// Análise
export const analisarVideo = (canalId: string, videoId: string) =>
  request<{ analise: object }>(`/canais/${canalId}/analisar/${videoId}`, { method: 'POST' })
export const getAnalisados = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/analisados`)

// Produção
export const produzirVideo = (canalId: string, videoId: string) =>
  request<{ mp4_url: string }>(`/canais/${canalId}/produzir/${videoId}`, { method: 'POST' })
export const getFila = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/fila`)

// Publicação
export const publicarVideo = (canalId: string, videoId: string) =>
  request<{ yt_link: string }>(`/canais/${canalId}/publicar/${videoId}`, { method: 'POST' })
export const getPublicados = (canalId: string) =>
  request<Video[]>(`/canais/${canalId}/publicados`)
```

- [ ] **Step 4: Commit**

```bash
git add frontend/lib/
git commit -m "feat: types TypeScript + API client + auth helpers"
```

---

### Task F3: Middleware de Auth + Login Page

**Files:**
- Create: `frontend/middleware.ts`
- Create: `frontend/app/(auth)/login/page.tsx`

- [ ] **Step 1: Criar frontend/middleware.ts**

```typescript
// frontend/middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(req: NextRequest) {
  const token = req.cookies.get('ytdark_token')?.value
  const isAuth = req.nextUrl.pathname.startsWith('/login')

  if (!token && !isAuth) {
    return NextResponse.redirect(new URL('/login', req.url))
  }
  if (token && isAuth) {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

- [ ] **Step 2: Criar frontend/app/(auth)/login/page.tsx**

```tsx
// frontend/app/(auth)/login/page.tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login } from '@/lib/api'
import { setToken } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { token } = await login(email, senha)
      setToken(token)
      router.push('/dashboard')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <Card className="w-full max-w-sm bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white text-2xl text-center">🎬 YT DARK</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-slate-300">Email</Label>
              <Input value={email} onChange={e => setEmail(e.target.value)}
                type="email" placeholder="admin@email.com"
                className="bg-slate-800 border-slate-700 text-white" />
            </div>
            <div>
              <Label className="text-slate-300">Senha</Label>
              <Input value={senha} onChange={e => setSenha(e.target.value)}
                type="password" placeholder="••••••"
                className="bg-slate-800 border-slate-700 text-white" />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **Step 3: Criar frontend/app/layout.tsx**

```tsx
// frontend/app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'YT DARK',
  description: 'Sistema de produção de vídeos',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} bg-slate-950 text-white`}>
        {children}
      </body>
    </html>
  )
}
```

- [ ] **Step 4: Criar frontend/app/page.tsx**

```tsx
// frontend/app/page.tsx
import { redirect } from 'next/navigation'
export default function Home() { redirect('/dashboard') }
```

- [ ] **Step 5: Commit**

```bash
git add frontend/middleware.ts frontend/app/
git commit -m "feat: auth middleware + login page"
```

---

### Task F4: Componentes Reutilizáveis

**Files:**
- Create: `frontend/components/ScoreBadge.tsx`
- Create: `frontend/components/VideoRow.tsx`
- Create: `frontend/components/CanalCard.tsx`
- Create: `frontend/components/PipelineActions.tsx`

- [ ] **Step 1: Criar frontend/components/ScoreBadge.tsx**

```tsx
// frontend/components/ScoreBadge.tsx
import { Badge } from '@/components/ui/badge'

export function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? 'bg-green-600' : score >= 60 ? 'bg-yellow-600' : 'bg-red-600'
  return (
    <Badge className={`${color} text-white font-bold`}>
      ⭐ {score.toFixed(0)}
    </Badge>
  )
}
```

- [ ] **Step 2: Criar frontend/components/VideoRow.tsx**

```tsx
// frontend/components/VideoRow.tsx
import { Video } from '@/lib/types'
import { ScoreBadge } from './ScoreBadge'
import { PipelineActions } from './PipelineActions'

const STATUS_LABEL: Record<string, string> = {
  candidato: '⬜ Candidato', aprovado: '🟡 Aprovado', minerado: '🔵 Minerado',
  analisado: '🟣 Analisado', roteiro_gerado: '📝 Roteiro', audio_gerado: '🎙️ Áudio',
  video_pronto: '🎬 Pronto', publicado: '✅ Publicado',
}

interface Props {
  video: Video
  canalId: string
  onAction: () => void
}

export function VideoRow({ video, canalId, onAction }: Props) {
  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/50">
      <td className="p-3">
        <ScoreBadge score={video.score} />
      </td>
      <td className="p-3">
        <p className="font-medium text-sm">{video.titulo}</p>
        <p className="text-xs text-slate-400">{video.canal_fonte} · {video.views.toLocaleString()} views</p>
      </td>
      <td className="p-3 text-sm text-slate-300">{STATUS_LABEL[video.status]}</td>
      <td className="p-3">
        <PipelineActions video={video} canalId={canalId} onAction={onAction} />
      </td>
    </tr>
  )
}
```

- [ ] **Step 3: Criar frontend/components/PipelineActions.tsx**

```tsx
// frontend/components/PipelineActions.tsx
'use client'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Video } from '@/lib/types'
import { aprovarVideo, analisarVideo, produzirVideo, publicarVideo } from '@/lib/api'

interface Props {
  video: Video
  canalId: string
  onAction: () => void
}

export function PipelineActions({ video, canalId, onAction }: Props) {
  const [loading, setLoading] = useState(false)

  async function run(fn: () => Promise<unknown>) {
    setLoading(true)
    try { await fn(); onAction() }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Erro') }
    finally { setLoading(false) }
  }

  if (video.status === 'candidato')
    return <Button size="sm" disabled={loading}
      onClick={() => run(() => aprovarVideo(canalId, video.video_id))}>
      ✓ Aprovar
    </Button>

  if (video.status === 'aprovado')
    return <Button size="sm" disabled={loading}
      onClick={() => run(() => analisarVideo(canalId, video.video_id))}>
      🔍 Analisar
    </Button>

  if (video.status === 'analisado')
    return <Button size="sm" disabled={loading}
      onClick={() => run(() => produzirVideo(canalId, video.video_id))}>
      🎬 Produzir
    </Button>

  if (video.status === 'video_pronto')
    return <Button size="sm" disabled={loading}
      onClick={() => run(() => publicarVideo(canalId, video.video_id))}>
      🚀 Publicar
    </Button>

  if (video.status === 'publicado' && video.yt_link)
    return <a href={video.yt_link} target="_blank" rel="noopener noreferrer"
      className="text-xs text-blue-400 hover:underline">▶ Ver no YouTube</a>

  return <span className="text-xs text-slate-500">Processando...</span>
}
```

- [ ] **Step 4: Criar frontend/components/CanalCard.tsx**

```tsx
// frontend/components/CanalCard.tsx
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Props {
  canalId: string
  prontos: number
  emProducao: number
  candidatos: number
}

export function CanalCard({ canalId, prontos, emProducao, candidatos }: Props) {
  return (
    <Link href={`/canais/${canalId}`}>
      <Card className="bg-slate-900 border-slate-800 hover:border-slate-600 cursor-pointer transition-colors">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            🎬 {canalId}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2 flex-wrap">
          {prontos > 0 && <Badge className="bg-green-700">{prontos} prontos</Badge>}
          {emProducao > 0 && <Badge className="bg-yellow-700">{emProducao} em produção</Badge>}
          {candidatos > 0 && <Badge className="bg-slate-600">{candidatos} candidatos</Badge>}
          {prontos === 0 && emProducao === 0 && candidatos === 0 &&
            <Badge variant="outline">Vazio</Badge>}
        </CardContent>
      </Card>
    </Link>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/
git commit -m "feat: componentes reutilizáveis (ScoreBadge, VideoRow, PipelineActions, CanalCard)"
```

---

### Task F5: Dashboard + Painel do Canal

**Files:**
- Create: `frontend/app/dashboard/page.tsx`
- Create: `frontend/app/canais/[canal]/page.tsx`

- [ ] **Step 1: Criar frontend/app/dashboard/page.tsx**

```tsx
// frontend/app/dashboard/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { getCanais, getCandidatos, getFila, getPublicados } from '@/lib/api'
import { CanalCard } from '@/components/CanalCard'
import { Button } from '@/components/ui/button'
import { removeToken } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Dashboard() {
  const router = useRouter()
  const [canais, setCanais] = useState<string[]>([])
  const [stats, setStats] = useState<Record<string, { prontos: number; emProducao: number; candidatos: number }>>({})

  useEffect(() => {
    getCanais().then(async ({ canais: ids }) => {
      setCanais(ids)
      const statsMap: typeof stats = {}
      for (const id of ids) {
        const [candidatos, fila, publicados] = await Promise.all([
          getCandidatos(id).catch(() => []),
          getFila(id).catch(() => []),
          getPublicados(id).catch(() => []),
        ])
        statsMap[id] = {
          candidatos: candidatos.filter(v => v.status === 'candidato').length,
          emProducao: fila.length,
          prontos: fila.filter(v => v.status === 'video_pronto').length,
        }
      }
      setStats(statsMap)
    })
  }, [])

  function logout() {
    removeToken()
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">🎬 YT DARK</h1>
          <div className="flex gap-3">
            <Link href="/descoberta">
              <Button variant="outline">🔍 Descobrir Canais</Button>
            </Link>
            <Button variant="ghost" onClick={logout}>Sair</Button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {canais.map(id => (
            <CanalCard key={id} canalId={id} {...(stats[id] || { prontos: 0, emProducao: 0, candidatos: 0 })} />
          ))}
        </div>
        {canais.length === 0 && (
          <p className="text-slate-400 text-center mt-16">Nenhum canal configurado ainda.</p>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Criar frontend/app/canais/[canal]/page.tsx**

```tsx
// frontend/app/canais/[canal]/page.tsx
'use client'
import { useEffect, useState, useCallback } from 'react'
import { getCandidatos, getFila, minerar } from '@/lib/api'
import { Video } from '@/lib/types'
import { VideoRow } from '@/components/VideoRow'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export default function CanalPage({ params }: { params: { canal: string } }) {
  const { canal } = params
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(false)
  const [minerando, setMinerando] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const [cands, fila] = await Promise.all([getCandidatos(canal), getFila(canal)])
      const todos = [...fila, ...cands.filter(v => v.status === 'candidato')]
      todos.sort((a, b) => b.score - a.score)
      setVideos(todos)
    } finally {
      setLoading(false)
    }
  }, [canal])

  useEffect(() => { refresh() }, [refresh])

  async function handleMinerar() {
    setMinerando(true)
    try { await minerar(canal); await refresh() }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Erro ao minerar') }
    finally { setMinerando(false) }
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-slate-400 hover:text-white">← Dashboard</Link>
            <h1 className="text-2xl font-bold text-white">🎬 {canal}</h1>
          </div>
          <div className="flex gap-2">
            <Link href={`/canais/${canal}/dna`}>
              <Button variant="outline" size="sm">🧬 Editar DNA</Button>
            </Link>
            <Button onClick={handleMinerar} disabled={minerando} size="sm">
              {minerando ? '⏳ Minerando...' : '⛏️ Minerar Vídeos'}
            </Button>
          </div>
        </div>

        {loading ? (
          <p className="text-slate-400">Carregando...</p>
        ) : (
          <div className="bg-slate-900 rounded-lg border border-slate-800">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="p-3 text-left text-slate-400 text-sm">Score</th>
                  <th className="p-3 text-left text-slate-400 text-sm">Vídeo</th>
                  <th className="p-3 text-left text-slate-400 text-sm">Status</th>
                  <th className="p-3 text-left text-slate-400 text-sm">Ação</th>
                </tr>
              </thead>
              <tbody>
                {videos.map(v => (
                  <VideoRow key={v.video_id} video={v} canalId={canal} onAction={refresh} />
                ))}
              </tbody>
            </table>
            {videos.length === 0 && (
              <p className="text-slate-400 text-center p-8">
                Nenhum vídeo encontrado. Clique em "Minerar Vídeos" para começar.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/dashboard/ frontend/app/canais/
git commit -m "feat: dashboard geral + painel por canal com pipeline completo"
```

---

### Task F6: Descoberta de Canais

**Files:**
- Create: `frontend/app/descoberta/page.tsx`
- Create: `frontend/components/CanalCandidatoRow.tsx`

- [ ] **Step 1: Criar frontend/components/CanalCandidatoRow.tsx**

```tsx
// frontend/components/CanalCandidatoRow.tsx
import { CanalCandidato } from '@/lib/types'
import { ScoreBadge } from './ScoreBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface Props {
  candidato: CanalCandidato
  onAdicionar: (handle: string) => void
}

const MOMENTUM_COLOR = { crescendo: 'bg-green-700', estavel: 'bg-slate-600', declinando: 'bg-red-700' }

export function CanalCandidatoRow({ candidato: c, onAdicionar }: Props) {
  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/50">
      <td className="p-3"><ScoreBadge score={c.score} /></td>
      <td className="p-3">
        <p className="font-medium">{c.handle}</p>
        <p className="text-xs text-slate-400">{c.nome}</p>
      </td>
      <td className="p-3 text-sm">{c.metricas.subscribers.toLocaleString()} subs</td>
      <td className="p-3 text-sm">{Math.round(c.metricas.avg_views).toLocaleString()} avg</td>
      <td className="p-3 text-sm">{c.metricas.engagement_rate.toFixed(1)}%</td>
      <td className="p-3">
        <Badge className={MOMENTUM_COLOR[c.metricas.momentum]}>{c.metricas.momentum}</Badge>
      </td>
      <td className="p-3">
        {c.adicionado
          ? <span className="text-green-400 text-xs">✓ Adicionado</span>
          : <Button size="sm" onClick={() => onAdicionar(c.handle)}>+ Adicionar</Button>
        }
      </td>
    </tr>
  )
}
```

- [ ] **Step 2: Criar frontend/app/descoberta/page.tsx**

```tsx
// frontend/app/descoberta/page.tsx
'use client'
import { useState } from 'react'
import { descobrirCanais } from '@/lib/api'
import { CanalCandidato } from '@/lib/types'
import { CanalCandidatoRow } from '@/components/CanalCandidatoRow'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

export default function DescobertaPage() {
  const [estrategia, setEstrategia] = useState<'categoria' | 'seed'>('categoria')
  const [nicho, setNicho] = useState('personal finance')
  const [seed, setSeed] = useState('')
  const [minViews, setMinViews] = useState(50000)
  const [minSubs, setMinSubs] = useState(100000)
  const [loading, setLoading] = useState(false)
  const [candidatos, setCandidatos] = useState<CanalCandidato[]>([])

  async function buscar() {
    setLoading(true)
    try {
      const result = await descobrirCanais({
        estrategia,
        nicho,
        idioma: 'en',
        seed_channel: estrategia === 'seed' ? seed : undefined,
        filtros: { subscribers_min: minSubs, avg_views_min: minViews,
                   upload_freq_min: 4, avg_duration_min_min: 8, avg_duration_max_min: 20 },
        top_n: 20,
      })
      setCandidatos(result)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Erro ao buscar canais')
    } finally {
      setLoading(false)
    }
  }

  function handleAdicionar(handle: string) {
    setCandidatos(prev => prev.map(c => c.handle === handle ? { ...c, adicionado: true } : c))
    alert(`${handle} adicionado! Configure-o manualmente no config.json do canal.`)
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard" className="text-slate-400 hover:text-white">← Dashboard</Link>
          <h1 className="text-2xl font-bold text-white">🔍 Descobrir Canais Fonte</h1>
        </div>

        <Card className="bg-slate-900 border-slate-800 mb-6">
          <CardHeader><CardTitle>Filtros de Busca</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <Label>Estratégia</Label>
              <div className="flex gap-2 mt-1">
                {(['categoria', 'seed'] as const).map(e => (
                  <button key={e} onClick={() => setEstrategia(e)}
                    className={`px-3 py-1 rounded text-sm ${estrategia === e ? 'bg-blue-600' : 'bg-slate-700'}`}>
                    {e}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label>Nicho</Label>
              <Input value={nicho} onChange={e => setNicho(e.target.value)}
                className="bg-slate-800 border-slate-700" />
            </div>
            {estrategia === 'seed' && (
              <div>
                <Label>Canal Seed</Label>
                <Input value={seed} onChange={e => setSeed(e.target.value)}
                  placeholder="@CasuallyFinance"
                  className="bg-slate-800 border-slate-700" />
              </div>
            )}
            <div>
              <Label>Min. Views Médio</Label>
              <Input type="number" value={minViews} onChange={e => setMinViews(+e.target.value)}
                className="bg-slate-800 border-slate-700" />
            </div>
            <div>
              <Label>Min. Inscritos</Label>
              <Input type="number" value={minSubs} onChange={e => setMinSubs(+e.target.value)}
                className="bg-slate-800 border-slate-700" />
            </div>
            <div className="flex items-end">
              <Button onClick={buscar} disabled={loading} className="w-full">
                {loading ? '⏳ Buscando...' : '🔍 Buscar Canais'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {candidatos.length > 0 && (
          <div className="bg-slate-900 rounded-lg border border-slate-800">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  {['Score','Handle','Inscritos','Avg Views','Engagement','Momentum',''].map(h => (
                    <th key={h} className="p-3 text-left text-slate-400 text-sm">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {candidatos.map(c => (
                  <CanalCandidatoRow key={c.channel_id} candidato={c} onAdicionar={handleAdicionar} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/descoberta/ frontend/components/CanalCandidatoRow.tsx
git commit -m "feat: tela de descoberta de canais por métricas"
```

---

### Task F7: Editor de Channel DNA

**Files:**
- Create: `frontend/app/canais/[canal]/dna/page.tsx`

- [ ] **Step 1: Criar frontend/app/canais/[canal]/dna/page.tsx**

```tsx
// frontend/app/canais/[canal]/dna/page.tsx
'use client'
import { useEffect, useState } from 'react'
import { getCanalDna, updateCanalDna } from '@/lib/api'
import { ChannelDNA } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

export default function DnaPage({ params }: { params: { canal: string } }) {
  const { canal } = params
  const [dna, setDna] = useState<ChannelDNA | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => { getCanalDna(canal).then(setDna) }, [canal])

  function update(field: keyof ChannelDNA, value: unknown) {
    setDna(prev => prev ? { ...prev, [field]: value } : prev)
    setSaved(false)
  }

  async function save() {
    if (!dna) return
    setSaving(true)
    try {
      await updateCanalDna(canal, dna)
      setSaved(true)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Erro ao salvar DNA')
    } finally {
      setSaving(false)
    }
  }

  if (!dna) return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Carregando...</div>

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Link href={`/canais/${canal}`} className="text-slate-400 hover:text-white">← Pipeline</Link>
          <h1 className="text-2xl font-bold text-white">🧬 Channel DNA — {canal}</h1>
        </div>

        <div className="space-y-4">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader><CardTitle>Identidade Visual</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <Label>Estilo Visual</Label>
                <select value={dna.estilo_visual} onChange={e => update('estilo_visual', e.target.value)}
                  className="w-full mt-1 p-2 bg-slate-800 border border-slate-700 rounded text-white">
                  <option value="whiteboard">Whiteboard</option>
                  <option value="talking_head">Talking Head</option>
                  <option value="slides">Slides</option>
                </select>
              </div>
              <div>
                <Label>Duração Alvo (min)</Label>
                <Input type="number" value={dna.duracao_alvo_min}
                  onChange={e => update('duracao_alvo_min', +e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>Tom de Voz</Label>
                <Input value={dna.tom_voz} onChange={e => update('tom_voz', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader><CardTitle>Estrutura do Roteiro</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <Label>Hook Style</Label>
                <Input value={dna.hook_style} onChange={e => update('hook_style', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div>
                <Label>Nº de Pontos</Label>
                <Input type="number" value={dna.num_pontos}
                  onChange={e => update('num_pontos', +e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>Fórmula de Título</Label>
                <Input value={dna.titulo_formula} onChange={e => update('titulo_formula', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>CTA Style</Label>
                <Input value={dna.cta_style} onChange={e => update('cta_style', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader><CardTitle>Thumbnail</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <Label>Fórmula Visual</Label>
                <Input value={dna.thumbnail_formula} onChange={e => update('thumbnail_formula', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div>
                <Label>Fonte</Label>
                <Input value={dna.thumbnail_fonte} onChange={e => update('thumbnail_fonte', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>Cores Principais (hex)</Label>
                <div className="flex gap-2 mt-1">
                  {dna.paleta_cores.map((cor, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <div className="w-6 h-6 rounded" style={{ backgroundColor: cor }} />
                      <Input value={cor} onChange={e => {
                        const novas = [...dna.paleta_cores]
                        novas[i] = e.target.value
                        update('paleta_cores', novas)
                      }} className="bg-slate-800 border-slate-700 w-28" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Button onClick={save} disabled={saving} className="w-full">
            {saving ? 'Salvando...' : saved ? '✓ DNA Salvo!' : '💾 Salvar DNA'}
          </Button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/canais/
git commit -m "feat: editor de Channel DNA com formulário visual"
```

---

### Task F8: Deploy no Cloudflare Pages

**Files:**
- Create: `.github/workflows/deploy-frontend.yml`

- [ ] **Step 1: Criar .github/workflows/deploy-frontend.yml**

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend to Cloudflare Pages

on:
  push:
    branches: [main]
    paths: ['frontend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Build
        working-directory: frontend
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: ytdark
          directory: frontend/out
```

- [ ] **Step 2: Configurar Cloudflare Pages**

1. Acessa [dash.cloudflare.com](https://dash.cloudflare.com)
2. Workers & Pages → Create application → Pages → Connect to Git
3. Seleciona o repo `Simplobot1/YTDARK`
4. Build settings:
   - Build command: `cd frontend && npm ci && npm run build`
   - Build output directory: `frontend/out`
5. Environment variables: `NEXT_PUBLIC_API_URL` = URL do seu VPS

- [ ] **Step 3: Adicionar secrets no GitHub**

Em `github.com/Simplobot1/YTDARK/settings/secrets/actions`:
- `API_URL` = `http://SEU_VPS_IP:8000`
- `CLOUDFLARE_API_TOKEN` = token da Cloudflare
- `CLOUDFLARE_ACCOUNT_ID` = account ID da Cloudflare

- [ ] **Step 4: Commit e push para disparar deploy**

```bash
git add .github/
git commit -m "ci: deploy automático frontend no Cloudflare Pages"
git push origin main
```

Esperado: GitHub Actions executa, frontend aparece em `ytdark.pages.dev`.

---

**Frontend completo. Sistema YT DARK 100% implementado.**
