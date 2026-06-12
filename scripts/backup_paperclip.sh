#!/usr/bin/env bash
# Backup da configuração do Paperclip para o Supabase Storage (bucket: backups).
#
# Estratégia:
#   1. pg_dumpall do postgres embutido (dump lógico consistente) via container
#      descartável postgres:18-alpine plugado no namespace de rede do Paperclip.
#      Credenciais: paperclip/paperclip (default upstream, hardcoded em
#      server/src/index.ts — o postgres só é alcançável de dentro do container).
#   2. tar do resto da config: companies, data, secrets, workspaces, telemetry.
#      Fica de fora: db/ (substituído pelo dump), projects/ (~900MB de repos
#      clonados, reconstruíveis), logs/, bin/, bgutil-* (reinstaláveis).
#   3. Criptografia AES-256 (openssl, pbkdf2) ANTES do upload — nenhuma
#      credencial sai da VPS em texto claro.
#   4. Upload em chunks de 45MB (limite do Supabase Storage) + retenção.
#
# GUARDE UMA CÓPIA de /etc/ytdark-backup.env fora da VPS:
# sem a BACKUP_PASSPHRASE o backup é irrecuperável.
#
# Restore:
#   cat paperclip-<stamp>.tar.gz.enc.part* > backup.tar.gz.enc
#   openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE \
#     -in backup.tar.gz.enc | tar xzf - -C /tmp/restore
#   # config: copiar /tmp/restore/instances/... sobre /opt/paperclip-data
#   # banco:  psql -f /tmp/restore/db-dump.sql (no postgres novo, via mesmo método)
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
PG_PORT="${PG_PORT:-54329}"

. "$ENV_FILE"
: "${SUPABASE_URL:?faltou SUPABASE_URL em $ENV_FILE}"
: "${SUPABASE_SERVICE_KEY:?faltou SUPABASE_SERVICE_KEY em $ENV_FILE}"
: "${BACKUP_PASSPHRASE:?faltou BACKUP_PASSPHRASE em $ENV_FILE}"
export BACKUP_PASSPHRASE

STAMP="$(date +%Y%m%d-%H%M)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PAPERCLIP_CID="$(docker ps -q -f name=paperclip | head -1)"
[ -n "$PAPERCLIP_CID" ] || { echo "[backup] container do paperclip não encontrado"; exit 1; }

echo "[backup] $(date '+%F %T') — pg_dumpall do postgres embutido (porta ${PG_PORT})"
docker run --rm --network "container:${PAPERCLIP_CID}" \
  -e PGPASSWORD=paperclip postgres:18-alpine \
  pg_dumpall -h 127.0.0.1 -p "$PG_PORT" -U paperclip > "$WORK/db-dump.sql"
echo "[backup] dump: $(du -h "$WORK/db-dump.sql" | cut -f1)"

echo "[backup] empacotando config + dump e criptografando"
tar czf - -C "$DATA_DIR" \
  --warning=no-file-changed \
  --exclude='instances/default/projects' \
  --exclude='instances/default/logs' \
  --exclude='instances/default/db' \
  --exclude='bin' \
  --exclude='bgutil-provider' \
  --exclude='bgutil-ytdlp-pot-provider' \
  instances secrets -C "$WORK" db-dump.sql |
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
