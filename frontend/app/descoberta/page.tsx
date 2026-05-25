'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { descobrirCanais, getCanais, salvarCanaisDescobertos } from '@/lib/api'
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

const LS_KEY = 'ytdark_descoberta'

function loadState() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}

function saveState(data: object) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(data)) } catch {}
}

export default function DescobertaPage() {
  const router = useRouter()
  useEffect(() => { if (!isAuthenticated()) router.push('/login') }, [router])

  const saved = useRef(loadState())

  const [nicho, setNicho] = useState(saved.current?.nicho ?? 'personal finance')
  const [seed, setSeed] = useState(saved.current?.seed ?? '')
  const [idioma, setIdioma] = useState(saved.current?.idioma ?? 'en')
  const [periodo, setPeriodo] = useState(saved.current?.periodo ?? 90)
  const [ordem, setOrdem] = useState(saved.current?.ordem ?? 'viewCount')
  const [minViews, setMinViews] = useState(saved.current?.minViews ?? 0)
  const [minSubs, setMinSubs] = useState(saved.current?.minSubs ?? 10000)
  const [maxSubs, setMaxSubs] = useState(saved.current?.maxSubs ?? 10000000)
  const [minFreq, setMinFreq] = useState(saved.current?.minFreq ?? 0)
  const [minDuracao, setMinDuracao] = useState(saved.current?.minDuracao ?? 0)
  const [maxDuracao, setMaxDuracao] = useState(saved.current?.maxDuracao ?? 60)
  const [topN, setTopN] = useState(saved.current?.topN ?? 20)
  const [candidatos, setCandidatos] = useState<CanalCandidato[]>(saved.current?.candidatos ?? [])
  const [buscou, setBuscou] = useState(!!(saved.current?.candidatos?.length))
  const [canalDestino, setCanalDestino] = useState(saved.current?.canalDestino ?? '')

  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const [canais, setCanais] = useState<string[]>([])
  const [toast, setToast] = useState('')

  useEffect(() => {
    getCanais().then(r => {
      setCanais(r.canais)
      if (!canalDestino && r.canais.length === 1) setCanalDestino(r.canais[0])
    }).catch(() => {})
  }, [])

  // Persiste estado no localStorage sempre que muda
  useEffect(() => {
    saveState({ nicho, seed, idioma, periodo, ordem, minViews, minSubs, maxSubs,
      minFreq, minDuracao, maxDuracao, topN, candidatos, canalDestino })
  }, [nicho, seed, idioma, periodo, ordem, minViews, minSubs, maxSubs,
      minFreq, minDuracao, maxDuracao, topN, candidatos, canalDestino])

  function showToast(msg: string) {
    setToast(msg)
    setTimeout(() => setToast(''), 3500)
  }

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
        nicho, seed_channel: seed.trim() || undefined,
        idioma, periodo_dias: periodo, ordem,
        filtros: { subscribers_min: minSubs, subscribers_max: maxSubs,
          avg_views_min: minViews, upload_freq_min: minFreq,
          avg_duration_min_min: minDuracao, avg_duration_max_min: maxDuracao },
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

  async function handleAdicionar(handle: string) {
    if (!canalDestino) {
      showToast('Selecione o canal destino primeiro')
      return
    }
    // Marca localmente
    setCandidatos(prev => prev.map(c => c.handle === handle ? { ...c, adicionado: true } : c))
    // Salva imediatamente no Supabase
    const canal = candidatos.find(c => c.handle === handle)
    if (!canal) return
    try {
      await salvarCanaisDescobertos(canalDestino, [{ ...canal, adicionado: true }])
      showToast(`"${handle}" salvo em "${canalDestino}"`)
    } catch {
      showToast(`Erro ao salvar "${handle}"`)
    }
  }

  const adicionados = candidatos.filter(c => c.adicionado)

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-5xl mx-auto">

        {/* Toast */}
        {toast && (
          <div className="fixed top-4 right-4 z-50 bg-emerald-700 text-white px-4 py-2 rounded-lg shadow-lg text-sm animate-in fade-in slide-in-from-top-2">
            {toast}
          </div>
        )}

        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard" className="text-slate-400 hover:text-white">&#8592; Dashboard</Link>
          <h1 className="text-2xl font-bold text-white">Descobrir Canais Fonte</h1>
        </div>

        <Card className="bg-slate-900 border-slate-800 mb-6">
          <CardHeader><CardTitle className="text-white">Busca</CardTitle></CardHeader>
          <CardContent className="space-y-4">

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Nicho / Keywords</Label>
                <Input value={nicho} onChange={e => setNicho(e.target.value)}
                  placeholder="ex: personal finance, investing"
                  className="bg-slate-800 border-slate-700 mt-1" />
                <p className="text-slate-500 text-xs mt-1">Busca canais que falam sobre esse assunto</p>
              </div>
              <div>
                <Label className="text-slate-300">Canal Similar a (opcional)</Label>
                <Input value={seed} onChange={e => setSeed(e.target.value)}
                  placeholder="ex: @CasuallyFinance"
                  className="bg-slate-800 border-slate-700 mt-1" />
                <p className="text-slate-500 text-xs mt-1">Encontra canais parecidos com este</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <Label className="text-slate-300">Período de atividade</Label>
                <select value={periodo} onChange={e => setPeriodo(+e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm">
                  {PERIODOS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Ordenar por</Label>
                <select value={ordem} onChange={e => setOrdem(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm">
                  {ORDENS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Idioma</Label>
                <select value={idioma} onChange={e => setIdioma(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-white text-sm">
                  {IDIOMAS.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Qtd. Resultados</Label>
                <Input type="number" value={topN} onChange={e => setTopN(+e.target.value)}
                  min={5} max={50} className="bg-slate-800 border-slate-700 mt-1" />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {[
                ['Min. Inscritos', minSubs, setMinSubs],
                ['Max. Inscritos', maxSubs, setMaxSubs],
                ['Min. Views Médio', minViews, setMinViews],
                ['Min. Uploads/período', minFreq, setMinFreq],
                ['Duração min (min)', minDuracao, setMinDuracao],
                ['Duração max (min)', maxDuracao, setMaxDuracao],
              ].map(([label, val, setter]) => (
                <div key={label as string}>
                  <Label className="text-slate-300 text-xs">{label as string}</Label>
                  <Input type="number" value={val as number}
                    onChange={e => (setter as (v: number) => void)(+e.target.value)}
                    className="bg-slate-800 border-slate-700 mt-1 text-sm" />
                </div>
              ))}
            </div>

            {/* Canal destino — selecionado ANTES de buscar */}
            {canais.length > 0 && (
              <div className="flex items-center gap-3 pt-1">
                <Label className="text-slate-300 text-sm whitespace-nowrap">Canal destino:</Label>
                {canais.length === 1
                  ? <span className="text-white text-sm font-medium">{canalDestino}</span>
                  : (
                    <select value={canalDestino} onChange={e => setCanalDestino(e.target.value)}
                      className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-white text-sm">
                      <option value="">Selecionar...</option>
                      {canais.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  )
                }
                {!canalDestino && (
                  <span className="text-amber-400 text-xs">Selecione para que "+ Adicionar" salve automaticamente</span>
                )}
              </div>
            )}

            <div className="flex gap-3 flex-wrap">
              <Button onClick={buscar} disabled={loading}>
                {loading ? 'Buscando...' : 'Buscar Canais'}
              </Button>
              {candidatos.length > 0 && (
                <Button variant="outline" onClick={() => { setCandidatos([]); setBuscou(false); saveState({}) }}
                  className="border-slate-700 text-slate-400 hover:text-white">
                  Limpar resultados
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {erro && (
          <div className="bg-red-900/40 border border-red-700 rounded-lg p-4 mb-4">
            <p className="text-red-300 text-sm font-medium">Erro: {erro}</p>
          </div>
        )}

        {candidatos.length > 0 && (
          <div className="bg-slate-900 rounded-lg border border-slate-800 overflow-x-auto">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-3 flex-wrap">
              <span className="text-slate-400 text-sm">
                {candidatos.length} canais encontrados
                {adicionados.length > 0 && (
                  <span className="ml-2 text-emerald-400">· {adicionados.length} salvos</span>
                )}
              </span>
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
