'use client'
import { useEffect, useState, useCallback, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { getCandidatos, getFila, minerar } from '@/lib/api'
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

  const refresh = useCallback(async (p = 1) => {
    if (!isAuthenticated()) { router.push('/login'); return }
    if (!canal) return
    setLoading(true)
    try {
      const [filaRes, candsRes] = await Promise.all([
        getFila(canal),
        getCandidatos(canal, p, PAGE_LIMIT),
      ])
      setFila(filaRes as Video[])
      setCandidatos(candsRes.videos)
      setTotal(candsRes.total)
      setPage(candsRes.page)
      setPages(candsRes.pages)
    } catch {
      // silently handle
    } finally {
      setLoading(false)
    }
  }, [canal, router])

  useEffect(() => { refresh(1) }, [refresh])

  async function handleMinerar() {
    setMinerando(true)
    try { await minerar(canal); await refresh(1) }
    catch (e: unknown) { alert(e instanceof Error ? e.message : 'Erro ao minerar') }
    finally { setMinerando(false) }
  }

  function handlePage(p: number) {
    setPage(p)
    refresh(p)
  }

  const allVideos = [...fila, ...candidatos]

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-slate-400 hover:text-white">&#8592; Dashboard</Link>
            <h1 className="text-2xl font-bold text-white">{canal}</h1>
          </div>
          <div className="flex gap-2">
            <Link href={`/canal/dna?id=${canal}`}>
              <Button variant="outline" size="sm">Editar DNA</Button>
            </Link>
            <Button onClick={handleMinerar} disabled={minerando} size="sm">
              {minerando ? 'Minerando...' : 'Minerar Videos'}
            </Button>
          </div>
        </div>

        {loading ? (
          <p className="text-slate-400">Carregando...</p>
        ) : (
          <>
            <div className="bg-slate-900 rounded-lg border border-slate-800">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="p-3 text-left text-slate-400 text-sm">Score</th>
                    <th className="p-3 text-left text-slate-400 text-sm">Video</th>
                    <th className="p-3 text-left text-slate-400 text-sm">Status</th>
                    <th className="p-3 text-left text-slate-400 text-sm">Acao</th>
                  </tr>
                </thead>
                <tbody>
                  {allVideos.map(v => (
                    <VideoRow key={v.video_id} video={v} canalId={canal} onAction={() => refresh(page)} />
                  ))}
                </tbody>
              </table>
              {allVideos.length === 0 && (
                <p className="text-slate-400 text-center p-8">
                  Nenhum video encontrado. Clique em Minerar Videos para comecar.
                </p>
              )}
            </div>

            {pages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <span className="text-slate-400 text-sm">{total} candidatos no total</span>
                <div className="flex gap-2">
                  <Button
                    variant="outline" size="sm"
                    disabled={page <= 1}
                    onClick={() => handlePage(page - 1)}
                  >
                    Anterior
                  </Button>
                  <span className="text-slate-400 text-sm self-center">
                    {page} / {pages}
                  </span>
                  <Button
                    variant="outline" size="sm"
                    disabled={page >= pages}
                    onClick={() => handlePage(page + 1)}
                  >
                    Proximo
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
