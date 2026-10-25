#!/usr/bin/env bash
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

set -euo pipefail
umask 077

if ! command -v age >/dev/null 2>&1 || ! command -v age-keygen >/dev/null 2>&1; then
    printf 'Fehler: age und age-keygen muessen installiert sein.\n' >&2
    exit 1
fi

if (($# > 1)); then
    printf 'Verwendung: %s [ZWECK]\n' "$0" >&2
    exit 2
fi

purpose=${1:-}
if [[ -z $purpose ]]; then
    read -r -p 'Zweck (zte-ipaddress oder zte-admin-password): ' purpose
fi
if [[ -z ${purpose//[[:space:]]/} ]]; then
    printf 'Fehler: Der Zweck darf nicht leer sein.\n' >&2
    exit 2
fi

slug=$(printf '%s' "$purpose" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C tr -cs 'a-z0-9._-' '-')
slug=${slug#-}
slug=${slug%-}
slug=${slug:0:64}
if [[ -z $slug ]]; then
    printf 'Fehler: Aus dem Zweck konnte kein Dateiname gebildet werden.\n' >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
identity=${AGE_IDENTITY:-"$config_home/age/keys.txt"}
secrets_dir=$script_dir/secrets
identity_dir=$(dirname -- "$identity")
mkdir -p -- "$identity_dir" "$secrets_dir"
chmod 700 -- "$identity_dir" "$secrets_dir"

if [[ -L $identity ]]; then
    printf 'Fehler: Die age-Identitaetsdatei darf kein Symlink sein: %s\n' "$identity" >&2
    exit 1
fi
if [[ ! -e $identity ]]; then
    age-keygen -o "$identity" >&2
    printf 'Neue lokale age-Identitaet erstellt: %s\n' "$identity" >&2
    printf 'Diese Datei sicher sichern. Ohne sie sind die Secrets nicht wiederherstellbar.\n' >&2
fi
if [[ ! -f $identity ]]; then
    printf 'Fehler: Keine lesbare age-Identitaet unter %s\n' "$identity" >&2
    exit 1
fi
chmod 600 -- "$identity"
recipient=$(age-keygen -y "$identity")

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
output=$secrets_dir/${slug}-${timestamp}.age
if [[ -e $output || -L $output ]]; then
    printf 'Fehler: Zieldatei existiert bereits: %s\n' "$output" >&2
    exit 1
fi

secret=''
trap 'unset secret' EXIT
read -r -s -p 'Secret (Eingabe bleibt unsichtbar): ' secret
printf '\n'
if [[ -z $secret ]]; then
    printf 'Fehler: Das Secret darf nicht leer sein.\n' >&2
    exit 2
fi

if ! printf '%s' "$secret" | age -r "$recipient" -o "$output"; then
    rm -f -- "$output"
    printf 'Fehler: Verschluesselung fehlgeschlagen.\n' >&2
    exit 1
fi
chmod 600 -- "$output"
unset secret
trap - EXIT

printf 'Verschluesselt gespeichert: %s\n' "$output"