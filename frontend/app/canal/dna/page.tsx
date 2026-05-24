'use client'
import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { getCanalDna, updateCanalDna } from '@/lib/api'
import { ChannelDNA } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Link from 'next/link'

function DnaContent() {
  const searchParams = useSearchParams()
  const canal = searchParams.get('id') || ''
  const [dna, setDna] = useState<ChannelDNA | null>(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (canal) getCanalDna(canal).then(setDna).catch(() => {})
  }, [canal])

  function update<K extends keyof ChannelDNA>(field: K, value: ChannelDNA[K]) {
    setDna(prev => prev ? { ...prev, [field]: value } : prev)
    setSaved(false)
  }

  async function save() {
    if (!dna) return
    setSaving(true)
    try {
      await updateCanalDna(canal, dna)
      setSaved(true)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Erro ao salvar DNA')
    } finally {
      setSaving(false)
    }
  }

  if (!dna) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
      Carregando...
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-950 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <Link href={`/canal?id=${canal}`} className="text-slate-400 hover:text-white">&#8592; Pipeline</Link>
          <h1 className="text-2xl font-bold text-white">Channel DNA &mdash; {canal}</h1>
        </div>

        <div className="space-y-4">
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader><CardTitle>Identidade Visual</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <Label>Estilo Visual</Label>
                <select value={dna.estilo_visual} onChange={e => update('estilo_visual', e.target.value)}
                  className="w-full mt-1 p-2 bg-slate-800 border border-slate-700 rounded text-white">
                  <option value="whiteboard">Whiteboard</option>
                  <option value="talking_head">Talking Head</option>
                  <option value="slides">Slides</option>
                </select>
              </div>
              <div>
                <Label>Duracao Alvo (min)</Label>
                <Input type="number" value={dna.duracao_alvo_min}
                  onChange={e => update('duracao_alvo_min', +e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>Tom de Voz</Label>
                <Input value={dna.tom_voz} onChange={e => update('tom_voz', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader><CardTitle>Estrutura do Roteiro</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <Label>Hook Style</Label>
                <Input value={dna.hook_style} onChange={e => update('hook_style', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div>
                <Label>Numero de Pontos</Label>
                <Input type="number" value={dna.num_pontos}
                  onChange={e => update('num_pontos', +e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>Formula de Titulo</Label>
                <Input value={dna.titulo_formula} onChange={e => update('titulo_formula', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>CTA Style</Label>
                <Input value={dna.cta_style} onChange={e => update('cta_style', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardHeader><CardTitle>Thumbnail</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div>
                <Label>Formula Visual</Label>
                <Input value={dna.thumbnail_formula} onChange={e => update('thumbnail_formula', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div>
                <Label>Fonte</Label>
                <Input value={dna.thumbnail_fonte} onChange={e => update('thumbnail_fonte', e.target.value)}
                  className="bg-slate-800 border-slate-700" />
              </div>
              <div className="col-span-2">
                <Label>Cores Principais (hex)</Label>
                <div className="flex gap-2 mt-1 flex-wrap">
                  {dna.paleta_cores.map((cor, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <div className="w-6 h-6 rounded border border-slate-600" style={{ backgroundColor: cor }} />
                      <Input value={cor} onChange={e => {
                        const novas = [...dna.paleta_cores]
                        novas[i] = e.target.value
                        update('paleta_cores', novas)
                      }} className="bg-slate-800 border-slate-700 w-28 text-xs" />
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Button onClick={save} disabled={saving} className="w-full">
            {saving ? 'Salvando...' : saved ? 'DNA Salvo!' : 'Salvar DNA'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function DnaPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">Carregando...</div>}>
      <DnaContent />
    </Suspense>
  )
}
