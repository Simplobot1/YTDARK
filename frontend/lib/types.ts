export type VideoStatus =
  | 'candidato' | 'aprovado' | 'minerado' | 'analisado'
  | 'roteiro_gerado' | 'audio_gerado' | 'video_pronto' | 'publicado'

export interface Video {
  video_id: string
  titulo: string
  canal_fonte: string
  views: number
  data_pub: string
  duracao_min: number
  tipo: string
  score: number
  status: VideoStatus
  transcricao?: string
  analise?: Record<string, unknown>
  roteiro_path?: string
  audio_path?: string
  thumbnail_path?: string
  video_path?: string
  drive_link?: string
  yt_link?: string
}

export interface MetricasCanal {
  subscribers: number
  avg_views: number
  engagement_rate: number
  upload_freq_mensal: number
  avg_duration_min: number
  momentum: 'crescendo' | 'estavel' | 'declinando'
}

export interface CanalCandidato {
  handle: string
  nome: string
  channel_id: string
  metricas: MetricasCanal
  score: number
  melhor_video_recente?: Record<string, unknown>
  adicionado: boolean
}

export interface ChannelDNA {
  estilo_visual: string
  tom_voz: string
  paleta_cores: string[]
  intro_max_sec: number
  hook_style: string
  num_pontos: number
  cta_style: string
  thumbnail_formula: string
  thumbnail_fonte: string
  titulo_formula: string
  duracao_alvo_min: number
}

export interface CanalConfig {
  canal_id: string
  youtube_handle: string
  idioma: string
  nicho_keywords: string[]
  canais_fonte: string[]
  tipo_video_padrao: string
  google_sheets_id: string
  google_drive_folder_id: string
}

export interface CanalInfo {
  id: string
  handle: string
  nicho: string[]
}

export interface Keyword {
  termo: string
  volume: number
  competition: number
  seo_score: number
}
