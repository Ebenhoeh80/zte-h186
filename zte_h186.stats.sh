#!/usr/bin/env bash

# zte-h186-stats
#
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

set -euo pipefail

read -rp "Router-IP oder Hostname: " ROUTER

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
echo "3. Passwort hashen"
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
    echo "Fehler: Keine SID erhalten."
    exit 1
fi

echo "SID=$SID"

echo
echo "=================================================="
echo "5. DSL-Statusseite laden"
echo "=================================================="

STATUS_URL="$MODEM/getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp"

curl -s \
    -b "$COOKIE" \
    -H "Referer: $MODEM/" \
    "$STATUS_URL" \
    > "$STATUS_PAGE"

grep -q "internet_dsl_interface_lua.lua" "$STATUS_PAGE" || {
    echo "Fehler: DSL-Endpunkt wurde nicht gefunden."
    exit 1
}

echo "DSL-Endpunkt gefunden"

echo
echo "=================================================="
echo "6. DSL-Daten abrufen"
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

    sed 's/></>\n</g' "$DSL_XML" |
    awk -v key="$key" '
        $0 ~ "<ParaName>" key "</ParaName>" {
            getline
            gsub(/<\/?ParaValue>/, "")
            print
            exit
        }
    '
}

STATUS=$(getval Status)

MODE=$(getval Module_type)
PROFILE=$(getval CurrentProfile)

DOWN=$(getval Downstream_current_rate)
UP=$(getval Upstream_current_rate)

MAXDOWN=$(getval Downstream_max_rate)
MAXUP=$(getval Upstream_max_rate)

SNRDOWN=$(getval Downstream_noise_margin)
SNRUP=$(getval Upstream_noise_margin)

ATTDOWN=$(getval Downstream_attenuation)
ATTUP=$(getval Upstream_attenuation)

POWERDOWN=$(getval Downstream_power)
POWERUP=$(getval Upstream_power)

PATHMODE=$(getval Data_path)

DEPTHDOWN=$(getval DownInterleavedepth)
DEPTHUP=$(getval UpInterleaveDepth)

DELAYDOWN=$(getval DownInterleaveDelay)
DELAYUP=$(getval UpInterleaveDelay)

INPDOWN=$(getval DownstreamInp)
INPUP=$(getval UpstreamInp)

SHOWTIME=$(getval Showtime_start)

LINKENCAP=$(getval tLinkEncapsulationUsed)

CRCDOWN=$(getval DownCrc_errors)
CRCUP=$(getval UpCrc_errors)

FECDOWN=$(getval Fec_errors)
FECUP=$(getval Atuc_fec_errors)

echo
echo "=================================================="
echo "DSL STATUS"
echo "=================================================="
echo

echo "Router     : $ROUTER"
echo "Status     : $STATUS"
echo "Modulation : $MODE"
echo "Profil     : $PROFILE"
echo

echo "Sync Down  : $(awk "BEGIN { printf \"%.1f\", $DOWN/1000 }") Mbit/s"
echo "Sync Up    : $(awk "BEGIN { printf \"%.1f\", $UP/1000 }") Mbit/s"
echo

echo "Max Down   : $(awk "BEGIN { printf \"%.1f\", $MAXDOWN/1000 }") Mbit/s"
echo "Max Up     : $(awk "BEGIN { printf \"%.1f\", $MAXUP/1000 }") Mbit/s"
echo

echo "SNR Down   : $(awk "BEGIN { printf \"%.1f\", $SNRDOWN/10 }") dB"
echo "SNR Up     : $(awk "BEGIN { printf \"%.1f\", $SNRUP/10 }") dB"
echo

echo "Attn Down  : $(awk "BEGIN { printf \"%.1f\", $ATTDOWN/10 }") dB"
echo "Attn Up    : $(awk "BEGIN { printf \"%.1f\", $ATTUP/10 }") dB"
echo

echo "Power Down : $(awk "BEGIN { printf \"%.1f\", $POWERDOWN/10 }") dBm"
echo "Power Up   : $(awk "BEGIN { printf \"%.1f\", $POWERUP/10 }") dBm"
echo

echo "Path       : $PATHMODE"
echo

echo "Depth Down : $DEPTHDOWN"
echo "Depth Up   : $DEPTHUP"
echo

echo "Delay Down : $DELAYDOWN ms"
echo "Delay Up   : $DELAYUP ms"
echo

echo "INP Down   : $(awk "BEGIN { printf \"%.1f\", $INPDOWN/10 }") Symbols"
echo "INP Up     : $(awk "BEGIN { printf \"%.1f\", $INPUP/10 }") Symbols"
echo

echo "Showtime   : $SHOWTIME Sekunden"

if [[ "$SHOWTIME" =~ ^[0-9]+$ ]]; then
    DAYS=$((SHOWTIME / 86400))
    HOURS=$(((SHOWTIME % 86400) / 3600))
    MINS=$(((SHOWTIME % 3600) / 60))
    SECS=$((SHOWTIME % 60))

    echo "           : ${DAYS}d ${HOURS}h ${MINS}m ${SECS}s"
fi

echo
echo "Link Encap : $LINKENCAP"
echo

echo "CRC Down   : $CRCDOWN"
echo "CRC Up     : $CRCUP"
echo

echo "FEC Down   : $FECDOWN"
echo "FEC Up     : $FECUP"