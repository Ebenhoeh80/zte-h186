#!/usr/bin/env bash

# zte-h186-stats
#
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
#
# Reads all 26 DSL line parameters from ZTE H186 modem

set -euo pipefail

read -rp "Router-IP oder Hostname [192.168.10.2]: " ROUTER
ROUTER=${ROUTER:-192.168.10.2}

if [[ -z "$ROUTER" ]]; then
    echo "Fehler: Router-IP oder Hostname erforderlich."
    exit 1
fi

read -rp "Benutzername [admin]: " USER
USER=${USER:-admin}

read -s -p "Passwort: " PASS
echo

MODEM="http://${ROUTER}"

COOKIE=$(mktemp)
LOGIN_PAGE=$(mktemp)
STATUS_PAGE=$(mktemp)
DSL_XML=$(mktemp)

cleanup() {
    rm -f "$COOKIE" "$LOGIN_PAGE" "$STATUS_PAGE" "$DSL_XML"
}
trap cleanup EXIT

echo
echo "=================================================="
echo "1. Loginseite laden"
echo "=================================================="

curl -s "$MODEM/" > "$LOGIN_PAGE"

SESSIONTOKEN=$(
perl -0777 -ne '
if(/var _sessionTmpToken = "(.*?)"/){
    $s=$1;
    $s =~ s/\\x([0-9A-Fa-f]{2})/chr(hex($1))/eg;
    print $s;
}
' "$LOGIN_PAGE"
)

if [[ -z "$SESSIONTOKEN" ]]; then
    echo "Fehler: SessionToken nicht gefunden."
    exit 1
fi

echo "SESSIONTOKEN=$SESSIONTOKEN"

echo
echo "=================================================="
echo "2. LoginToken abrufen"
echo "=================================================="

LOGINTOKEN=$(
curl -s \
"$MODEM/function_module/login_module/login_page/logintoken_lua.lua" |
grep -o '[0-9]\+' |
head -1
)

if [[ -z "$LOGINTOKEN" ]]; then
    echo "Fehler: LoginToken nicht gefunden."
    exit 1
fi

echo "LOGINTOKEN=$LOGINTOKEN"

echo
echo "=================================================="
echo "3. Passwort hashen (SHA-256)"
echo "=================================================="

HASH=$(
printf "%s%s" "$PASS" "$LOGINTOKEN" |
sha256sum |
awk '{print $1}'
)

echo "SHA256 berechnet"

echo
echo "=================================================="
echo "4. Login"
echo "=================================================="

curl -s -L \
    -c "$COOKIE" \
    -b "_TESTCOOKIESUPPORT=1" \
    -H "Referer: $MODEM/" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data "Username=$USER" \
    --data "Password=$HASH" \
    --data "action=login" \
    --data "_sessionTOKEN=$SESSIONTOKEN" \
    "$MODEM/" \
    > /dev/null

SID=$(
awk '$6=="SID"{print $7}' "$COOKIE"
)

if [[ -z "$SID" ]]; then
    echo "Fehler: Keine SID erhalten. Bitte Passwort prüfen."
    exit 1
fi

echo "SID=$SID"

echo
echo "=================================================="
echo "5. DSL-Statusseite laden (Session-Synchronisation)"
echo "=================================================="

STATUS_URL="$MODEM/getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp"

curl -s \
    -b "$COOKIE" \
    -H "Referer: $MODEM/" \
    "$STATUS_URL" \
    > "$STATUS_PAGE"

grep -q "internet_dsl_interface_lua.lua" "$STATUS_PAGE" || {
    echo "Fehler: DSL-Endpunkt wurde auf der Statusseite nicht gefunden."
    exit 1
}

echo "DSL-Endpunkt gefunden"

echo
echo "=================================================="
echo "6. DSL-Daten abrufen (XML)"
echo "=================================================="

curl -s \
    -b "$COOKIE" \
    -H "X-Requested-With: XMLHttpRequest" \
    -H "Accept: application/xml, text/xml, */*; q=0.01" \
    -H "Referer: $STATUS_URL" \
    "$MODEM/common_page/internet_dsl_interface_lua.lua?_=$(date +%s%3N)" \
    > "$DSL_XML"

if grep -q "SessionTimeout" "$DSL_XML"; then
    echo "Fehler: SessionTimeout"
    exit 1
fi

echo "DSL-XML erfolgreich abgerufen"

getval() {
    local key="$1"
    local default="${2:-}"

    local res
    res=$(
        sed 's/></>\n</g' "$DSL_XML" |
        awk -v key="$key" '
            $0 ~ "<ParaName>" key "</ParaName>" {
                getline
                gsub(/<\/?ParaValue>/, "")
                print
                exit
            }
        '
    )
    if [[ -z "$res" ]]; then
        echo "$default"
    else
        echo "$res"
    fi
}

# Alle 26 Parameter auslesen
STATUS=$(getval Status "N/A")
MODE=$(getval Module_type "N/A")
PROFILE=$(getval CurrentProfile "N/A")

DOWN=$(getval Downstream_current_rate "0")
UP=$(getval Upstream_current_rate "0")

MAXDOWN=$(getval Downstream_max_rate "0")
MAXUP=$(getval Upstream_max_rate "0")

SNRDOWN=$(getval Downstream_noise_margin "0")
SNRUP=$(getval Upstream_noise_margin "0")

ATTDOWN=$(getval Downstream_attenuation "0")
ATTUP=$(getval Upstream_attenuation "0")

POWERDOWN=$(getval Downstream_power "0")
POWERUP=$(getval Upstream_power "0")

PATHMODE=$(getval Data_path "N/A")

DEPTHDOWN=$(getval DownInterleavedepth "N/A")
DEPTHUP=$(getval UpInterleaveDepth "N/A")

DELAYDOWN=$(getval DownInterleaveDelay "N/A")
DELAYUP=$(getval UpInterleaveDelay "N/A")

INPDOWN=$(getval DownstreamInp "0")
INPUP=$(getval UpstreamInp "0")

SHOWTIME=$(getval Showtime_start "0")

LINKENCAP=$(getval tLinkEncapsulationUsed "N/A")

CRCDOWN=$(getval DownCrc_errors "0")
CRCUP=$(getval UpCrc_errors "0")

FECDOWN=$(getval Fec_errors "0")
FECUP=$(getval Atuc_fec_errors "0")

echo
echo "=================================================="
echo "ZTE H186 DSL STATUS (26 Parameter)"
echo "=================================================="
echo
echo "Router     : $ROUTER"
echo "Status     : $STATUS"
echo "Modulation : $MODE"
echo "Profil     : $PROFILE"
echo "Datenpfad  : $PATHMODE"
echo "Link-Encap : $LINKENCAP"
echo "--------------------------------------------------"
echo "Sync Down  : $(awk "BEGIN { printf \"%.1f\", ${DOWN:-0}/1000 }") Mbit/s"
echo "Sync Up    : $(awk "BEGIN { printf \"%.1f\", ${UP:-0}/1000 }") Mbit/s"
echo "Max Down   : $(awk "BEGIN { printf \"%.1f\", ${MAXDOWN:-0}/1000 }") Mbit/s"
echo "Max Up     : $(awk "BEGIN { printf \"%.1f\", ${MAXUP:-0}/1000 }") Mbit/s"
echo "--------------------------------------------------"
echo "SNR Down   : $(awk "BEGIN { printf \"%.1f\", ${SNRDOWN:-0}/10 }") dB"
echo "SNR Up     : $(awk "BEGIN { printf \"%.1f\", ${SNRUP:-0}/10 }") dB"
echo "Attn Down  : $(awk "BEGIN { printf \"%.1f\", ${ATTDOWN:-0}/10 }") dB"
echo "Attn Up    : $(awk "BEGIN { printf \"%.1f\", ${ATTUP:-0}/10 }") dB"
echo "Power Down : $(awk "BEGIN { printf \"%.1f\", ${POWERDOWN:-0}/10 }") dBm"
echo "Power Up   : $(awk "BEGIN { printf \"%.1f\", ${POWERUP:-0}/10 }") dBm"
echo "--------------------------------------------------"
echo "Delay Down : $DELAYDOWN ms"
echo "Delay Up   : $DELAYUP ms"
echo "Depth Down : $DEPTHDOWN"
echo "Depth Up   : $DEPTHUP"
echo "INP Down   : $(awk "BEGIN { printf \"%.1f\", ${INPDOWN:-0}/10 }") Symbole"
echo "INP Up     : $(awk "BEGIN { printf \"%.1f\", ${INPUP:-0}/10 }") Symbole"
echo "--------------------------------------------------"
echo "Showtime   : $SHOWTIME Sekunden"
if [[ "$SHOWTIME" =~ ^[0-9]+$ && "$SHOWTIME" -gt 0 ]]; then
    DAYS=$((SHOWTIME / 86400))
    HOURS=$(((SHOWTIME % 86400) / 3600))
    MINS=$(((SHOWTIME % 3600) / 60))
    SECS=$((SHOWTIME % 60))
    echo "           : ${DAYS}d ${HOURS}h ${MINS}m ${SECS}s"
fi
echo "--------------------------------------------------"
echo "CRC Down   : $CRCDOWN"
echo "CRC Up     : $CRCUP"
echo "FEC Down   : $FECDOWN"
echo "FEC Up     : $FECUP"
echo "=================================================="