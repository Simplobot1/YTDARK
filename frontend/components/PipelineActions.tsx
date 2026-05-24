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
    return <Button size="sm" disabled={loading} onClick={() => run(() => aprovarVideo(canalId, video.video_id))}>Aprovar</Button>
  if (video.status === 'aprovado')
    return <Button size="sm" disabled={loading} onClick={() => run(() => analisarVideo(canalId, video.video_id))}>Analisar</Button>
  if (video.status === 'analisado')
    return <Button size="sm" disabled={loading} onClick={() => run(() => produzirVideo(canalId, video.video_id))}>Produzir</Button>
  if (video.status === 'video_pronto')
    return <Button size="sm" disabled={loading} onClick={() => run(() => publicarVideo(canalId, video.video_id))}>Publicar</Button>
  if (video.status === 'publicado' && video.yt_link)
    return <a href={video.yt_link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline">Ver no YouTube</a>
  return <span className="text-xs text-slate-500">Processando...</span>
}
