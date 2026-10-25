# ZTE H186 Home Assistant Integration (HACS)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/Ebenhoeh80/zte-h186)](https://github.com/Ebenhoeh80/zte-h186/releases)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Quality Scale: Bronze](https://img.shields.io/badge/Quality%20Scale-Bronze-brown.svg)](https://developers.home-assistant.io/docs/core/integration-quality-scale/)

Eine native, asynchrone Home-Assistant-Integration für das **ZTE H186 DSL-Modem**. Liest alle relevanten DSL-Leitungsparameter (Sync-Raten, Störabstand/SNR, Dämpfung, CRC/FEC-Fehler, Trägerprofil, Showtime) direkt über die lokale Weboberfläche des Modems aus.

---

## 🚀 Funktionen

- **UI-Konfiguration (Config Flow)**: Einfache Einrichtung über die Home-Assistant-Benutzeroberfläche (*Einstellungen -> Geräte & Dienste -> Integration hinzufügen*).
- **Kein YAML erforderlich**: Vollständige Verwaltung über die GUI mit automatischer Geräte- und Entitätserstellung.
- **Reconfigure Flow**: IP-Adresse oder Passwort nachträglich ändern, ohne Entitäten oder Verlaufsdaten zu verlieren.
- **Options Flow**: Aktualisierungsintervall (Polling) flexibel einstellbar (15 bis 600 Sekunden, Standard: 60s).
- **26 DSL-Sensoren**:
  - **Bandbreite & Sync**: Downstream- & Upstream-Sync-Rate, maximale Leitungskapazität (Attainable Rate).
  - **Signalqualität**: Downstream- & Upstream-SNR-Marge (dB), Leitungsdämpfung (dB), Ausgangsleistung (dBm).
  - **Physikalische Parameter**: Profil (z.B. 17a, 35b Supervectoring), Modulationsstandard (VDSL2), Datenpfad (Interleaved / Fast).
  - **Laufzeit**: DSL-Showtime (Link-Uptime in Sekunden).
  - **Übertragungsqualität & Latenz**: Interleave-Tiefe, Interleave-Verzögerung (ms), Impulsstörungsschutz (INP in Symbolen).
  - **Fehlerzähler**: Downstream-/Upstream-CRC-Fehler, Downstream-/Upstream-FEC-Fehler.
- **Binärsensoren**:
  - `dsl_link`: DSL-Verbindungsstatus (Konnektivität aktiv / getrennt).
  - `line_noise_warning`: Problem-Erkennung bei kritisch niedrigem SNR (< 6 dB).
- **Aktionen & Buttons**:
  - `refresh_stats`: Sofortiges Neuladen der DSL-Werte per Knopfdruck oder Automation.
- **Vollständige Diagnostik**: Export von anonymisierten Diagnosedaten für Fehleranalysen.
- **Zweisprachig**: Vollständige deutsche und englische Übersetzungen.

---

## 📦 Installation über HACS

### Methode 1: HACS Custom Repository (Empfohlen)

1. Öffne **Home Assistant**.
2. Navigiere zu **HACS** > **Integrationen**.
3. Klicke oben rechts auf das Drei-Punkte-Menü und wähle **Benutzerdefinierte Repositories**.
4. Trage die Repository-URL ein:
   ```text
   https://github.com/Ebenhoeh80/zte-h186
   ```
5. Wähle als Typ **Integration** und klicke auf **Hinzufügen**.
6. Suche nach **ZTE H186 DSL Modem** und klicke auf **Herunterladen**.
7. Starte Home Assistant neu.

### Methode 2: Manuelle Installation

1. Lade das Repository als ZIP herunter.
2. Kopiere den Ordner `custom_components/zte_h186` in dein Home-Assistant-Verzeichnis unter `/config/custom_components/zte_h186`.
3. Starte Home Assistant neu.

---

## ⚙️ Konfiguration

1. Gehe in Home Assistant zu **Einstellungen** > **Geräte & Dienste**.
2. Klicke unten rechts auf **Integration hinzufügen**.
3. Suche nach **ZTE H186 DSL Modem**.
4. Gib folgende Daten ein:
   - **IP-Adresse oder Hostname**: z.B. `192.168.1.1` (oder die Management-IP deines Modems)
   - **Benutzername**: `admin` (Standard)
   - **Passwort**: Das Web-Passwort deines ZTE H186 Modems
5. Klicke auf **Absenden**. Die Integration prüft die Verbindung und richtet das Gerät mit allen Sensoren ein.

---

## 📊 Entitätsübersicht

| Entität | Typ | Einheit | Beschreibung |
|---|---|---|---|
| `sensor.zte_h186_<ip>_downstream_sync` | Sensor | Mbit/s | Aktuelle Downstream-Synchronisationsrate |
| `sensor.zte_h186_<ip>_upstream_sync` | Sensor | Mbit/s | Aktuelle Upstream-Synchronisationsrate |
| `sensor.zte_h186_<ip>_downstream_max` | Sensor | Mbit/s | Maximal erreichbare Downstream-Leitungskapazität |
| `sensor.zte_h186_<ip>_upstream_max` | Sensor | Mbit/s | Maximal erreichbare Upstream-Leitungskapazität |
| `sensor.zte_h186_<ip>_downstream_snr` | Sensor | dB | Signal-Rausch-Verhältnis (Störabstand) im Downstream |
| `sensor.zte_h186_<ip>_upstream_snr` | Sensor | dB | Signal-Rausch-Verhältnis (Störabstand) im Upstream |
| `sensor.zte_h186_<ip>_downstream_attenuation`| Sensor | dB | Leitungsdämpfung im Downstream |
| `sensor.zte_h186_<ip>_upstream_attenuation`  | Sensor | dB | Leitungsdämpfung im Upstream |
| `sensor.zte_h186_<ip>_downstream_power`      | Sensor (Diagnostik) | dBm | Sendeleistung im Downstream |
| `sensor.zte_h186_<ip>_upstream_power`        | Sensor (Diagnostik) | dBm | Sendeleistung im Upstream |
| `sensor.zte_h186_<ip>_profile`               | Sensor | - | DSL-Trägerprofil (z.B. 17a, 35b) |
| `sensor.zte_h186_<ip>_modulation`            | Sensor | - | Modulation (z.B. VDSL2) |
| `sensor.zte_h186_<ip>_dsl_status`            | Sensor | - | DSL-Link-Status (z.B. Up) |
| `sensor.zte_h186_<ip>_showtime`              | Sensor (Diagnostik) | s | Unterbrechungsfreie Verbindungsdauer |
| `sensor.zte_h186_<ip>_downstream_crc`        | Sensor (Diagnostik) | Fehler | Unkorrigierbare CRC-Fehler Downstream |
| `sensor.zte_h186_<ip>_upstream_crc`          | Sensor (Diagnostik) | Fehler | Unkorrigierbare CRC-Fehler Upstream |
| `sensor.zte_h186_<ip>_downstream_fec`        | Sensor (Diagnostik) | Fehler | Korrigierte FEC-Bitfehler Downstream |
| `sensor.zte_h186_<ip>_upstream_fec`          | Sensor (Diagnostik) | Fehler | Korrigierte FEC-Bitfehler Upstream |
| `binary_sensor.zte_h186_<ip>_dsl_link`       | Binärsensor | - | Zeigt an, ob die DSL-Verbindung steht |
| `binary_sensor.zte_h186_<ip>_line_noise_warning` | Binärsensor | - | Warnt bei SNR < 6 dB |
| `button.zte_h186_<ip>_refresh_stats`         | Button | - | Löst sofortigen Messdatenabruf aus |

---

## 🔒 Sicherheit & Technische Details

- **Sitzungserhaltung & Effizienz**: Das Modem verwendet eine mehrstufige Challenge-Response-Authentifizierung (Session-Token, Login-Token, SHA-256-Passworthash und SID-Cookie). Der asynchrone Client (`aiohttp`) hält die Sitzung aufrecht und loggt sich nur bei Session-Timeout neu ein, um das Modem zu schonen.
- **Passwortschutz**: Passwörter werden niemals im Klartext in Logs ausgegeben. In Diagnosedaten wird das Passwort automatisch unkenntlich gemacht (`REDACTED`).
- **Laufzeit-Architektur**: Verwendet `DataUpdateCoordinator` und Home Assistant `ConfigEntry` Runtime Data.

---

## 📄 Lizenz

Dieses Projekt ist unter der GNU General Public License v3.0 lizenziert – siehe [LICENSE](LICENSE).
Copyright (C) 2026 Daniel Ebenhöh.