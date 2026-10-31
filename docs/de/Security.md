# Sicherheit und Veröffentlichungen

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Security.md) | [Deutsch](Security.md) | [Français](../fr/Security.md) | [Español](../es/Security.md)

## Umgang mit Geheimnissen

Modemadresse und Administratorkennwort gehören in verschlüsselte Dateien unter `secrets/`, erzeugt mit `store-age-secret.sh` (oder geschützt in Home Assistant ConfigEntries). Das Repository ignoriert `.age`-Dateien sowie lokale Inhalte von `secrets/`. Keine Klartext-Konfigurationsdateien ins Git-Repository aufnehmen.

Der private Age-Schlüssel unter `~/.config/age/keys.txt` ist kein öffentlicher Schlüssel. Er muss strikt geheim bleiben und darf niemals in Repositories committed, in Issues geteilt oder an Dritte weitergegeben werden.

Vor einer Veröffentlichung prüfen, ob Secrets ignoriert werden:
```sh
git check-ignore secrets/zte-ipaddress-example.age
git check-ignore secrets/zte-admin-password-example.age
```

## Laufzeitverhalten

Der Client entschlüsselt Adresse und Passwort ausschließlich im Arbeitsspeicher. Das Passwort wird vor dem Senden mit dem Challenge-Token des Modems gehasht; Klartextpasswörter werden weder als Formularwert gesendet noch auf Datenträger geschrieben. Fehlermeldungen geben keine Passwörter oder geheimen Tokens aus.

Das Modem stellt seine Weboberfläche über unverschlüsseltes HTTP bereit. Führen Sie den Client nur in vertrauenswürdigen lokalen Netzwerken aus und exponieren Sie die Modemschnittstelle niemals in ungesicherte Netze oder ins Internet.
