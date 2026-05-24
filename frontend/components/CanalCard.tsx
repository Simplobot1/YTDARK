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
    <Link href={`/canal?id=${canalId}`}>
      <Card className="bg-slate-900 border-slate-800 hover:border-slate-600 cursor-pointer transition-colors">
        <CardHeader>
          <CardTitle className="text-white">{canalId}</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2 flex-wrap">
          {prontos > 0 && <Badge className="bg-green-700">{prontos} prontos</Badge>}
          {emProducao > 0 && <Badge className="bg-yellow-700">{emProducao} em producao</Badge>}
          {candidatos > 0 && <Badge className="bg-slate-600">{candidatos} candidatos</Badge>}
          {prontos === 0 && emProducao === 0 && candidatos === 0 && <Badge variant="outline">Vazio</Badge>}
        </CardContent>
      </Card>
    </Link>
  )
}
