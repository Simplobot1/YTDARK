'use client'
import { useState } from 'react'
import { descobrirCanais } from '@/lib/api'
import { CanalCandidato } from '@/lib/types'
import { CanalCandidatoRow } from '@/components/CanalCandidatoRow'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

export default function DescobertaPage() {
  const [estrategia, setEstrategia] = useState<'categoria' | 'seed'>('categoria')
  const [nicho, setNicho] = useState('personal finance')
  const [seed, setSeed] = useState('')
  const [minViews, setMinViews] = useState(50000)
  const [minSubs, setMinSubs] = useState(100000)
  const [loading, setLoading] = useState(false)
  const [candidatos, setCandidatos] = useState<CanalCandidato[]>([])

  async function buscar() {
    setLoading(true)
    try {
      const result = await descobrirCanais({
        estrategia,
        nicho,
        idioma: 'en',
        seed_channel: estrategia === 'seed' ? seed : undefined,
        filtros: { subscribers_min: minSubs, avg_views_min: minViews,
                   upload_freq_min: 4, avg_duration_min_min: 8, avg_duration_max_min: 20 },
        top_n: 20,
      })
      setCandidatos(result)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Erro ao buscar canais')
    } finally {
      setLoading(false)
    }
  }

  function handleAdicionar(handle: string) {
    setCandidatos(prev => prev.map(c => c.handle === handle ? { ...c, adicionado: true } : c))
  }

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard" className="text-slate-400 hover:text-white">&#8592; Dashboard</Link>
          <h1 className="text-2xl font-bold text-white">Descobrir Canais Fonte</h1>
        </div>

        <Card className="bg-slate-900 border-slate-800 mb-6">
          <CardHeader><CardTitle>Filtros de Busca</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <Label>Estrategia</Label>
              <div className="flex gap-2 mt-1">
                {(['categoria', 'seed'] as const).map(e => (
                  <button key={e} onClick={() => setEstrategia(e)}
                    className={`px-3 py-1 rounded text-sm ${estrategia === e ? 'bg-blue-600' : 'bg-slate-700'}`}>
                    {e}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Label>Nicho</Label>
              <Input value={nicho} onChange={e => setNicho(e.target.value)}
                className="bg-slate-800 border-slate-700" />
            </div>
            {estrategia === 'seed' && (
              <div>
                <Label>Canal Seed</Label>
                <Input value={seed} onChange={e => setSeed(e.target.value)}
                  placeholder="@CasuallyFinance"
                  className="bg-slate-800 border-slate-700" />
              </div>
            )}
            <div>
              <Label>Min. Views Medio</Label>
              <Input type="number" value={minViews} onChange={e => setMinViews(+e.target.value)}
                className="bg-slate-800 border-slate-700" />
            </div>
            <div>
              <Label>Min. Inscritos</Label>
              <Input type="number" value={minSubs} onChange={e => setMinSubs(+e.target.value)}
                className="bg-slate-800 border-slate-700" />
            </div>
            <div className="flex items-end">
              <Button onClick={buscar} disabled={loading} className="w-full">
                {loading ? 'Buscando...' : 'Buscar Canais'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {candidatos.length > 0 && (
          <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  {['Score','Handle','Inscritos','Avg Views','Engagement','Momentum',''].map((h, i) => (
                    <th key={i} className="p-3 text-left text-slate-400 text-sm">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {candidatos.map(c => (
                  <CanalCandidatoRow key={c.channel_id} candidato={c} onAdicionar={handleAdicionar} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
