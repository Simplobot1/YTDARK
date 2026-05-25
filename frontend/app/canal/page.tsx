'use client'
import { useEffect, useState, useCallback, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { getCandidatos, getFila, minerar, listarFontes, removerFonte } from '@/lib/api'
import { Video } from '@/lib/types'
import { VideoRow } from '@/components/VideoRow'
import { Button } from '@/components/ui/button'
import { isAuthenticated } from '@/lib/auth'
import Link from 'next/link'

const PAGE_LIMIT = 20

function CanalContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const canal = searchParams.get('id') || ''

  const [fila, setFila] = useState<Video[]>([])
  const [candidatos, setCandidatos] = useState<Video[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(0)
  const [loading, setLoading] = useState(false)
  const [minerando, setMinerando] = useState(false)
  const [minerMsg, setMinerMsg] = useState('')
  const [fontes, setFontes] = useState<string[]>([])

  const refresh = useCallback(async (p = 1) => {
    if (!isAuthenticated()) { router.push('/login'); return }
    if (!canal) return
    setLoading(true)
    try {
      const [filaRes, candsRes, fontesRes] = await Promise.all([
        getFila(canal),
        getCandidatos(canal, p, PAGE_LIMIT),
        listarFontes(canal).catch(() => ({ fontes: [] })),
      ])
      setFila(filaRes as Video[])
      setCandidatos(candsRes.videos)
      setTotal(candsRes.total)
      setPage(candsRes.page)
      setPages(candsRes.pages)
      setFontes(fontesRes.fontes)
    } catch {
      // silently handle
    } finally {
      setLoading(false)
    }
  }, [canal, router])

  useEffect(() => { refresh(1) }, [refresh])

  async function handleMinerar() {
    if (fontes.length === 0) {
      setMinerMsg('Nenhuma fonte configurada. Adicione canais na página de Descoberta primeiro.')
      return
    }
    setMinerando(true)
    setMinerMsg('')
    try {
      const res = await minerar(canal)
      if (res.minerados === 0) {
        setMinerMsg('Nenhum vídeo novo encontrado. Tente ampliar os filtros no config do canal.')
      } else {
        setMinerMsg(`${res.minerados} vídeo(s) minerado(s)!`)
      }
      await refresh(1)
    } catch (e: unknown) {
      setMinerMsg(e instanceof Error ? e.message : 'Erro ao minerar')
    } finally {
      setMinerando(false)
    }
  }

  async function handleRemoverFonte(handle: string) {
    try {
      const res = await removerFonte(canal, handle)
      setFontes(res.fontes)
    } catch {}
  }

  function handlePage(p: number) {
    setPage(p)
    refresh(p)
  }

  const allVideos = [...fila, ...candidatos]

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-slate-400 hover:text-white">&#8592; Dashboard</Link>
            <h1 className="text-2xl font-bold text-white">{canal}</h1>
          </div>
          <div className="flex gap-2">
            <Link href={`/canal/dna?id=${canal}`}>
              <Button variant="outline" size="sm">Editar DNA</Button>
            </Link>
            <Button onClick={handleMinerar} disabled={minerando} size="sm">
              {minerando ? 'Minerando...' : 'Minerar Vídeos'}
            </Button>
          </div>
        </div>

        {/* Fontes configuradas */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-300">Canais Fonte</h2>
            <Link href="/descoberta" className="text-xs text-blue-400 hover:text-blue-300">
              + Adicionar fonte
            </Link>
          </div>
          {fontes.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-slate-500 text-sm">Nenhuma fonte configurada.</p>
              <Link href="/descoberta" className="text-blue-400 hover:text-blue-300 text-sm underline mt-1 inline-block">
                Ir para Descoberta para adicionar canais →
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {fontes.map(h => (
                <span key={h} className="flex items-center gap-1.5 bg-slate-800 text-slate-200 text-xs px-2.5 py-1 rounded-full">
                  <a
                    href={`https://www.youtube.com/${h}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-white"
                  >
                    {h}
                  </a>
                  <button
                    onClick={() => handleRemoverFonte(h)}
                    className="text-slate-500 hover:text-red-400 ml-0.5 leading-none"
                    title="Remover fonte"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Feedback mineração */}
        {minerMsg && (
          <div className={`rounded-lg px-4 py-2 text-sm ${
            minerMsg.includes('Erro') || minerMsg.includes('Nenhum')
              ? 'bg-amber-900/40 border border-amber-700 text-amber-300'
              : 'bg-emerald-900/40 border border-emerald-700 text-emerald-300'
          }`}>
            {minerMsg}
          </div>
        )}

        {/* Tabela de vídeos */}
        {loading ? (
          <p className="text-slate-400">Carregando...</p>
        ) : (
          <>
            <div className="bg-slate-900 rounded-lg border border-slate-800">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <span className="text-slate-400 text-sm">{total} candidatos · {fila.length} na fila</span>
              </div>
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
                  {allVideos.map(v => (
                    <VideoRow key={v.video_id} video={v} canalId={canal} onAction={() => refresh(page)} />
                  ))}
                </tbody>
              </table>
              {allVideos.length === 0 && (
                <div className="text-center p-10">
                  <p className="text-slate-400">Nenhum vídeo ainda.</p>
                  {fontes.length > 0 && (
                    <p className="text-slate-500 text-sm mt-1">Clique em <strong className="text-white">Minerar Vídeos</strong> para buscar candidatos.</p>
                  )}
                </div>
              )}
            </div>

            {pages > 1 && (
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm">{total} candidatos</span>
                <div className="flex gap-2 items-center">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => handlePage(page - 1)}>
                    Anterior
                  </Button>
                  <span className="text-slate-400 text-sm">{page} / {pages}</span>
                  <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => handlePage(page + 1)}>
                    Próximo
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function CanalPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Carregando...</div>}>
      <CanalContent />
    </Suspense>
  )
}
