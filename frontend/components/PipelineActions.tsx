'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Video } from '@/lib/types'
import { aprovarVideo } from '@/lib/api'

interface Props {
  video: Video
  canalId: string
  onAction: () => void
}

export function PipelineActions({ video, canalId, onAction }: Props) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  async function approve() {
    setLoading(true)
    try {
      await aprovarVideo(canalId, video.video_id)
      onAction()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Erro')
    } finally {
      setLoading(false)
    }
  }

  function remodelar() {
    router.push(`/remodelar?canal=${encodeURIComponent(canalId)}&video=${encodeURIComponent(video.video_id)}`)
  }

  if (video.status === 'publicado' && video.yt_link) {
    return (
      <a
        href={video.yt_link}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-blue-400 hover:underline"
      >
        Ver no YouTube
      </a>
    )
  }

  // Para estados em progresso (analisado, roteiro_gerado, audio_gerado, video_pronto),
  // continua no wizard de remodelação.
  if (['candidato', 'aprovado', 'minerado', 'analisado', 'roteiro_gerado', 'audio_gerado', 'video_pronto'].includes(video.status)) {
    return (
      <div className="flex gap-2">
        {video.status === 'candidato' && (
          <Button size="sm" variant="outline" disabled={loading} onClick={approve}>
            Aprovar
          </Button>
        )}
        <Button size="sm" disabled={loading} onClick={remodelar}>
          Remodelar →
        </Button>
      </div>
    )
  }

  return <span className="text-xs text-slate-500">Processando...</span>
}
