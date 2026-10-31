# Modem-Anfrageprotokoll

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Protocol.md) | [Deutsch](Protocol.md) | [Français](../fr/Protocol.md) | [Español](../es/Protocol.md)

Der Client nutzt die bestehende Weboberflächen-Sitzung des Modems für reine Leseabfragen der DSL-Statistiken. Adresse und Passwort werden gemäß [Einrichtung](Setup.md) geladen.

## Ablauf der Anfragen

Alle HTTP-Anfragen teilen sich ein gemeinsames Cookie-Jar:

1. Laden der Startseite und Dekodieren des JavaScript-Session-Tokens (`_sessionTmpToken`) mit Hex-Escapes.
2. Abruf des numerischen Challenge-Tokens von `/function_module/login_module/login_page/logintoken_lua.lua`.
3. Berechnung des SHA-256-Hashes aus Passwort und Challenge-Token; Senden von Benutzername, Hash, Aktion und Session-Token an den Login-Handler.
4. Laden der DSL-Statusseite: `getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp`.
5. Abrufen von `/common_page/internet_dsl_interface_lua.lua` mit denselben Sitzungscookies und der Statusseite als HTTP-Referer.

Das Aufrufen der Statusseite zwischen Login und Datenabruf ist zwingend erforderlich, um den vom Modem erwarteten internen Sitzungszustand zu initialisieren. Ein erfolgreicher Login mit SID allein reicht nicht aus.

## Antwortdaten

Der Endpunkt liefert XML-Datensätze mit Parameternamen und -werten. Der Client extrahiert aktuelle und erreichbare Downstream-/Upstream-Raten, Störabstandsmargen (SNR), Dämpfung, Profil und Modulationsstandard. Raten werden in Mbit/s, SNR und Dämpfung in dB ausgegeben.
