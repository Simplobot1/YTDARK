'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { descobrirCanais } from '@/lib/api'
import { isAuthenticated } from '@/lib/auth'
import { CanalCandidato } from '@/lib/types'
import { CanalCandidatoRow } from '@/components/CanalCandidatoRow'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

const PERIODOS = [
  { label: 'Últimos 7 dias', value: 7 },
  { label: 'Últimos 30 dias', value: 30 },
  { label: 'Últimos 90 dias', value: 90 },
  { label: 'Últimos 6 meses', value: 180 },
  { label: 'Último ano', value: 365 },
]

const ORDENS = [
  { label: 'Mais vistos', value: 'viewCount' },
  { label: 'Mais relevantes', value: 'relevance' },
  { label: 'Mais recentes', value: 'date' },
  { label: 'Melhor avaliados', value: 'rating' },
]

const IDIOMAS = [
  { label: 'Inglês', value: 'en' },
  { label: 'Português', value: 'pt' },
  { label: 'Espanhol', value: 'es' },
  { label: 'Qualquer', value: '' },
]

export default function DescobertaPage() {
  const router = useRouter()
  useEffect(() => { if (!isAuthenticated()) router.push('/login') }, [router])

  const [nicho, setNicho] = useState('personal finance')
  const [seed, setSeed] = useState('')
  const [idioma, setIdioma] = useState('en')
  const [periodo, setPeriodo] = useState(90)
  const [ordem, setOrdem] = useState('viewCount')
  const [minViews, setMinViews] = useState(0)
  const [minSubs, setMinSubs] = useState(10000)
  const [maxSubs, setMaxSubs] = useState(10000000)
  const [minFreq, setMinFreq] = useState(0)
  const [minDuracao, setMinDuracao] = useState(0)
  const [maxDuracao, setMaxDuracao] = useState(60)
  const [topN, setTopN] = useState(20)
  const [loading, setLoading] = useState(false)
  const [candidatos, setCandidatos] = useState<CanalCandidato[]>([])
  const [buscou, setBuscou] = useState(false)
  const [erro, setErro] = useState('')

  async function buscar() {
    if (!nicho.trim() && !seed.trim()) {
      alert('Preencha o nicho ou um canal semente')
      return
    }
    setLoading(true)
    setBuscou(false)
    setErro('')
    try {
      const result = await descobrirCanais({
        nicho,
        seed_channel: seed.trim() || undefined,
        idioma,
        periodo_dias: periodo,
        ordem,
        filtros: {
          subscribers_min: minSubs,
          subscribers_max: maxSubs,
          avg_views_min: minViews,
          upload_freq_min: minFreq,
          avg_duration_min_min: minDuracao,
          avg_duration_max_min: maxDuracao,
        },
        top_n: topN,
      })
      setCandidatos(result)
      setBuscou(true)
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : 'Erro ao buscar canais')
      setBuscou(true)
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
          <CardHeader><CardTitle className="text-white">Busca</CardTitle></CardHeader>
          <CardContent className="space-y-4">

            {/* Linha 1: busca principal */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Nicho / Keywords</Label>
                <Input
                  value={nicho}
                  onChange={e => setNicho(e.target.value)}
                  placeholder="ex: personal finance, investing"
                  className="bg-slate-800 border-slate-700 mt-1"
                />
                <p className="text-slate-500 text-xs mt-1">Busca canais que falam sobre esse assunto</p>
              </div>
              <div>
                <Label className="text-slate-300">Canal Similar a (opcional)</Label>
                <Input
                  value={seed}
                  onChange={e => setSeed(e.target.value)}
                  placeholder="ex: @CasuallyFinance"
                  className="bg-slate-800 border-slate-700 mt-1"
                />
                <p className="text-slate-500 text-xs mt-1">Encontra canais parecidos com este</p>
              </div>
            </div>

            {/* Linha 2: filtros de tempo e ordem */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <Label className="text-slate-300">Período de atividade</Label>
                <select
                  value={periodo}
                  onChange={e => setPeriodo(+e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm"
                >
                  {PERIODOS.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Ordenar por</Label>
                <select
                  value={ordem}
                  onChange={e => setOrdem(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm"
                >
                  {ORDENS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Idioma</Label>
                <select
                  value={idioma}
                  onChange={e => setIdioma(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm"
                >
                  {IDIOMAS.map(i => (
                    <option key={i.value} value={i.value}>{i.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Qtd. Resultados</Label>
                <Input
                  type="number"
                  value={topN}
                  onChange={e => setTopN(+e.target.value)}
                  min={5} max={50}
                  className="bg-slate-800 border-slate-700 mt-1"
                />
              </div>
            </div>

            {/* Linha 3: filtros de canal */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div>
                <Label className="text-slate-300 text-xs">Min. Inscritos</Label>
                <Input type="number" value={minSubs} onChange={e => setMinSubs(+e.target.value)}
                  className="bg-slate-800 border-slate-700 mt-1 text-sm" />
              </div>
              <div>
                <Label className="text-slate-300 text-xs">Max. Inscritos</Label>
                <Input type="number" value={maxSubs} onChange={e => setMaxSubs(+e.target.value)}
                  className="bg-slate-800 border-slate-700 mt-1 text-sm" />
              </div>
              <div>
                <Label className="text-slate-300 text-xs">Min. Views Médio</Label>
                <Input type="number" value={minViews} onChange={e => setMinViews(+e.target.value)}
                  className="bg-slate-800 border-slate-700 mt-1 text-sm" />
              </div>
              <div>
                <Label className="text-slate-300 text-xs">Min. Uploads/período</Label>
                <Input type="number" value={minFreq} onChange={e => setMinFreq(+e.target.value)}
                  className="bg-slate-800 border-slate-700 mt-1 text-sm" />
              </div>
              <div>
                <Label className="text-slate-300 text-xs">Duração min (min)</Label>
                <Input type="number" value={minDuracao} onChange={e => setMinDuracao(+e.target.value)}
                  className="bg-slate-800 border-slate-700 mt-1 text-sm" />
              </div>
              <div>
                <Label className="text-slate-300 text-xs">Duração max (min)</Label>
                <Input type="number" value={maxDuracao} onChange={e => setMaxDuracao(+e.target.value)}
                  className="bg-slate-800 border-slate-700 mt-1 text-sm" />
              </div>
            </div>

            <Button onClick={buscar} disabled={loading} className="w-full md:w-auto">
              {loading ? 'Buscando...' : 'Buscar Canais'}
            </Button>
          </CardContent>
        </Card>

        {erro && (
          <div className="bg-red-900/40 border border-red-700 rounded-lg p-4 mb-4">
            <p className="text-red-300 text-sm font-medium">Erro: {erro}</p>
          </div>
        )}

        {candidatos.length > 0 && (
          <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-x-auto">
            <div className="p-4 border-b border-slate-800">
              <span className="text-slate-400 text-sm">{candidatos.length} canais encontrados</span>
            </div>
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  {['Score', 'Handle', 'Inscritos', 'Avg Views', 'Engagement', 'Momentum', ''].map((h, i) => (
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

        {!loading && !buscou && candidatos.length === 0 && (
          <p className="text-slate-500 text-center mt-12">
            Preencha o nicho, o canal semente, ou ambos — depois clique em Buscar Canais.
          </p>
        )}
        {!loading && buscou && candidatos.length === 0 && (
          <p className="text-slate-400 text-center mt-12">
            Nenhum canal encontrado. Tente relaxar os filtros ou usar outros termos.
          </p>
        )}
      </div>
    </div>
  )
}
