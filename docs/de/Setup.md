# Einrichtung und Konfiguration

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Setup.md) | [Deutsch](Setup.md) | [Français](../fr/Setup.md) | [Español](../es/Setup.md)

Das ZTE-H186-Projekt bietet verschiedene flexible und sichere Wege zur Bereitstellung der Zugangsdaten – passend zur jeweiligen Betriebsumgebung (CLI-Skript, Home Assistant Custom Component oder Docker/Daemon).

## Konfigurationsmethoden

Der Client unterstützt vier Methoden in absteigender Priorität:

### 1. Geschützte JSON-Datei (Empfohlen für Automatisierungen)
Übergabe einer geschützten lokalen JSON-Datei via `--credentials`:
```sh
python3 zte_h186_stats.py --credentials /pfad/zu/credentials.json --ha-json
```
JSON-Format:
```json
{
  "host": "<MODEM-LAN-IP>",
  "username": "admin",
  "password": "<MODEM-PASSWORT>"
}
```

### 2. Befehlszeilenparameter & Umgebungsvariablen
Für interaktive Nutzung oder Container-Umgebungen:
```sh
# Direkte Übergabe per CLI-Parameter:
python3 zte_h186_stats.py --host <MODEM-LAN-IP> --user admin --password "<MODEM-PASSWORT>"

# Oder über Umgebungsvariablen:
export ZTE_MODEM_HOST="<MODEM-LAN-IP>"
export ZTE_MODEM_USER="admin"
export ZTE_MODEM_PASSWORD="<MODEM-PASSWORT>"
python3 zte_h186_stats.py --ha-json
```

### 3. Verschlüsselte Age-Secrets (Höchste Sicherheit auf Datenträgern)
Für Umgebungen, die verschlüsselte Secrets im Ruhezustand (Encryption at Rest) ohne Klartextdateien erfordern:

Ausführen der Hilfsskripte zum direkten Verschlüsseln in `secrets/`:
```sh
./store-age-secret.sh zte-ipaddress
./store-age-secret.sh zte-admin-password
```
Das Skript erstellt `~/.config/age/keys.txt` (oder beachtet `AGE_IDENTITY`) und speichert verschlüsselte `.age`-Dateien.

```sh
python3 zte_h186_stats.py --ha-json
```

### 4. Home Assistant UI Config Flow
Bei Installation als Home Assistant Integration (via HACS oder `custom_components/zte_h186`):
1. In Home Assistant zu **Einstellungen > Geräte & Dienste > Integration hinzufügen** navigieren.
2. Nach **ZTE H186 DSL Modem** suchen.
3. Die IP-Adresse (`<MODEM-LAN-IP>`), den Benutzernamen (`admin`) und das Passwort eingeben.
4. Die Integration stellt die Verbindung her, validiert die Erreichbarkeit und erstellt automatisch 27 Sensoren sowie einen Diagnose-Button.

Für detaillierte Informationen zur physischen Portverkabelung (Rot WAN, Gelb LAN, Grau DSL) und zur Vergabe einer statischen Management-IP siehe die [Verkabelungs- und Managementanleitung](HomeAssistant.md#verkabelung-und-lokale-verwaltung-des-modems).

## Voraussetzungen

- Python 3.10 oder neuer
- Netzwerkzugriff auf die ZTE H186 Weboberfläche (Standardport 80)
- ZTE H186 Modem mit aktivierter DSL-Statusseite

## Client ausführen

```sh
# Formatierte Texttabelle:
python3 zte_h186_stats.py

# Rohe XML-Werte als JSON:
python3 zte_h186_stats.py --json

# Normalisiertes Home Assistant JSON:
python3 zte_h186_stats.py --ha-json
```

## Fehlerbehebung

- `Erforderliches Secret fehlt`: Erstellen Sie das fehlende Secret mit dem passenden Zweck in `store-age-secret.sh`.
- `age konnte ein Secret nicht entschlüsseln`: Verwenden Sie dieselbe private Identität, die bei der Verschlüsselung genutzt wurde.
- `Das IP-Secret enthält keine gültige IP-Adresse`: Erstellen Sie eine neue Datei mit einer gültigen IPv4-Adresse.
- `Router nicht erreichbar`: Lokale Netzwerkverbindung und IP-Adresse prüfen.
- Login- oder Session-Fehler: Passwort überprüfen und Ablauf im [Protokoll](Protocol.md) nachvollziehen.
