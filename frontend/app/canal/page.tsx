'use client'
import { useEffect, useState, useCallback, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { getCandidatos, getFila, minerar } from '@/lib/api'
import { Video } from '@/lib/types'
import { VideoRow } from '@/components/VideoRow'
import { Button } from '@/components/ui/button'
import { isAuthenticated } from '@/lib/auth'
import Link from 'next/link'

function CanalContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const canal = searchParams.get('id') || ''
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(false)
  const [minerando, setMinerando] = useState(false)

  const refresh = useCallback(async () => {
    if (!isAuthenticated()) { router.push('/login'); return }
    if (!canal) return
    setLoading(true)
    try {
      const [cands, fila] = await Promise.all([getCandidatos(canal), getFila(canal)])
      const todos = [...fila, ...cands.filter(v => v.status === 'candidato')]
      todos.sort((a, b) => b.score - a.score)
      setVideos(todos)
    } catch {
      // silently handle
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
                {videos.map(v => (
                  <VideoRow key={v.video_id} video={v} canalId={canal} onAction={refresh} />
                ))}
              </tbody>
            </table>
            {videos.length === 0 && (
              <p className="text-slate-400 text-center p-8">
                Nenhum video encontrado. Clique em Minerar Videos para comecar.
              </p>
            )}
          </div>
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
