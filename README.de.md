# ZTE H186 Home Assistant Integration (HACS)

<p align="center">
  <img src="images/icon.png" alt="ZTE H186 DSL Modem" width="240">
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/Ebenhoeh80/zte-h186)](https://github.com/Ebenhoeh80/zte-h186/releases)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Quality Scale: Bronze](https://img.shields.io/badge/Quality%20Scale-Bronze-brown.svg)](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
[![Languages: en, de, fr, es](https://img.shields.io/badge/Languages-en%20%7C%20de%20%7C%20fr%20%7C%20es-brightgreen.svg)](#internationalisierung-i18n)

[English](README.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md)

Eine native, asynchrone Home Assistant Custom Integration für das **ZTE H186 DSL-Modem**. Liest DSL-Leitungstelemetrie (Sync-Raten, Störabstandsmargen SNR, Leitungsdämpfung, CRC/FEC-Fehlerzähler, Übertragungsprofil und Showtime-Laufzeit) in Echtzeit direkt aus der lokalen Weboberfläche des Modems aus.

---

## 🚀 Funktionen

- **UI-Einrichtung (Config Flow)**: Schnelle Einrichtung direkt in der Home Assistant Benutzeroberfläche (*Einstellungen > Geräte & Dienste > Integration hinzufügen*). Kein YAML erforderlich.
- **Neukonfigurations-Flow**: Komfortables Ändern von Modem-IP, Hostname oder Passwort ohne Verlust von Entitäts-IDs, Dashboards oder Langzeitstatistiken.
- **Optionen-Flow**: Anpassbares Abfrageintervall von 15 bis 600 Sekunden (Standard: 60 Sekunden).
- **Session-Caching & Effizienz**: Hält die authentifizierte Sitzung aktiv und fängt Timeouts automatisch ab.
- **Volle 4-Sprachen-Unterstützung (i18n)**: Automatische Lokalisierung in Englisch, Deutsch, Französisch und Spanisch.
- **27 Sensoren**:
  - **Bandbreite & Synchronisation**: Downstream & Upstream Sync-Rate (Mbit/s), erreichbare Kapazität (Mbit/s), Leitungsauslastung (%).
  - **Signalqualität**: Downstream & Upstream Störabstandsmarge (SNR in dB), Leitungsdämpfung (dB), Sendeleistung (dBm).
  - **Framing & Latenz**: DSL-Profil (z. B. 17a, 35b), Modulationsstandard (VDSL2), Datenpfad (Fast/Interleaved), Interleave-Tiefe & Verzögerung, Impulsschutz (INP).
  - **Laufzeit & Fehler**: Showtime-Dauer, unkorrigierte CRC-Fehler, korrigierte FEC-Bitfehler.
- **Binärsensoren**:
  - `dsl_link`: Physikalischer DSL-Verbindungsstatus.
  - `line_noise_warning`: Warnanzeige bei kritischem SNR-Abfall unter 6,0 dB.
- **Aktionsbutton**:
  - `refresh_stats`: Sofortiges manuelles Abfragen der Modemwerte.
- **Diagnose-Export**: Bereinigte Diagnose-Dumps mit maskierten Passwörtern per Klick.

---

## 📦 Installation via HACS

### Methode 1: HACS Custom Repository (Empfohlen)

1. **Home Assistant** öffnen.
2. Zu **HACS** > **Integrationen** navigieren.
3. Auf das Drei-Punkte-Menü (⋮) oben rechts klicken und **Benutzerdefinierte Repositories** wählen.
4. Repository-URL eintragen:
   ```text
   https://github.com/Ebenhoeh80/zte-h186
   ```
5. Typ **Integration** wählen und auf **Hinzufügen** klicken.
6. **ZTE H186 DSL Modem** auswählen und auf **Herunterladen** klicken.
7. Home Assistant neu starten.

### Methode 2: Manuelle Installation

1. Das Release-Archiv `zte-h186-v1.0.0.zip` herunterladen.
2. Den Ordner `custom_components/zte_h186` in dein Home-Assistant-Verzeichnis kopieren:
   ```text
   /config/custom_components/zte_h186
   ```
3. Home Assistant neu starten.

---

## ⚙️ Konfiguration

1. In Home Assistant zu **Einstellungen** > **Geräte & Dienste** navigieren.
2. Unten rechts auf **Integration hinzufügen** klicken.
3. Nach **ZTE H186 DSL Modem** suchen.
4. Verbindungsdaten eingeben:
   - **IP-Adresse oder Hostname**: `<MODEM-LAN-IP>` (feste Verwaltungs-IP des Modems)
   - **Benutzername**: `admin`
   - **Passwort**: Passwort der Modem-Weboberfläche
5. Auf **Absenden** klicken.

> 💡 **Hardware-Verkabelung & Netzwerk**: Für eine umfassende Anleitung zur physischen Port-Verkabelung (Rot WAN, Gelb LAN, Grau DSL), Deaktivierung des integrierten DHCP-Servers und Zuweisung einer statischen IP siehe die [Verkabelungs- und Managementanleitung](docs/de/HomeAssistant.md#verkabelung-und-lokale-verwaltung-des-modems).

---

## 🌐 Internationalisierung (i18n)

Die Integration unterstützt nativ 4 Sprachen:
- 🇬🇧 **Englisch (`en`)** – Kanonische Quellsprache
- 🇩🇪 **Deutsch (`de`)** – Vollständige deutsche Übersetzung
- 🇫🇷 **Französisch (`fr`)** – Traduction technique complète
- 🇪🇸 **Spanisch (`es`)** – Localización técnica en español

Die Übersetzungen gelten automatisch für:
- Einrichtungs- und Neukonfigurationsdialoge
- Options-Dialoge
- Fehler- und Abbruchmeldungen
- Alle 27 Sensornamen und Beschreibungen

---

## 📄 Lizenz

Dieses Projekt ist unter der GNU General Public License v3.0 lizenziert – siehe [LICENSE](LICENSE).  
Copyright (C) 2026 Daniel Ebenhöh.
