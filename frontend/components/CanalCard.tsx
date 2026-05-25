import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CanalInfo } from '@/lib/types'

interface Props {
  canal: CanalInfo
  prontos: number
  emProducao: number
  candidatos: number
}

export function CanalCard({ canal, prontos, emProducao, candidatos }: Props) {
  return (
    <Link href={`/canal?id=${canal.id}`}>
      <Card className="bg-slate-900 border-slate-800 hover:border-slate-500 cursor-pointer transition-colors">
        <CardHeader className="pb-2">
          <CardTitle className="text-white text-lg">{canal.handle}</CardTitle>
          <p className="text-slate-500 text-xs">{canal.nicho.join(' · ') || 'Sem nicho definido'}</p>
        </CardHeader>
        <CardContent className="flex gap-2 flex-wrap pt-0">
          {prontos > 0 && <Badge className="bg-green-700">{prontos} prontos</Badge>}
          {emProducao > 0 && <Badge className="bg-yellow-700">{emProducao} em produção</Badge>}
          {candidatos > 0 && <Badge className="bg-slate-600">{candidatos} candidatos</Badge>}
          {prontos === 0 && emProducao === 0 && candidatos === 0 && (
            <Badge variant="outline" className="text-slate-500">Clique para minerar vídeos</Badge>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}
