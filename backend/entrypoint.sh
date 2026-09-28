#!/bin/sh
# Resolve SECRET_KEY before the app or Alembic touches the database.
#
# Precedence:
#   1. A real SECRET_KEY supplied via the environment (CI, or a .env file).
#   2. A key persisted in the `api_secret` volume from a previous run, so
#      restarting the stack does not invalidate everyone's tokens.
#   3. A freshly generated key, generated once and then persisted.
#
# A placeholder supplied by the caller is replaced and reported, because
# app.core.config refuses to start on one and a known signing key would let
# anyone mint admin tokens.
set -eu

SECRET_FILE="${SECRET_FILE:-/run/secrets/secret_key}"
PLACEHOLDER_MARKERS="change-me changeme dev-only placeholder example-secret your-secret"

is_placeholder() {
  # A key is a placeholder if it is empty, too short to be a real key, or
  # still carries one of the marker strings shipped in example config.
  [ -z "${1:-}" ] && return 0
  [ "${#1}" -lt 32 ] && return 0
  lowered=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  for marker in $PLACEHOLDER_MARKERS; do
    case "$lowered" in
      *"$marker"*) return 0 ;;
    esac
  done
  return 1
}

if ! is_placeholder "${SECRET_KEY:-}"; then
  echo "[entrypoint] using SECRET_KEY from the environment"
  exec "$@"
fi

if [ -n "${SECRET_KEY:-}" ]; then
  echo "[entrypoint] WARNING: the supplied SECRET_KEY looks like a placeholder."
  echo "[entrypoint]          Generating a real one instead, so the stack is not"
  echo "[entrypoint]          signing tokens with a publicly known key."
fi

mkdir -p "$(dirname "$SECRET_FILE")"

if [ -s "$SECRET_FILE" ]; then
  SECRET_KEY=$(cat "$SECRET_FILE")
  echo "[entrypoint] reusing the SECRET_KEY generated on first run"
else
  SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
  printf '%s' "$SECRET_KEY" > "$SECRET_FILE"
  chmod 600 "$SECRET_FILE" || true
  echo "[entrypoint] generated a new SECRET_KEY and saved it to $SECRET_FILE"
fi

export SECRET_KEY
exec "$@"
