#!/usr/bin/env bash
# Test de fumée : vérifie de bout en bout qu'un déploiement fonctionne.
#
# Usage :
#   ./scripts/smoke_test.sh [URL_DU_FRONTEND]
#   ./scripts/smoke_test.sh http://localhost:8080
#   EXPECTED_VERSION=a1b2c3d ./scripts/smoke_test.sh http://<load-balancer>
#
# Code de sortie 0 = tout va bien, autre = échec (Jenkins déclenchera le rollback).
set -euo pipefail

BASE_URL="${1:-http://localhost:8080}"
BASE_URL="${BASE_URL%/}"
RETRIES="${RETRIES:-20}"
DELAY="${DELAY:-3}"

log() { printf '[smoke] %s\n' "$*"; }
fail() { printf '[smoke] ECHEC : %s\n' "$*" >&2; exit 1; }

# 1) Attendre que l'application réponde (un déploiement n'est pas instantané)
log "Attente de ${BASE_URL}/api/info"
ready=0
for _ in $(seq 1 "$RETRIES"); do
  if curl -fsS -o /dev/null --max-time 5 "${BASE_URL}/api/info"; then
    ready=1
    break
  fi
  sleep "$DELAY"
done
[ "$ready" -eq 1 ] || fail "l'application ne répond pas après $((RETRIES * DELAY)) secondes"

# 2) Vérifier la version déployée (optionnel)
info="$(curl -fsS --max-time 5 "${BASE_URL}/api/info")"
log "Réponse /api/info : ${info}"
if [ -n "${EXPECTED_VERSION:-}" ]; then
  echo "$info" | grep -q "\"version\":\"${EXPECTED_VERSION}\"" \
    || fail "version attendue ${EXPECTED_VERSION}, reçu ${info}"
  log "Version ${EXPECTED_VERSION} confirmée"
fi

# 3) Écrire un item (teste l'API + PostgreSQL)
created="$(curl -fsS --max-time 10 -X POST "${BASE_URL}/api/items" \
  -H 'Content-Type: application/json' \
  -d '{"name":"smoke-test"}')" || fail "POST /api/items a échoué"
item_id="$(echo "$created" | grep -o '"id":[0-9]*' | head -n1 | cut -d: -f2)"
[ -n "$item_id" ] || fail "identifiant de l'item introuvable dans : ${created}"
log "Item créé (id=${item_id})"

# 4) Le relire (teste la lecture, et indirectement le cache)
curl -fsS --max-time 10 "${BASE_URL}/api/items" | grep -q '"smoke-test"' \
  || fail "l'item créé n'apparaît pas dans la liste"
log "Item retrouvé dans la liste"

# 5) Nettoyer
curl -fsS --max-time 10 -X DELETE "${BASE_URL}/api/items/${item_id}" -o /dev/null \
  || fail "DELETE /api/items/${item_id} a échoué"
log "Item supprimé"

log "OK : tous les contrôles sont passés"
