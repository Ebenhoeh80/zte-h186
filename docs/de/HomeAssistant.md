# ZTE H186: Lokale DSL-Leitungswerte in Home Assistant

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/HomeAssistant.md) | [Deutsch](HomeAssistant.md) | [Français](../fr/HomeAssistant.md) | [Español](../es/HomeAssistant.md)

---

## Zweck und Umfang

Das Projekt liest DSL-Leitungswerte eines kompatiblen ZTE-H186-Modems über dessen
lokale Weboberfläche. Ein Client meldet sich an, liest die DSL-XML-Daten und
liefert sie gemeinsam an Home Assistant. Weder eine Cloud noch MQTT sind erforderlich.
Es werden keine DSL-, Router-, WLAN- oder WAN-Einstellungen verändert. Der Login
erzeugt jedoch eine Sitzung auf dem Modem und ist daher nicht völlig zustandslos.

Das Home-Assistant-Paket erzeugt einen Abrufsensor und 26 Mess-/Textsensoren.
Diese sind Leitungsdaten, keine Messung des aktuellen Datenverkehrs und kein
Internet-Speedtest.

Diese Beschreibung enthält keine installationsbezogenen Adressen, Netzbereiche,
Zugangsdaten oder Links zu einer privaten Home-Assistant-Instanz. Es werden neutrale
Platzhalter wie `<MODEM-LAN-IP>` verwendet.

---

## Architektur

Das Projekt unterstützt zwei Einbindungsvarianten für Home Assistant:

1. **Home Assistant Custom Integration (`custom_components/zte_h186`) (Empfohlen)**:
   - Native Integration mit UI Config Flow (**Einstellungen > Geräte & Dienste > Integration hinzufügen**)
   - Automatisches Erstellen von 27 Sensoren, 2 Binärsensoren und Diagnose-Button
   - Zentraler asynchroner DataUpdateCoordinator mit Session-Caching
   - Unterstützt HACS und automatische Reorganisation bei IP-/Passwort-Änderung

2. **Klassisches YAML-Paket (`zte-h186-package.yaml`)**:
   - Command-Line-Prozessabruf (`zte_h186_stats.py`) alle 300 Sekunden
   - Bereitstellung von Abrufsensor und Template-Sensoren
   - Für rein dateibasierte Umgebungen ohne Custom Components

```text
Home Assistant Core
  -> Custom Integration (custom_components/zte_h186)
     -> Config Flow (Host, Username, Password)
     -> DataUpdateCoordinator (asynchrone aiohttp-Abfragen)
     -> 27 Sensor-Entitäten, 2 Binärsensoren, 1 Action-Button
  -> ODER command_line YAML-Paket:
     -> Python-Prozess (zte_h186_stats.py)
     -> gemeinsames JSON mit Status, Zeitpunkt und Daten
     -> 26 Template-Sensoren
```

---

## Verkabelung und lokale Verwaltung des Modems

Diese Anleitung beschreibt die physische Verkabelung und die netzwerkseitige Einrichtung für den zuverlässigen Betrieb des ZTE H186 als reines DSL-Modem vor einem nachgeschalteten Router bei gleichzeitigem lokalem Managementzugriff.

### Anschlüsse und Farbcodierung

Die Anschlüsse des ZTE H186 übernehmen getrennte Rollen im Heim- und Betriebsnetzwerk:

| Port / Farbmarkierung | Bezeichnung | Verbindung | Funktion und Datenfluss |
|---|---|---|---|
| **Rot** | WAN / Routeranschluss | Mit dem **WAN-Port** des nachgeschalteten Routers verbinden | Leitet die reine DSL-Verbindung (Bridge-Modus / PPPoE-Passthrough) an den Hauptrouter weiter. Über diesen Port findet **keine** lokale Geräteverwaltung oder Weboberflächen-Anmeldung statt. |
| **Gelb** | LAN / Verwaltung | Mit einem **Netzwerkswitch** im lokalen Verwaltungsnetz verbinden | Dient ausschließlich dem administrativen Zugriff auf die Weboberfläche sowie der lokalen Telemetrieabfrage durch Home Assistant. |
| **Grau** | DSL | Mit der **DSL-/Telefonleitung** (TAE/Splitter/Anschlussdose) verbinden | Führt das Hochfrequenz-DSL-Signal der Teilnehmeranschlussleitung direkt an das Modem. |

> **Hinweis zu Herstellerunterlagen und Modellabweichungen:**  
> Die oben genannte Farbkodierung (Grau = DSL, Rot = WAN, Gelb = LAN) entspricht der geläufigen Werks- und Gehäuseausführung des ZTE H186. Je nach Distributor, Hardware-Revision oder Provider-Variante können einzelne Geräte abweichende Markierungen aufweisen (beispielsweise neutrale Buchsen mit eingeprägter Beschriftung wie `DSL`, `WAN` bzw. `LAN1` statt farbiger Ringe). Prüfen Sie vor dem Anstecken stets die Beschriftung direkt an den Buchsen des vorhandenen Geräts und gleichen Sie diese mit den zugehörigen Herstellerunterlagen ab.

---

### Schritt-für-Schritt-Einrichtung der lokalen Verwaltung

Um IP-Adresskollisionen im Produktivnetz zu verhindern und einen stabilen Abruf zu gewährleisten, wird das Modem vor der Einbindung in das Hausnetz vorkonfiguriert:

1. **Initialer Direktzugriff:**  
   Falls erforderlich (z. B. bei Neugeräten, nach einem Werksreset oder bei unbekannter Vorbelegung), schließen Sie zunächst einen PC oder Laptop direkt mit einem Ethernetkabel am **gelben LAN-Anschluss** an. Öffnen Sie die Weboberfläche des Modems im Webbrowser über die aktuell gültige bzw. werksseitige LAN-IP.

2. **Feste IP-Adresse im lokalen Verwaltungsnetz zuweisen:**  
   Weisen Sie dem LAN-Anschluss des ZTE H186 in den lokalen Netzwerkeinstellungen eine freie, feste IPv4-Adresse (`<MODEM-LAN-IP>`) aus Ihrem lokalen Verwaltungsnetz (z. B. Management-Subnetz oder Administrations-VLAN) zu.  
   - Wählen Sie die Subnetzmaske (`<SUBNETZ-MASKE>`) passend zu Ihrem Verwaltungsnetzwerk.  
   - Stellen Sie sicher, dass die vergebene `<MODEM-LAN-IP>` außerhalb des dynamischen DHCP-Vergabebereichs (DHCP-Pool) anderer Netzwerkgeräte liegt und keine Adresskonflikte mit bestehenden festen IP-Adressen im Netz entstehen.

3. **DHCP-Server des ZTE H186 deaktivieren:**  
   Deaktivieren Sie den integrierten DHCP-Server des ZTE H186 in den LAN-Einstellungen zwingend, **bevor** der gelbe Anschluss mit dem Switch des produktiven Netzwerks verbunden wird.  
   - *Hintergrund:* Zwei aktive DHCP-Server im selben Netzwerksegment ("Rogue DHCP") führen zu unkontrollierten Adressvergaben und massiven Verbindungsabbrüchen von Clients im Heimnetz.  
   - Der DHCP-Server des nachgeschalteten Hauptrouters bleibt unverändert aktiv und verwaltet weiterhin zentral alle regulären Netzwerk-Clients.

4. **Einstellungen speichern und neue Adresse aufrufen:**  
   Speichern Sie die geänderten Einstellungen auf dem Modem. Passen Sie die IP-Adresse des Test-PCs an das gewählte Verwaltungsnetz an und rufen Sie die Modemoberfläche im Browser unter der neuen statischen Adresse `http://<MODEM-LAN-IP>` auf, um die einwandfreie Erreichbarkeit zu prüfen.

5. **Verbindung mit dem Verwaltungsnetzwerk herstellen:**  
   Verbinden Sie den **gelben LAN-Anschluss** nun mit einem Switchport im passenden lokalen Verwaltungsnetzwerk.

6. **Zukünftiger Anmeldepfad:**  
   Das spätere Login sowie sämtliche Sensorabfragen erfolgen ausschließlich über die konfigurierte LAN-IP (`<MODEM-LAN-IP>`) am gelben LAN-Port – niemals über den roten WAN-Anschluss.

---

### Bezug zur Home-Assistant-Integration

Home Assistant fragt die DSL-Telemetriedaten lokal über die konfigurierte Management-Schnittstelle ab:

1. **Netzwerkerreichbarkeit aus Home Assistant:**  
   - Die in Home Assistant hinterlegte Modemadresse muss der erreichbaren lokalen LAN-IP (`<MODEM-LAN-IP>`) entsprechen.  
   - Die Home-Assistant-Instanz (z. B. auf Home Assistant OS / HAOS) benötigt netzwerkseitigen Zugriff auf diese LAN-IP über Port 80 (HTTP). Werden Home Assistant und das Modem in unterschiedlichen VLANs oder Subnetzen betrieben, müssen zwischengeschaltetes Routing und Firewall-Regeln den Zugriff auf `<MODEM-LAN-IP>` explizit gestatten.

2. **Hinterlegen der Zugangsdaten in der Home-Assistant-Integration:**  
   In Home Assistant wird die Verbindung über die vorhandene Integration eingerichtet:  
   - Navigieren Sie zu **Einstellungen > Geräte & Dienste**.  
   - Klicken Sie auf **Integration hinzufügen** und suchen Sie nach **ZTE H186 DSL Modem**.  
   - Hinterlegen Sie im Einrichtungsdialog die folgenden Parameter:  
     - **IP-Adresse oder Hostname** (`host`): Die feste LAN-IP des Modems (`<MODEM-LAN-IP>`).  
     - **Benutzername** (`username`): Der Benutzername der Weboberfläche (Voreinstellung: `admin`).  
     - **Passwort** (`password`): Das administrative Kennwort der Modem-Weboberfläche.  
   - *Geschützte Speicherung:* Das Passwort wird im Einrichtungsdialog ausschließlich in das dafür vorgesehene maskierte Passwortfeld eingetragen. Home Assistant speichert diese Zugangsdaten geschützt im internen Konfigurationseintrag (`ConfigEntry`). Zugangsdaten dürfen niemals in ungesicherten Skripten, Automatisierungen oder Klartextdateien hinterlegt werden.

3. **Vorgesehene Einrichtung und tatsächlich geprüfter Zustand:**  
   - *Vorgesehene Einrichtung:* Die hier beschriebene Zwei-Kabel-Topologie (roter WAN-Port für Internetdatenverkehr zum Router; gelber LAN-Port für lokale Verwaltung und Home-Assistant-Telemetrie über Switch/VLAN) stellt die herstellerkonforme und netzwerktechnisch saubere Trennung für den Bridge-Betrieb dar.  
   - *Geprüfter Zustand:* Die Software-Integration und Protokollabläufe wurden im Rahmen der Testsuite und lokaler Schnittstellentests (u. a. Token-/Challenge-Handshake, Session-Handling, Coordinator-Updates, Entity-Registry) evidenzbasiert validiert. Die tatsächliche physische Verkabelung, VLAN-Segmentierung, Switchport-Konfiguration und Firewall-Freigaben müssen in der jeweiligen Zielumgebung vor Ort anhand der individuellen Netzwerktopologie verifiziert werden.

---

## Vollständige Feldreferenz

| Schlüssel | XML-Feld | Umrechnung / Einheit | Pflicht |
|---|---|---|---|
| `downstream_sync` | `Downstream_current_rate` | /1000, Mbit/s | ja |
| `upstream_sync` | `Upstream_current_rate` | /1000, Mbit/s | ja |
| `downstream_max` | `Downstream_max_rate` | /1000, Mbit/s | ja |
| `upstream_max` | `Upstream_max_rate` | /1000, Mbit/s | ja |
| `downstream_snr` | `Downstream_noise_margin` | /10, dB | ja |
| `upstream_snr` | `Upstream_noise_margin` | /10, dB | ja |
| `downstream_attenuation` | `Downstream_attenuation` | /10, dB | ja |
| `upstream_attenuation` | `Upstream_attenuation` | /10, dB | ja |
| `profile` | `CurrentProfile` | Text | ja |
| `modulation` | `Module_type` | Text | ja |
| `dsl_status` | `Status` | Text | nein |
| `downstream_power` | `Downstream_power` | /10, dBm | nein |
| `upstream_power` | `Upstream_power` | /10, dBm | nein |
| `data_path` | `Data_path` | Text | nein |
| `downstream_interleave_depth` | `DownInterleavedepth` | Ganzzahl | nein |
| `upstream_interleave_depth` | `UpInterleaveDepth` | Ganzzahl | nein |
| `downstream_interleave_delay` | `DownInterleaveDelay` | ms | nein |
| `upstream_interleave_delay` | `UpInterleaveDelay` | ms | nein |
| `downstream_inp` | `DownstreamInp` | /10, Symbole | nein |
| `upstream_inp` | `UpstreamInp` | /10, Symbole | nein |
| `showtime` | `Showtime_start` | Ganzzahl, s | nein |
| `link_encapsulation` | `tLinkEncapsulationUsed` | Text | nein |
| `downstream_crc` | `DownCrc_errors` | Ganzzahl, Fehler | nein |
| `upstream_crc` | `UpCrc_errors` | Ganzzahl, Fehler | nein |
| `downstream_fec` | `Fec_errors` | Ganzzahl, Fehler | nein |
| `upstream_fec` | `Atuc_fec_errors` | Ganzzahl, Fehler | nein |
