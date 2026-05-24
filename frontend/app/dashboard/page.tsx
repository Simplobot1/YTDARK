'use client'
import { useEffect, useState } from 'react'
import { getCanais, getCandidatos, getFila } from '@/lib/api'
import { CanalCard } from '@/components/CanalCard'
import { Button } from '@/components/ui/button'
import { removeToken } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Dashboard() {
  const router = useRouter()
  const [canais, setCanais] = useState<string[]>([])
  const [stats, setStats] = useState<Record<string, { prontos: number; emProducao: number; candidatos: number }>>({})

  useEffect(() => {
    getCanais().then(async ({ canais: ids }) => {
      setCanais(ids)
      const statsMap: typeof stats = {}
      for (const id of ids) {
        const [candidatos, fila] = await Promise.all([
          getCandidatos(id).catch(() => [] as { status: string }[]),
          getFila(id).catch(() => [] as { status: string }[]),
        ])
        statsMap[id] = {
          candidatos: candidatos.filter(v => v.status === 'candidato').length,
          emProducao: fila.length,
          prontos: fila.filter(v => v.status === 'video_pronto').length,
        }
      }
      setStats(statsMap)
    }).catch(() => {})
  }, [])

  function logout() {
    removeToken()
    router.push('/login')
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">YT DARK</h1>
          <div className="flex gap-3">
            <Link href="/descoberta">
              <Button variant="outline">Descobrir Canais</Button>
            </Link>
            <Button variant="ghost" onClick={logout}>Sair</Button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {canais.map(id => (
            <CanalCard key={id} canalId={id} {...(stats[id] || { prontos: 0, emProducao: 0, candidatos: 0 })} />
          ))}
        </div>
        {canais.length === 0 && (
          <p className="text-slate-400 text-center mt-16">Nenhum canal configurado ainda.</p>
        )}
      </div>
    </div>
  )
}
