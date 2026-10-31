# Configuration et Installation

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Setup.md) | [Deutsch](../de/Setup.md) | [Français](Setup.md) | [Español](../es/Setup.md)

Le projet ZTE H186 offre plusieurs méthodes sécurisées pour fournir les identifiants de connexion selon votre environnement d'exécution.

## Méthodes d'Identifiants

Le client prend en charge quatre méthodes par ordre de priorité :

### 1. Fichier d'identifiants JSON (Recommandé pour l'automatisation)
Fournir un fichier JSON local protégé via `--credentials` :
```sh
python3 zte_h186_stats.py --credentials /chemin/vers/credentials.json --ha-json
```
Format JSON :
```json
{
  "host": "<MODEM-LAN-IP>",
  "username": "admin",
  "password": "<MODEM-MOT-DE-PASSE>"
}
```

### 2. Paramètres de ligne de commande et variables d'environnement
Pour une utilisation interactive ou sous conteneur :
```sh
# Paramètres CLI :
python3 zte_h186_stats.py --host <MODEM-LAN-IP> --user admin --password "<MODEM-MOT-DE-PASSE>"

# Ou variables d'environnement :
export ZTE_MODEM_HOST="<MODEM-LAN-IP>"
export ZTE_MODEM_USER="admin"
export ZTE_MODEM_PASSWORD="<MODEM-MOT-DE-PASSE>"
python3 zte_h186_stats.py --ha-json
```

### 3. Secrets chiffrés avec Age (Sécurité maximale au repos)
Pour les environnements nécessitant le chiffrement des données au repos :
```sh
./store-age-secret.sh zte-ipaddress
./store-age-secret.sh zte-admin-password
```
Puis exécutez :
```sh
python3 zte_h186_stats.py --ha-json
```

### 4. Interface graphique Home Assistant (Config Flow)
Dans Home Assistant :
1. Allez dans **Paramètres > Appareils et services > Ajouter une intégration**.
2. Recherchez **ZTE H186 DSL Modem**.
3. Renseignez l'adresse IP (`<MODEM-LAN-IP>`), le nom d'utilisateur et le mot de passe.
4. L'intégration crée automatiquement les 27 capteurs et le bouton d'actualisation.

Pour le guide détaillé de câblage et d'attribution d'IP, consultez le [Guide de Câblage](HomeAssistant.md#câblage-et-gestion-locale-du-modem).
