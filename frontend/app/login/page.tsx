'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login } from '@/lib/api'
import { setToken } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { token } = await login(email, senha)
      setToken(token)
      router.push('/dashboard')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <Card className="w-full max-w-sm bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white text-2xl text-center">YT DARK</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="text-slate-300">Email</Label>
              <Input value={email} onChange={e => setEmail(e.target.value)}
                type="email" placeholder="admin@email.com"
                className="bg-slate-800 border-slate-700 text-white" />
            </div>
            <div>
              <Label className="text-slate-300">Senha</Label>
              <Input value={senha} onChange={e => setSenha(e.target.value)}
                type="password" placeholder="••••••"
                className="bg-slate-800 border-slate-700 text-white" />
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
