import { Video } from '@/lib/types'
import { ScoreBadge } from './ScoreBadge'
import { PipelineActions } from './PipelineActions'

const STATUS_LABEL: Record<string, string> = {
  candidato: 'Candidato', aprovado: 'Aprovado', minerado: 'Minerado',
  analisado: 'Analisado', roteiro_gerado: 'Roteiro', audio_gerado: 'Audio',
  video_pronto: 'Pronto', publicado: 'Publicado',
}

interface Props {
  video: Video
  canalId: string
  onAction: () => void
}

export function VideoRow({ video, canalId, onAction }: Props) {
  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/50">
      <td className="p-3"><ScoreBadge score={video.score} /></td>
      <td className="p-3">
        <p className="font-medium text-sm">{video.titulo}</p>
        <p className="text-xs text-slate-400">{video.canal_fonte} &middot; {video.views.toLocaleString()} views</p>
      </td>
      <td className="p-3 text-sm text-slate-300">{STATUS_LABEL[video.status] || video.status}</td>
      <td className="p-3">
        <PipelineActions video={video} canalId={canalId} onAction={onAction} />
      </td>
    </tr>
  )
}
