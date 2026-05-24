import { Badge } from '@/components/ui/badge'

export function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? 'bg-green-600' : score >= 60 ? 'bg-yellow-600' : 'bg-red-600'
  return (
    <Badge className={`${color} text-white font-bold`}>
      {score.toFixed(0)}pts
    </Badge>
  )
}
