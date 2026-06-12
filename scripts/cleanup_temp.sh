#!/usr/bin/env bash
# Limpeza dos arquivos brutos de produção em /opt/ytdark/temp.
# Seguro deletar: o vídeo final já foi publicado no YouTube e os metadados
# estão no Supabase — os brutos (download, frames, áudio) são descartáveis.
#
# Uso:  cleanup_temp.sh [dir]          (default: /opt/ytdark/temp)
# Env:  MAX_AGE_HOURS=48               (idade mínima para deletar)
set -euo pipefail

TEMP_DIR="${1:-/opt/ytdark/temp}"
MAX_AGE_HOURS="${MAX_AGE_HOURS:-48}"

[ -d "$TEMP_DIR" ] || { echo "dir não existe: $TEMP_DIR"; exit 0; }

echo "[cleanup] $(date '+%F %T') — removendo arquivos com mais de ${MAX_AGE_HOURS}h em ${TEMP_DIR}"
find "$TEMP_DIR" -type f \
  \( -name '*.mp4' -o -name '*.webm' -o -name '*.mkv' \
     -o -name '*.mp3' -o -name '*.wav' -o -name '*.m4a' \
     -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \
     -o -name '*.part' -o -name '*.ytdl' \) \
  -mmin +"$((MAX_AGE_HOURS * 60))" -print -delete

# remove subpastas que ficaram vazias
find "$TEMP_DIR" -mindepth 1 -type d -empty -delete

echo "[cleanup] disco após limpeza:"
df -h / | tail -1
