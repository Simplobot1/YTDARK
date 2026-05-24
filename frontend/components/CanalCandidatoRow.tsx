import { CanalCandidato } from '@/lib/types'
import { ScoreBadge } from './ScoreBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface Props {
  candidato: CanalCandidato
  onAdicionar: (handle: string) => void
}

const MOMENTUM_COLOR: Record<string, string> = {
  crescendo: 'bg-green-700',
  estavel: 'bg-slate-600',
  declinando: 'bg-red-700',
}

export function CanalCandidatoRow({ candidato: c, onAdicionar }: Props) {
  return (
    <tr className="border-b border-slate-800 hover:bg-slate-800/50">
      <td className="p-3"><ScoreBadge score={c.score} /></td>
      <td className="p-3">
        <p className="font-medium">{c.handle}</p>
        <p className="text-xs text-slate-400">{c.nome}</p>
      </td>
      <td className="p-3 text-sm">{c.metricas.subscribers.toLocaleString()}</td>
      <td className="p-3 text-sm">{Math.round(c.metricas.avg_views).toLocaleString()}</td>
      <td className="p-3 text-sm">{c.metricas.engagement_rate.toFixed(1)}%</td>
      <td className="p-3">
        <Badge className={MOMENTUM_COLOR[c.metricas.momentum] || 'bg-slate-600'}>{c.metricas.momentum}</Badge>
      </td>
      <td className="p-3">
        {c.adicionado
          ? <span className="text-green-400 text-xs">Adicionado</span>
          : <Button size="sm" onClick={() => onAdicionar(c.handle)}>+ Adicionar</Button>
        }
      </td>
    </tr>
  )
}
