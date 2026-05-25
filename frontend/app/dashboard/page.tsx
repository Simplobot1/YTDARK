'use client'
import { useEffect, useState } from 'react'
import { getCanais, getCandidatos, getFila } from '@/lib/api'
import { CanalCard } from '@/components/CanalCard'
import { CanalInfo } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { removeToken, isAuthenticated } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Dashboard() {
  const router = useRouter()
  const [canais, setCanais] = useState<CanalInfo[]>([])
  const [stats, setStats] = useState<Record<string, { prontos: number; emProducao: number; candidatos: number }>>({})

  useEffect(() => {
    if (!isAuthenticated()) { router.push('/login'); return }
    getCanais().then(async ({ canais: lista }) => {
      setCanais(lista)
      const statsMap: typeof stats = {}
      for (const canal of lista) {
        const [candsRes, fila] = await Promise.all([
          getCandidatos(canal.id).catch(() => ({ videos: [], total: 0, page: 1, pages: 0 })),
          getFila(canal.id).catch(() => []),
        ])
        const filaArr = Array.isArray(fila) ? fila : []
        statsMap[canal.id] = {
          candidatos: candsRes.total,
          emProducao: filaArr.length,
          prontos: filaArr.filter(v => v.status === 'video_pronto').length,
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
          <div>
            <h1 className="text-3xl font-bold text-white">YT DARK</h1>
            <p className="text-slate-500 text-sm mt-1">Descubra canais, minere vídeos e remodeле o conteúdo</p>
          </div>
          <div className="flex gap-3">
            <Link href="/descoberta">
              <Button variant="outline">Descobrir Canais</Button>
            </Link>
            <Button variant="ghost" onClick={logout} className="text-slate-400">Sair</Button>
          </div>
        </div>

        {canais.length === 0 ? (
          <div className="text-center mt-20">
            <p className="text-slate-400 text-lg mb-2">Nenhum canal configurado ainda.</p>
            <p className="text-slate-600 text-sm">Configure um canal no servidor para começar.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {canais.map(canal => (
              <CanalCard
                key={canal.id}
                canal={canal}
                {...(stats[canal.id] || { prontos: 0, emProducao: 0, candidatos: 0 })}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
