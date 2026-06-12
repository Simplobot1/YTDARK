#!/usr/bin/env bash
# Backup da configuração do Paperclip para o Supabase Storage (bucket: backups).
#
# O que entra:  instances/default/{db,companies,data,secrets,workspaces,telemetry}
#               + secrets/ da raiz
# O que fica de fora: projects/ (~900MB de repos clonados, reconstruíveis),
#               bin/, bgutil-* (reinstaláveis), logs/
#
# Segurança: o tar é criptografado com AES-256 (openssl) ANTES do upload —
# nenhuma credencial sai da VPS em texto claro. A passphrase fica em
# /etc/ytdark-backup.env (BACKUP_PASSPHRASE). GUARDE UMA CÓPIA desse arquivo
# fora da VPS: sem a passphrase o backup é irrecuperável.
#
# O blob criptografado é dividido em chunks de 45MB (limite do Supabase Storage).
# Restore:
#   cat paperclip-<stamp>.tar.gz.enc.part* > backup.tar.gz.enc
#   openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE \
#     -in backup.tar.gz.enc | tar xzf - -C /opt/paperclip-data
#   (com o container do Paperclip parado)
#
# Env file (chmod 600): /etc/ytdark-backup.env
#   SUPABASE_URL=https://xxxx.supabase.co
#   SUPABASE_SERVICE_KEY=eyJ...
#   BACKUP_PASSPHRASE=<openssl rand -hex 32>
set -euo pipefail

ENV_FILE="${ENV_FILE:-/etc/ytdark-backup.env}"
DATA_DIR="${DATA_DIR:-/opt/paperclip-data}"
BUCKET="backups"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

. "$ENV_FILE"
: "${SUPABASE_URL:?faltou SUPABASE_URL em $ENV_FILE}"
: "${SUPABASE_SERVICE_KEY:?faltou SUPABASE_SERVICE_KEY em $ENV_FILE}"
: "${BACKUP_PASSPHRASE:?faltou BACKUP_PASSPHRASE em $ENV_FILE}"
export BACKUP_PASSPHRASE

STAMP="$(date +%Y%m%d-%H%M)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "[backup] $(date '+%F %T') — empacotando e criptografando config do Paperclip"
tar czf - -C "$DATA_DIR" \
  --exclude='instances/default/projects' \
  --exclude='instances/default/logs' \
  --exclude='bin' \
  --exclude='bgutil-provider' \
  --exclude='bgutil-ytdlp-pot-provider' \
  instances secrets |
  openssl enc -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE \
    -out "$WORK/paperclip-${STAMP}.tar.gz.enc"

SIZE_MB="$(du -m "$WORK/paperclip-${STAMP}.tar.gz.enc" | cut -f1)"
echo "[backup] tamanho criptografado: ${SIZE_MB}MB — dividindo em chunks de 45MB"
split -b 45M -d "$WORK/paperclip-${STAMP}.tar.gz.enc" "$WORK/paperclip-${STAMP}.tar.gz.enc.part"

for part in "$WORK"/paperclip-"${STAMP}".tar.gz.enc.part*; do
  name="$(basename "$part")"
  echo "[backup] enviando ${name}"
  curl -sf -X POST \
    "${SUPABASE_URL}/storage/v1/object/${BUCKET}/paperclip/${name}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @"$part" > /dev/null
done

echo "[backup] removendo backups com mais de ${RETENTION_DAYS} dias"
CUTOFF="$(date -d "-${RETENTION_DAYS} days" +%Y%m%d)"
curl -sf -X POST "${SUPABASE_URL}/storage/v1/object/list/${BUCKET}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"prefix":"paperclip/","limit":1000}' |
  grep -oE '"name":"paperclip-[0-9]{8}-[0-9]{4}\.tar\.gz\.enc\.part[0-9]+"' |
  cut -d'"' -f4 |
  while read -r old; do
    fdate="$(echo "$old" | grep -oE '[0-9]{8}' | head -1)"
    if [ -n "$fdate" ] && [ "$fdate" -lt "$CUTOFF" ]; then
      echo "[backup] apagando antigo: $old"
      curl -sf -X DELETE \
        "${SUPABASE_URL}/storage/v1/object/${BUCKET}/paperclip/${old}" \
        -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" > /dev/null || true
    fi
  done

echo "[backup] ok: paperclip-${STAMP}.tar.gz.enc (${SIZE_MB}MB em chunks)"
