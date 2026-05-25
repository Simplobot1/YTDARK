'use client'

import { Suspense, useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { isAuthenticated } from '@/lib/auth'
import {
  getStatusRemodelacao,
  transcreverVideo,
  analisarVideo,
  narrarVideo,
  gerarThumbnail,
  gerarSeo,
  publicarVideo,
  streamSSE,
} from '@/lib/api'
import type { RemodelarStatus } from '@/lib/types'

type StepId = 1 | 2 | 3 | 4 | 5 | 6 | 7
type StepState = 'pending' | 'running' | 'done' | 'error'

interface StepDef {
  id: StepId
  label: string
  has: keyof Pick<RemodelarStatus, 'tem_transcricao' | 'tem_analise' | 'tem_roteiro' | 'tem_audio' | 'tem_thumbnail' | 'tem_video' | 'tem_yt_link'>
}

const STEPS: StepDef[] = [
  { id: 1, label: 'Transcrever', has: 'tem_transcricao' },
  { id: 2, label: 'Analisar', has: 'tem_analise' },
  { id: 3, label: 'Roteiro', has: 'tem_roteiro' },
  { id: 4, label: 'Voz', has: 'tem_audio' },
  { id: 5, label: 'Thumbnail', has: 'tem_thumbnail' },
  { id: 6, label: 'Vídeo', has: 'tem_video' },
  { id: 7, label: 'Publicar', has: 'tem_yt_link' },
]

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function StepIndicator({
  step,
  state,
  active,
  onClick,
}: {
  step: StepDef
  state: StepState
  active: boolean
  onClick: () => void
}) {
  const icon = state === 'done' ? '✓' : state === 'running' ? '⟳' : state === 'error' ? '!' : step.id
  const ring = active
    ? 'ring-2 ring-blue-500'
    : state === 'done'
      ? 'ring-1 ring-emerald-600'
      : 'ring-1 ring-slate-700'
  const bg = state === 'done'
    ? 'bg-emerald-600 text-white'
    : state === 'running'
      ? 'bg-blue-600 text-white animate-pulse'
      : state === 'error'
        ? 'bg-red-700 text-white'
        : 'bg-slate-800 text-slate-300'

  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-1 px-1 transition-opacity ${active ? 'opacity-100' : 'opacity-70 hover:opacity-100'}`}
    >
      <span className={`flex items-center justify-center w-9 h-9 rounded-full text-sm font-semibold ${bg} ${ring}`}>
        {icon}
      </span>
      <span className={`text-[10px] ${active ? 'text-white font-semibold' : 'text-slate-400'}`}>
        {step.label}
      </span>
    </button>
  )
}

function RemodelarContent() {
  const params = useSearchParams()
  const canal = params.get('canal') || ''
  const video = params.get('video') || ''

  const [status, setStatus] = useState<RemodelarStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [authed, setAuthed] = useState(false)
  const [currentStep, setCurrentStep] = useState<StepId>(1)
  const [error, setError] = useState('')

  // Step-specific state
  const [running, setRunning] = useState(false)
  const [transcricao, setTranscricao] = useState('')
  const [analise, setAnalise] = useState<{ prompt_titulo?: string; estrutura_video?: string; estrutura_thumb?: string } | null>(null)
  const [roteiro, setRoteiro] = useState('')
  const [tituloGerado, setTituloGerado] = useState('')
  const [idioma, setIdioma] = useState('en')
  const [tituloOverride, setTituloOverride] = useState('')
  const [progressMsg, setProgressMsg] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [voiceId, setVoiceId] = useState('')
  const [thumbUrl, setThumbUrl] = useState('')
  const [imageProvider, setImageProvider] = useState<'together' | 'dalle'>('together')
  const [videoUrl, setVideoUrl] = useState('')
  const [seoTitulo, setSeoTitulo] = useState('')
  const [seoDescricao, setSeoDescricao] = useState('')
  const [seoTags, setSeoTags] = useState<string[]>([])
  const [tagsInput, setTagsInput] = useState('')
  const [ytLink, setYtLink] = useState('')

  // Auth check
  useEffect(() => {
    setAuthed(isAuthenticated())
  }, [])

  const refreshStatus = useCallback(async () => {
    if (!canal || !video) return
    try {
      const s = await getStatusRemodelacao(canal, video)
      setStatus(s)
      // Determina step inicial: primeiro pendente
      const firstPending = STEPS.find(st => !s[st.has])
      setCurrentStep(firstPending ? firstPending.id : 7)
      if (s.titulo) {
        setSeoTitulo(prev => prev || s.titulo)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar status')
    } finally {
      setLoading(false)
    }
  }, [canal, video])

  useEffect(() => {
    if (!canal || !video) {
      setLoading(false)
      return
    }
    refreshStatus()
  }, [canal, video, refreshStatus])

  function stepState(stepId: StepId): StepState {
    if (!status) return 'pending'
    const step = STEPS.find(s => s.id === stepId)
    if (!step) return 'pending'
    if (running && stepId === currentStep) return 'running'
    if (status[step.has]) return 'done'
    return 'pending'
  }

  // ─── Actions ──────────────────────────────────────────────────────────────

  async function runTranscrever(force = false) {
    setRunning(true)
    setError('')
    try {
      const res = await transcreverVideo(canal, video, force)
      setTranscricao(res.transcricao)
      await refreshStatus()
      if (!force) setCurrentStep(2)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runAnalisar(force = false) {
    setRunning(true)
    setError('')
    try {
      const res = await analisarVideo(canal, video, force)
      setAnalise(res)
      await refreshStatus()
      if (!force) setCurrentStep(3)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runRoteiro(force = false) {
    setRunning(true)
    setError('')
    setProgressMsg('')
    setRoteiro('')
    try {
      const path = `/canais/${canal}/remodelar/${video}/roteirizar`
      type Evt = { roteiro?: string; titulo?: string; step?: string; detail?: string; char_count?: number }
      await streamSSE<Evt>(
        path,
        { idioma, force, titulo_novo: tituloOverride || undefined },
        (event, data) => {
          if (event === 'progress') {
            setProgressMsg(data.step || '')
            if (data.titulo) setTituloGerado(data.titulo)
          } else if (event === 'done') {
            setRoteiro(data.roteiro || '')
            if (data.titulo) setTituloGerado(data.titulo)
            setProgressMsg('')
          } else if (event === 'error') {
            setError(data.detail || 'Erro no roteiro')
            setProgressMsg('')
          }
        },
      )
      await refreshStatus()
      if (!force && !error) setCurrentStep(4)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runNarrar(force = false) {
    setRunning(true)
    setError('')
    try {
      const res = await narrarVideo(canal, video, voiceId || undefined, force)
      setAudioUrl(`${BASE}${res.audio_url}`)
      await refreshStatus()
      if (!force) setCurrentStep(5)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runThumb(force = false) {
    setRunning(true)
    setError('')
    try {
      const res = await gerarThumbnail(canal, video, imageProvider, force)
      setThumbUrl(`${BASE}${res.thumbnail_url}`)
      await refreshStatus()
      if (!force) setCurrentStep(6)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runMontar(force = false) {
    setRunning(true)
    setError('')
    setProgressMsg('')
    try {
      const path = `/canais/${canal}/remodelar/${video}/montar`
      type Evt = { video_url?: string; step?: string; detail?: string; size_bytes?: number }
      await streamSSE<Evt>(
        path,
        { force },
        (event, data) => {
          if (event === 'progress') setProgressMsg(data.step || '')
          else if (event === 'done') {
            if (data.video_url) setVideoUrl(`${BASE}${data.video_url}`)
            setProgressMsg('')
          } else if (event === 'error') {
            setError(data.detail || 'Erro na montagem')
            setProgressMsg('')
          }
        },
      )
      await refreshStatus()
      if (!force && !error) setCurrentStep(7)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runGerarSeo() {
    setRunning(true)
    setError('')
    try {
      const res = await gerarSeo(canal, video, idioma)
      setSeoDescricao(res.descricao || '')
      setSeoTags(res.tags || [])
      setTagsInput((res.tags || []).join(', '))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  async function runPublicar() {
    setRunning(true)
    setError('')
    try {
      const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean)
      const res = await publicarVideo(canal, video, seoTitulo, seoDescricao, tags, 'private')
      setYtLink(res.yt_link)
      await refreshStatus()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro')
    } finally {
      setRunning(false)
    }
  }

  // ─── Render guards ────────────────────────────────────────────────────────

  if (!authed) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Link href="/login" className="text-blue-400 hover:underline">Faça login para continuar</Link>
      </div>
    )
  }

  if (!canal || !video) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Parâmetros faltando. Use <code className="ml-1 mr-1 text-amber-300">?canal=&video=</code>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        Carregando...
      </div>
    )
  }

  // ─── Step renderer ────────────────────────────────────────────────────────

  function renderStep() {
    if (!status) return null

    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">1. Transcrever vídeo fonte</h2>
            <p className="text-slate-400 text-sm">
              Busca a transcrição diretamente do YouTube — sem download de áudio.
            </p>
            {status.tem_transcricao && (
              <div className="bg-slate-900 border border-slate-800 rounded p-3">
                <p className="text-emerald-400 text-sm mb-2">✓ Transcrição já capturada</p>
                {transcricao && (
                  <pre className="text-slate-300 text-xs max-h-40 overflow-y-auto whitespace-pre-wrap">
                    {transcricao.slice(0, 800)}{transcricao.length > 800 ? '…' : ''}
                  </pre>
                )}
              </div>
            )}
            <div className="flex gap-2">
              {!status.tem_transcricao ? (
                <Button disabled={running} onClick={() => runTranscrever(false)}>
                  {running ? 'Transcrevendo...' : 'Transcrever'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setCurrentStep(2)}>Próximo →</Button>
                  <Button variant="outline" disabled={running} onClick={() => runTranscrever(true)}>
                    Refazer
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">2. Analisar padrões do canal</h2>
            <p className="text-slate-400 text-sm">
              GPT-4o lê título + transcrição + thumbnail e extrai os padrões do canal fonte.
            </p>
            {status.tem_analise && analise && (
              <div className="space-y-2 text-sm">
                <div className="bg-slate-900 border border-slate-800 rounded p-3">
                  <p className="text-emerald-400 text-xs uppercase mb-1">Padrão de título</p>
                  <p className="text-slate-200">{analise.prompt_titulo}</p>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded p-3">
                  <p className="text-emerald-400 text-xs uppercase mb-1">Estrutura do vídeo</p>
                  <p className="text-slate-200 whitespace-pre-wrap">{analise.estrutura_video}</p>
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded p-3">
                  <p className="text-emerald-400 text-xs uppercase mb-1">Estilo da thumbnail</p>
                  <p className="text-slate-200">{analise.estrutura_thumb}</p>
                </div>
              </div>
            )}
            <div className="flex gap-2">
              {!status.tem_analise ? (
                <Button disabled={running || !status.tem_transcricao} onClick={() => runAnalisar(false)}>
                  {running ? 'Analisando...' : 'Analisar'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setCurrentStep(3)}>Próximo →</Button>
                  <Button variant="outline" disabled={running} onClick={() => runAnalisar(true)}>
                    Refazer
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">3. Gerar roteiro dark</h2>
            <p className="text-slate-400 text-sm">
              GPT-4o gera 20-30k caracteres seguindo o padrão do canal e censura criativa do nicho dark.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <Label className="text-slate-300 text-xs">Idioma</Label>
                <select
                  value={idioma}
                  onChange={e => setIdioma(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm"
                >
                  <option value="en">Inglês</option>
                  <option value="pt">Português</option>
                  <option value="es">Espanhol</option>
                </select>
              </div>
              <div>
                <Label className="text-slate-300 text-xs">Título customizado (opcional)</Label>
                <Input
                  value={tituloOverride}
                  onChange={e => setTituloOverride(e.target.value)}
                  placeholder="Deixe vazio para gerar via IA"
                  className="bg-slate-800 border-slate-700 mt-1"
                />
              </div>
            </div>
            {tituloGerado && (
              <div className="bg-slate-900 border border-slate-800 rounded p-3">
                <p className="text-emerald-400 text-xs uppercase mb-1">Título gerado</p>
                <p className="text-white">{tituloGerado}</p>
              </div>
            )}
            {progressMsg && (
              <div className="bg-blue-900/40 border border-blue-700 rounded p-3">
                <p className="text-blue-300 text-sm animate-pulse">⟳ {progressMsg}…</p>
              </div>
            )}
            {roteiro && (
              <div className="bg-slate-900 border border-slate-800 rounded p-3">
                <p className="text-emerald-400 text-xs uppercase mb-1">Roteiro ({roteiro.length} chars)</p>
                <pre className="text-slate-300 text-xs max-h-60 overflow-y-auto whitespace-pre-wrap">
                  {roteiro.slice(0, 2000)}{roteiro.length > 2000 ? '…' : ''}
                </pre>
              </div>
            )}
            <div className="flex gap-2">
              {!status.tem_roteiro ? (
                <Button disabled={running || !status.tem_analise} onClick={() => runRoteiro(false)}>
                  {running ? 'Gerando...' : 'Gerar Roteiro'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setCurrentStep(4)}>Próximo →</Button>
                  <Button variant="outline" disabled={running} onClick={() => runRoteiro(true)}>
                    Refazer
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 4:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">4. Gerar narração</h2>
            <p className="text-slate-400 text-sm">
              ElevenLabs converte o roteiro em MP3. Voz padrão configurada no servidor.
            </p>
            <div>
              <Label className="text-slate-300 text-xs">Voice ID (opcional)</Label>
              <Input
                value={voiceId}
                onChange={e => setVoiceId(e.target.value)}
                placeholder="Padrão: voz configurada no servidor"
                className="bg-slate-800 border-slate-700 mt-1"
              />
            </div>
            {(audioUrl || status.tem_audio) && (
              <div className="bg-slate-900 border border-slate-800 rounded p-3">
                <p className="text-emerald-400 text-xs uppercase mb-2">Áudio gerado</p>
                {audioUrl ? (
                  <audio controls src={audioUrl} className="w-full" />
                ) : (
                  <p className="text-slate-400 text-xs">(salvo em cache)</p>
                )}
              </div>
            )}
            <div className="flex gap-2">
              {!status.tem_audio ? (
                <Button disabled={running || !status.tem_roteiro} onClick={() => runNarrar(false)}>
                  {running ? 'Narrando...' : 'Gerar Narração'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setCurrentStep(5)}>Próximo →</Button>
                  <Button variant="outline" disabled={running} onClick={() => runNarrar(true)}>
                    Refazer
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 5:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">5. Gerar thumbnail</h2>
            <p className="text-slate-400 text-sm">
              Geração baseada no estilo extraído do canal fonte. Together (FLUX, grátis) ou DALL-E 3.
            </p>
            <div>
              <Label className="text-slate-300 text-xs">Provider</Label>
              <select
                value={imageProvider}
                onChange={e => setImageProvider(e.target.value as 'together' | 'dalle')}
                className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm"
              >
                <option value="together">Together (FLUX, grátis)</option>
                <option value="dalle">DALL-E 3 (OpenAI)</option>
              </select>
            </div>
            {(thumbUrl || status.tem_thumbnail) && (
              <div className="bg-slate-900 border border-slate-800 rounded p-3">
                <p className="text-emerald-400 text-xs uppercase mb-2">Thumbnail gerada</p>
                {thumbUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={thumbUrl} alt="thumbnail" className="max-w-full rounded" />
                ) : (
                  <p className="text-slate-400 text-xs">(salva em cache)</p>
                )}
              </div>
            )}
            <div className="flex gap-2">
              {!status.tem_thumbnail ? (
                <Button disabled={running} onClick={() => runThumb(false)}>
                  {running ? 'Gerando...' : 'Gerar Thumbnail'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setCurrentStep(6)}>Próximo →</Button>
                  <Button variant="outline" disabled={running} onClick={() => runThumb(true)}>
                    Refazer
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 6:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">6. Montar vídeo final</h2>
            <p className="text-slate-400 text-sm">
              FFmpeg combina thumbnail (loop) + narração + música de fundo (se configurada).
            </p>
            {progressMsg && (
              <div className="bg-blue-900/40 border border-blue-700 rounded p-3">
                <p className="text-blue-300 text-sm animate-pulse">⟳ {progressMsg}…</p>
              </div>
            )}
            {(videoUrl || status.tem_video) && (
              <div className="bg-slate-900 border border-slate-800 rounded p-3">
                <p className="text-emerald-400 text-xs uppercase mb-2">Vídeo final</p>
                {videoUrl ? (
                  <video controls src={videoUrl} className="max-w-full rounded" />
                ) : (
                  <p className="text-slate-400 text-xs">(salvo em cache)</p>
                )}
              </div>
            )}
            <div className="flex gap-2">
              {!status.tem_video ? (
                <Button disabled={running || !status.tem_audio || !status.tem_thumbnail} onClick={() => runMontar(false)}>
                  {running ? 'Montando...' : 'Montar Vídeo'}
                </Button>
              ) : (
                <>
                  <Button onClick={() => setCurrentStep(7)}>Próximo →</Button>
                  <Button variant="outline" disabled={running} onClick={() => runMontar(true)}>
                    Refazer
                  </Button>
                </>
              )}
            </div>
          </div>
        )

      case 7:
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-white">7. Publicar no YouTube</h2>
            <p className="text-slate-400 text-sm">
              Geramos descrição e tags otimizadas para SEO — você revisa antes de publicar.
            </p>
            <div>
              <Label className="text-slate-300 text-xs">Título</Label>
              <Input
                value={seoTitulo}
                onChange={e => setSeoTitulo(e.target.value)}
                className="bg-slate-800 border-slate-700 mt-1"
                placeholder="Título no YouTube"
              />
            </div>
            <div>
              <Label className="text-slate-300 text-xs">Descrição</Label>
              <textarea
                value={seoDescricao}
                onChange={e => setSeoDescricao(e.target.value)}
                rows={6}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm mt-1"
                placeholder="Descrição do vídeo"
              />
            </div>
            <div>
              <Label className="text-slate-300 text-xs">Tags (separadas por vírgula)</Label>
              <Input
                value={tagsInput}
                onChange={e => setTagsInput(e.target.value)}
                className="bg-slate-800 border-slate-700 mt-1"
                placeholder="tag1, tag2, tag3"
              />
              {seoTags.length > 0 && (
                <p className="text-slate-500 text-xs mt-1">{seoTags.length} tags sugeridas pela IA</p>
              )}
            </div>

            {ytLink ? (
              <div className="bg-emerald-900/40 border border-emerald-700 rounded p-4">
                <p className="text-emerald-300 text-sm font-medium mb-2">Publicado!</p>
                <a href={ytLink} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline break-all">
                  {ytLink}
                </a>
              </div>
            ) : (
              <div className="flex gap-2 flex-wrap">
                <Button variant="outline" disabled={running} onClick={runGerarSeo}>
                  {running ? '...' : 'Gerar SEO via IA'}
                </Button>
                <Button disabled={running || !seoTitulo || !seoDescricao || !status.tem_video} onClick={runPublicar}>
                  {running ? 'Publicando...' : 'Publicar no YouTube'}
                </Button>
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-3xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href={`/canal?id=${canal}`} className="text-slate-400 hover:text-white">&#8592; {canal}</Link>
          <div>
            <h1 className="text-2xl font-bold text-white">Remodelar Vídeo</h1>
            <p className="text-slate-500 text-xs mt-0.5">{status?.titulo || video}</p>
          </div>
        </div>

        {/* Step bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            {STEPS.map(step => (
              <StepIndicator
                key={step.id}
                step={step}
                state={stepState(step.id)}
                active={step.id === currentStep}
                onClick={() => setCurrentStep(step.id)}
              />
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900/40 border border-red-700 rounded p-3">
            <p className="text-red-300 text-sm">Erro: {error}</p>
          </div>
        )}

        {/* Step content */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          {renderStep()}
        </div>
      </div>
    </div>
  )
}

export default function RemodelarPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Carregando...</div>}>
      <RemodelarContent />
    </Suspense>
  )
}
